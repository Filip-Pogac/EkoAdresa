"""Air quality for an address (decision 2026-11-05, option a: same basis as the heatmap).

- Score: mean PM10 of the nearest City of Zagreb monitoring station, Jan-Aug 2023
  (zg-zrak-mjerenja, the latest published data), via ekoskor.air_score.
- Shown with it: the station (zg-zrak-postaje), latest daily values with their date, and
  the last 30 days of data for the chart.
- Extra information: the national air quality index at the nearest national station
  (rh-zrak-indeks, INSPIRE WFS, same-day values). Its scale is not verified yet, so it is
  flagged `scale_verified=False` and never used for the score. If the WFS does not answer
  within LIVE_TIMEOUT_S the layer is returned without it.

Distances: straight line in EPSG:3765 (HTRS96/TM, metres), as in scripts/build_heatmap.py,
so the nearest station is the same as in the heatmap.
"""

import asyncio
import json
import logging
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import cache

import httpx2 as httpx
import pandas as pd

from app.cache import Cache, cached_fetch
from app.models import AirLayer, AirStation, AirValue, LiveAirIndex
from app.paths import DATA_DIR
from app.services.ekoskor import air_score, status
from app.services.geo import from_htrs, to_htrs

SOURCE_ID = "zg-zrak-mjerenja"
STATIONS_SOURCE_ID = "zg-zrak-postaje"
STATIONS_FILE = "air_stations.geojson"
HISTORY_FILE = "air_history.parquet"
HISTORY_DAYS = 30

LIVE_SOURCE_ID = "rh-zrak-indeks"
LIVE_URL = "https://servisi.azo.hr/inspire/geos1/hh/wfs"
LIVE_PARAMS = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "hh1:EnvHealthDeterminantMeasure",
}
LIVE_CACHE_NAMESPACE = f"{LIVE_SOURCE_ID}:all-stations"  # one answer for all addresses
LIVE_TTL_S = 3600  # values change hourly at most
LIVE_TIMEOUT_S = 2.5
GML_NS = {
    "hh1": "http://inspire.ec.europa.eu/schemas/hh/4.0",
    "gml": "http://www.opengis.net/gml/3.2",
}

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Station:
    id: str
    name: str
    station_type: str | None
    lat: float
    lon: float
    x: float
    y: float


@dataclass(frozen=True)
class _Data:
    stations: list[_Station]
    history: pd.DataFrame
    pm10_mean: dict[str, float]


@cache
def _data() -> _Data:
    features = json.loads((DATA_DIR / STATIONS_FILE).read_text(encoding="utf-8"))["features"]
    stations = []
    for f in features:
        lon, lat = f["geometry"]["coordinates"]
        x, y = to_htrs.transform(lon, lat)
        p = f["properties"]
        stations.append(_Station(p["id"], p["name"], p.get("station_type"), lat, lon, x, y))
    history = pd.read_parquet(DATA_DIR / HISTORY_FILE)
    pm10 = history[history["pollutant"] == "pm10"].groupby("station_id")["value_ug_m3"].mean()
    return _Data(stations, history, {k: float(v) for k, v in pm10.items()})


def _distance_m(x: float, y: float, lat: float, lon: float) -> float:
    px, py = to_htrs.transform(lon, lat)
    return math.hypot(px - x, py - y)


def _values(rows: pd.DataFrame) -> list[AirValue]:
    return [
        AirValue(pollutant=p, value_ug_m3=round(float(v), 1), date=d)
        for p, v, d in zip(rows["pollutant"], rows["value_ug_m3"], rows["date"], strict=True)
    ]


async def _fetch_live(client: httpx.AsyncClient) -> list[dict]:
    """All national stations: [{lat, lon, value, measured_at}], reprojected from EPSG:3765."""
    resp = await client.get(LIVE_URL, params=LIVE_PARAMS)
    resp.raise_for_status()
    out = []
    for m in ET.fromstring(resp.content).iterfind(".//hh1:EnvHealthDeterminantMeasure", GML_NS):
        pos, measure = m.find(".//gml:pos", GML_NS), m.find("hh1:measure", GML_NS)
        end = m.find(".//gml:endPosition", GML_NS)
        if pos is None or measure is None or end is None or not measure.text:
            continue
        x, y = map(float, (pos.text or "").split())
        lon, lat = from_htrs.transform(x, y)
        out.append({"lat": lat, "lon": lon, "value": float(measure.text), "measured_at": end.text})
    if not out:
        raise ValueError("no air index features in the WFS answer")
    return out


async def _live_index(
    client: httpx.AsyncClient, cache_: Cache, lat: float, lon: float
) -> LiveAirIndex | None:
    try:
        answer = await asyncio.wait_for(
            cached_fetch(
                cache_, LIVE_CACHE_NAMESPACE, 0.0, 0.0, lambda: _fetch_live(client), LIVE_TTL_S
            ),
            LIVE_TIMEOUT_S,
        )
    except Exception as exc:  # extra information only: never fail the air layer for it
        log.warning("national air index unavailable: %s", exc)
        return None

    def distance_to(s: dict) -> float:
        return _distance_m(*to_htrs.transform(s["lon"], s["lat"]), lat, lon)

    nearest = min(answer.value, key=distance_to)
    return LiveAirIndex(
        value=nearest["value"],
        measured_at=datetime.fromisoformat(nearest["measured_at"].replace("Z", "+00:00")),
        distance_m=round(distance_to(nearest)),
        scale_verified=False,
        source_id=LIVE_SOURCE_ID,
    )


async def air_at(client: httpx.AsyncClient, cache_: Cache, lat: float, lon: float) -> AirLayer:
    data = _data()
    station = min(data.stations, key=lambda s: _distance_m(s.x, s.y, lat, lon))
    rows = data.history[data.history["station_id"] == station.id].sort_values(["date", "pollutant"])
    period_from: date = rows["date"].min()
    period_to: date = rows["date"].max()
    latest = rows.groupby("pollutant").tail(1).sort_values("pollutant")
    recent = rows[rows["date"] > period_to - timedelta(days=HISTORY_DAYS)]

    pm10_mean = data.pm10_mean[station.id]
    score = air_score(pm10_mean)
    return AirLayer(
        status=status(score),
        score=round(score),
        source_id=SOURCE_ID,
        station=AirStation(
            id=station.id,
            name=station.name,
            station_type=station.station_type,
            lat=station.lat,
            lon=station.lon,
            distance_m=round(_distance_m(station.x, station.y, lat, lon)),
            source_id=STATIONS_SOURCE_ID,
        ),
        pm10_mean_ug_m3=round(pm10_mean, 1),
        period_from=period_from,
        period_to=period_to,
        latest=_values(latest),
        history=_values(recent),
        live_index=await _live_index(client, cache_, lat, lon),
    )
