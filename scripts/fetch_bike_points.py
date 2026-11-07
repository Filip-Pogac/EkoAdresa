"""Fetch public bike stations and public bike parking (Grad Zagreb) into data/.

Sources (see docs/data-sources.md):
- zg-javni-bicikli: Geoportal "Geolokacije sustava javnih bicikala", data.zagreb.hr, ArcGIS
  Hub GeoJSON export, EPSG:4326 -> data/bike_stations.geojson (32 stations)
- zg-parkiralista-bicikli: Geoportal "Geolokacije javnih parkirališta za bicikle", same
  export style -> data/bike_parking.geojson (318 places)

Output: one GeoJSON FeatureCollection each, EPSG:4326, trimmed to the properties the app
uses; every feature has `source_id`. Raw downloads go to data/raw/.

Run from the repo root:  uv run --project backend python scripts/fetch_bike_points.py
"""

import json
import logging
import time
from pathlib import Path

import httpx2 as httpx

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
STATIONS_PATH = ROOT / "data" / "bike_stations.geojson"
PARKING_PATH = ROOT / "data" / "bike_parking.geojson"

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"
STATIONS_URL = (
    "https://opendata.arcgis.com/api/v3/datasets/95f8892f77eb45968b65469b9063f8b9_3"
    "/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1"
)
PARKING_URL = (
    "https://opendata.arcgis.com/api/v3/datasets/04012b0e4968447c978a6ee494d76495_2"
    "/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1"
)

log = logging.getLogger("fetch_bike_points")


def get_with_retry(client: httpx.Client, url: str) -> bytes:
    """GET with exponential backoff; the open-data portal sometimes returns 5xx."""
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
    """Collapse embedded newlines and repeated spaces; empty -> None."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def fetch_stations(client: httpx.Client) -> list[dict]:
    raw = get_with_retry(client, STATIONS_URL)
    (RAW_DIR / "zg_sustav_javnih_bicikala.geojson").write_bytes(raw)
    features = json.loads(raw)["features"]
    log.info("zg-javni-bicikli: %d raw features", len(features))
    out = []
    for f in features:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        out.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "id": f"zg-javni-bicikli/{p['OBJECTID']}",
                    "name": clean(p["naziv"]),
                    "location": clean(p["lokacija"]),
                    "racks": p["broj_stalaka"],
                    "source_id": "zg-javni-bicikli",
                },
            }
        )
    return out


def fetch_parking(client: httpx.Client) -> list[dict]:
    raw = get_with_retry(client, PARKING_URL)
    (RAW_DIR / "zg_javna_parkiralista_bicikli.geojson").write_bytes(raw)
    features = json.loads(raw)["features"]
    log.info("zg-parkiralista-bicikli: %d raw features", len(features))
    out = []
    for f in features:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        out.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "id": f"zg-parkiralista-bicikli/{p['OBJECTID']}",
                    "name": clean(p["naziv"]),
                    "location": clean(p["lokacija"]),
                    "kind": clean(p["vrsta"]),  # 'stalci' = racks; others as published
                    "racks": p["broj_stalaka"],
                    "source_id": "zg-parkiralista-bicikli",
                },
            }
        )
    return out


def write(path: Path, features: list[dict], source_id: str) -> None:
    collection = {
        "type": "FeatureCollection",
        "metadata": {"crs": "EPSG:4326", "source_id": source_id},
        "features": features,
    }
    text = json.dumps(collection, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8", newline="\n")
    log.info("wrote %s: %d features", path.relative_to(ROOT), len(features))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120) as client:
        stations = fetch_stations(client)
        parking = fetch_parking(client)
    write(STATIONS_PATH, stations, "zg-javni-bicikli")
    write(PARKING_PATH, parking, "zg-parkiralista-bicikli")


if __name__ == "__main__":
    main()
