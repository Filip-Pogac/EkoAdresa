"""Current air measurements at the nearest DHMZ state station (source dhmz-kvaliteta-zraka).

DHMZ (Državni hidrometeorološki zavod) runs the state air quality stations Zagreb 1-4.
It publishes the last 24 hours of hourly, raw and unvalidated values ("izvorni
nekontrolirani podaci") per station and pollutant only as web pages
(meteo.hr/kvaliteta_zraka.php); it has no API or XML for air quality (checked 2026-11-06,
docs/data-sources.md). The values are in each page's chart data as
`[new Date(Y, M-1, D, H), value]`, hours in local time. Terms of use: free reuse, credit
"(Izvor: DHMZ)".

Extra information only: 24 hours of raw data cannot replace the annual PM10 mean behind
the score (docs/ekoskor.md). The reading gets its own status against the WHO 2021 24-hour
values (DAY_LIMITS), never mixed into the air layer's status or EkoSkor.

Requests name the station, never the user's coordinates; one cached answer per station and
pollutant serves every address for an hour.
"""

import asyncio
import functools
import logging
import re

import httpx2 as httpx
import numpy as np

from app.cache import Cache, cached_fetch
from app.models import DhmzReading, DhmzStation, DhmzValue, Pollutant, Status
from app.services.geo import distances_m, project

SOURCE_ID = "dhmz-kvaliteta-zraka"
URL = "https://meteo.hr/kvaliteta_zraka.php"
TTL_S = 3600  # hourly values
TIMEOUT_S = 2.5

# Station coordinates from the DHMZ station map (meteo.hr/index_kz.php?tab=kz), 2026-11-06
STATIONS = {
    "Zagreb 1": (45.800496, 15.97422),
    "Zagreb 2": (45.823717, 16.035825),
    "Zagreb 3": (45.764947, 16.006469),
    "Zagreb 4": (45.774676, 15.931163),
}
# pollutant -> (id_komp, komp) as in the DHMZ page links. Zagreb 1 has no NO2 (empty page).
COMPONENTS: dict[Pollutant, tuple[int, str]] = {
    "pm10": (258, "lebdece cestice (<10um)"),
    "pm2_5": (259, "lebdece cestice (<2.5um)"),
    "no2": (257, "dusikov dioksid"),
}
# 24-hour means, µg/m³ (WHO global air quality guidelines 2021): pollutant -> (guideline,
# interim target). Green up to the guideline, yellow up to the interim target (PM10 IT-4,
# PM2.5 IT-4, NO2 IT-2), red above. The worst pollutant sets the status.
DAY_LIMITS: dict[Pollutant, tuple[float, float]] = {
    "pm10": (45, 50),
    "pm2_5": (15, 25),
    "no2": (25, 50),
}
MIN_HOURS = 18  # a 24-hour mean needs 75 % of hourly values (Directive 2008/50/EC, Annex VII)
CHART_ROW = re.compile(r"\[new Date\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)\s*,\s*(-?\d+(?:\.\d+)?)\]")

log = logging.getLogger(__name__)


NAMES = list(STATIONS)


@functools.cache
def _stations_xy() -> np.ndarray:
    """Station coordinates in EPSG:3765 (metres), in NAMES order."""
    lats, lons = np.array([STATIONS[n] for n in NAMES]).T
    return project(lons, lats)


def parse_hourly(page: str) -> list[tuple[str, float]]:
    """[(local hour 'YYYY-MM-DDTHH:00', µg/m³)] from a DHMZ chart page; [] if none."""
    rows = []
    for y, m, d, h, v in CHART_ROW.findall(page):
        rows.append((f"{int(y):04d}-{int(m) + 1:02d}-{int(d):02d}T{int(h):02d}:00", float(v)))
    return rows


def day_status(values: list[DhmzValue]) -> Status:
    """Status of the last 24 h: worst pollutant against DAY_LIMITS; unavailable if no
    pollutant has enough hours for a 24-hour mean."""
    rank = {"green": 0, "yellow": 1, "red": 2}
    found: list[Status] = []
    for v in values:
        if v.hours < MIN_HOURS or v.pollutant not in DAY_LIMITS:
            continue
        guideline, interim = DAY_LIMITS[v.pollutant]
        m = v.mean_24h_ug_m3
        found.append("green" if m <= guideline else "yellow" if m <= interim else "red")
    return max(found, key=rank.__getitem__) if found else "unavailable"


async def _fetch(client: httpx.AsyncClient, station: str, pollutant: Pollutant) -> list:
    id_komp, komp = COMPONENTS[pollutant]
    params = {"section": "podaci_kz", "post": station, "id_komp": id_komp, "komp": komp}
    resp = await client.get(URL, params=params)
    resp.raise_for_status()
    return [list(r) for r in parse_hourly(resp.text)]  # JSON-serialisable for the cache


async def _component(
    client: httpx.AsyncClient, cache: Cache, station: str, pollutant: Pollutant
) -> DhmzValue | None:
    lat, lon = STATIONS[station]
    answer = await cached_fetch(
        cache,
        f"{SOURCE_ID}:{pollutant}",
        lat,
        lon,
        lambda: _fetch(client, station, pollutant),
        TTL_S,
    )
    if answer.stale:
        return None  # an old "last 24 h" would look current: show nothing instead
    rows = answer.value
    if not rows:
        return None  # pollutant not measured at this station
    values = [v for _, v in rows]
    return DhmzValue(
        pollutant=pollutant,
        mean_24h_ug_m3=round(sum(values) / len(values), 1),
        latest_ug_m3=round(values[-1], 1),
        latest_at_local=rows[-1][0],
        hours=len(values),
    )


async def _reading(
    client: httpx.AsyncClient, cache: Cache, lat: float, lon: float
) -> DhmzReading | None:
    d = distances_m(_stations_xy(), lat, lon)
    i = int(d.argmin())
    name = NAMES[i]
    found = await asyncio.gather(*(_component(client, cache, name, p) for p in COMPONENTS))
    values = [v for v in found if v is not None]
    if not values:
        return None
    st_lat, st_lon = STATIONS[name]
    return DhmzReading(
        station=DhmzStation(name=name, lat=st_lat, lon=st_lon, distance_m=round(float(d[i]))),
        values=values,
        status=day_status(values),
        validated=False,
        source_id=SOURCE_ID,
    )


async def dhmz_at(
    client: httpx.AsyncClient, cache: Cache, lat: float, lon: float
) -> DhmzReading | None:
    """Last 24 h at the nearest DHMZ Zagreb station, or None (never fails the air layer)."""
    try:
        return await asyncio.wait_for(_reading(client, cache, lat, lon), TIMEOUT_S)
    except Exception as exc:  # extra information only
        log.warning("DHMZ air data unavailable: %s", type(exc).__name__)
        return None
