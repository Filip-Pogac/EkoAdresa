"""Fetch City of Zagreb air quality stations and 2023 daily measurements.

Sources (see docs/data-sources.md):
- zg-zrak-postaje:  Geoportal Kvaliteta zraka, ArcGIS Hub GeoJSON export, EPSG:4326 (6 stations)
- zg-zrak-mjerenja: "Podaci o kvaliteti zraka u Gradu Zagrebu - MP <station> 2023",
                    data.zagreb.hr, one XLSX per month (Jan-Aug 2023), one row per day

The files already hold one value per day, so no averaging is done here.

Outputs:
- data/air_stations.geojson  station points + which pollutants / dates the history covers
- data/air_history.parquet   long format: station_id, date, pollutant, value_ug_m3, source_id

Run from the repo root:  uv run --project backend python scripts/fetch_air.py
"""

import io
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import httpx2 as httpx
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "air"
STATIONS_OUT = ROOT / "data" / "air_stations.geojson"
HISTORY_OUT = ROOT / "data" / "air_history.parquet"

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"

STATIONS_URL = (
    "https://opendata.arcgis.com/api/v3/datasets/ed9898e63ec94770a8fb37713c36f8ca_0"
    "/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1"
)
CKAN_PACKAGE_SHOW = "https://data.zagreb.hr/api/3/action/package_show?id={}"

# station_id -> (`naziv` in zg-zrak-postaje, data.zagreb.hr package for 2023 measurements)
STATIONS = {
    "djordjiceva": ("Đorđićeva ulica", "podaci-o-kvaliteti-zraka-u-gradu-zagrebu-dordiceva-2023"),
    "ksaverska": ("Ksaverska cesta", "podaci-o-kvaliteti-zraka-u-gradu-zagrebu-ksaver-2023"),
    "pescenica": ("Peščenica", "podaci-o-kvaliteti-zraka-u-gradu-zagrebu-pescenica-2023"),
    "prilaz-baruna-filipovica": (
        "Prilaz baruna Filipovića",
        "podaci-o-kvaliteti-zraka-u-gradu-zagrebu-prilaz-baruna-filipovica-2023",
    ),
    "siget": ("Siget", "podaci-o-kvaliteti-zraka-u-gradu-zagrebu-siget-2023"),
    "susedgrad": ("Susedgrad", "podaci-o-kvaliteti-zraka-u-gradu-zagrebu-susedgrad-2023"),
}

SHEET = "Numeričke vrijednosti"
# Header text before " [unit]" (whitespace collapsed) -> pollutant code. All four are in µg/m3.
POLLUTANTS = {"NO2": "no2", "Ozon": "o3", "PM10": "pm10", "PM2,5": "pm2_5"}

log = logging.getLogger("fetch_air")


def get_with_retry(client: httpx.Client, url: str) -> bytes:
    """data.zagreb.hr returns occasional 502s (2 of 48 files in Phase 2 testing)."""
    delay_s = 5.0
    for attempt in range(1, 5):
        try:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.content
            log.warning("%s -> HTTP %s (attempt %d)", url, resp.status_code, attempt)
        except httpx.HTTPError as exc:
            log.warning("%s -> %s (attempt %d)", url, exc, attempt)
        time.sleep(delay_s)
        delay_s *= 2
    raise RuntimeError(f"giving up on {url}")


def clean(value: object) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def parse_month(content: bytes, station_id: str, file_name: str) -> list[dict]:
    """One XLSX -> rows of (station_id, date, pollutant, value). Trailer rows are skipped."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    rows = list(wb[SHEET].iter_rows(values_only=True))
    columns: dict[int, str] = {}
    for idx, header in enumerate(rows[0]):
        if header is None:
            continue
        name, _, unit = " ".join(str(header).split()).partition(" [")
        if name in POLLUTANTS:
            if not unit.endswith("g/m3]") or unit.startswith(("ng", "mg")):
                raise ValueError(f"{file_name}: unexpected unit for {name}: [{unit}")
            columns[idx] = POLLUTANTS[name]
    if not columns:
        raise ValueError(f"{file_name}: no known pollutant columns in {rows[0]}")

    out = []
    for row in rows[1:]:
        day = row[0]
        if not isinstance(day, datetime):
            continue  # blank or trailer row (monthly count of PM10 exceedances)
        for idx, pollutant in columns.items():
            value = row[idx]
            if value is None:
                continue
            out.append(
                {
                    "station_id": station_id,
                    "date": day.date(),
                    "pollutant": pollutant,
                    "value_ug_m3": float(value),
                    "source_id": "zg-zrak-mjerenja",
                }
            )
    return out


def fetch_history(client: httpx.Client) -> pd.DataFrame:
    rows: list[dict] = []
    for station_id, (_, package) in STATIONS.items():
        meta = json.loads(get_with_retry(client, CKAN_PACKAGE_SHOW.format(package)))
        urls = sorted(r["url"] for r in meta["result"]["resources"] if r["url"].endswith(".xlsx"))
        station_rows: list[dict] = []
        for url in urls:
            file_name = url.rsplit("/", 1)[-1]
            raw_path = RAW_DIR / file_name
            content = raw_path.read_bytes() if raw_path.exists() else b""
            if not content.startswith(b"PK"):  # missing or a saved error page
                content = get_with_retry(client, url)
                raw_path.write_bytes(content)
            station_rows += parse_month(content, station_id, file_name)
        log.info("%s: %d files, %d values", station_id, len(urls), len(station_rows))
        rows += station_rows

    df = pd.DataFrame(rows).sort_values(["station_id", "pollutant", "date"], ignore_index=True)
    dupes = df.duplicated(["station_id", "pollutant", "date"]).sum()
    if dupes:
        raise ValueError(f"{dupes} duplicate (station, pollutant, date) rows")
    return df


def fetch_stations(client: httpx.Client, history: pd.DataFrame) -> list[dict]:
    raw = get_with_retry(client, STATIONS_URL)
    (RAW_DIR / "zg_kvaliteta_zraka_postaje.geojson").write_bytes(raw)
    by_name = {f["properties"]["naziv"]: f for f in json.loads(raw)["features"]}

    out = []
    for station_id, (name, _) in STATIONS.items():
        f = by_name[name]  # KeyError = the City renamed a station; fix STATIONS
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        h = history[history["station_id"] == station_id]
        out.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "id": station_id,
                    "name": name,
                    "station_type": clean(p["tip_postaje"]),
                    "location": clean(p["opis_lokac"]),
                    "measured_substances": clean(p["mjerne_tvari"]),
                    "operator": clean(p["odgovorna_inst"]),
                    "info_url": clean(p["izvor"]),
                    "history_pollutants": sorted(h["pollutant"].unique().tolist()),
                    "history_from": h["date"].min().isoformat(),
                    "history_to": h["date"].max().isoformat(),
                    "source_id": "zg-zrak-postaje",
                    "history_source_id": "zg-zrak-mjerenja",
                },
            }
        )
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120, follow_redirects=True) as c:
        history = fetch_history(c)
        stations = fetch_stations(c, history)

    history.to_parquet(HISTORY_OUT, index=False)
    log.info(
        "wrote %s: %d rows, %s to %s",
        HISTORY_OUT.relative_to(ROOT),
        len(history),
        history["date"].min(),
        history["date"].max(),
    )
    collection = {
        "type": "FeatureCollection",
        "metadata": {
            "crs": "EPSG:4326",
            "sources": {
                "zg-zrak-postaje": {"url": STATIONS_URL},
                "zg-zrak-mjerenja": {"packages": [pkg for _, pkg in STATIONS.values()]},
            },
        },
        "features": stations,
    }
    text = json.dumps(collection, ensure_ascii=False, indent=1)
    STATIONS_OUT.write_text(text, encoding="utf-8", newline="\n")
    log.info("wrote %s: %d stations", STATIONS_OUT.relative_to(ROOT), len(stations))


if __name__ == "__main__":
    main()
