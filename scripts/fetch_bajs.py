"""Fetch Bajs public bike stations (OpenStreetMap) into data/bike_stations.geojson.

Source osm-bajs (see docs/data-sources.md): OSM amenity=bicycle_rental with
network="Bajs Zagreb" inside Grad Zagreb (ISO 3166-2 HR-21), via Overpass. The City's own
dataset (Geoportal "Sustav javnih bicikala", 32 stations, 2022) is outdated: 13 of its 32
stations have no Bajs station within 100 m (checked 2026-11-08), so OSM is used instead.
About half of the OSM stations carry fixme="Popravi poziciju stanice" (position to be
checked); they are kept and the flag is stored as `position_unchecked`.

Output: GeoJSON FeatureCollection, EPSG:4326, one point per station with `name`, `ref`
(station number), `position_unchecked` and `source_id`. Raw download goes to data/raw/.

Run from the repo root:  uv run --project backend python scripts/fetch_bajs.py
"""

import json
import logging
import time
from pathlib import Path

import httpx2 as httpx

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "bike_stations.geojson"

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
OVERPASS_QUERY = (
    "[out:json][timeout:90];"
    'area["ISO3166-2"="HR-21"]["admin_level"]->.zg;'
    'nwr["amenity"="bicycle_rental"]["network"="Bajs Zagreb"](area.zg);'
    "out center tags;"
)

log = logging.getLogger("fetch_bajs")


def post_with_retry(client: httpx.Client, url: str) -> httpx.Response:
    """POST the Overpass query with exponential backoff; Overpass sometimes returns 5xx."""
    delay_s = 5.0
    for attempt in range(1, 5):
        try:
            resp = client.post(url, data={"data": OVERPASS_QUERY})
            if resp.status_code == 200:
                return resp
            log.warning("%s -> HTTP %s (attempt %d)", url, resp.status_code, attempt)
        except httpx.HTTPError as exc:
            log.warning("%s -> %s (attempt %d)", url, exc, attempt)
        time.sleep(delay_s)
        delay_s *= 2
    raise RuntimeError(f"giving up on {url}")


def fetch(client: httpx.Client) -> tuple[list[dict], str]:
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            resp = post_with_retry(client, url)
            break
        except RuntimeError as exc:
            last_error = exc
    else:
        raise RuntimeError("all Overpass endpoints failed") from last_error
    (RAW_DIR / "osm_bajs.json").write_bytes(resp.content)
    payload = resp.json()
    osm_timestamp = payload["osm3s"]["timestamp_osm_base"]
    elements = payload["elements"]
    log.info("osm-bajs: %d stations (OSM data as of %s)", len(elements), osm_timestamp)
    out = []
    for el in elements:
        tags = el.get("tags", {})
        lat = el.get("lat", el.get("center", {}).get("lat"))
        lon = el.get("lon", el.get("center", {}).get("lon"))
        out.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "id": f"osm/{el['type']}/{el['id']}",
                    "name": tags.get("name"),
                    "ref": tags.get("ref"),
                    "position_unchecked": "fixme" in tags,
                    "source_id": "osm-bajs",
                },
            }
        )
    return out, osm_timestamp


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120) as client:
        stations, osm_timestamp = fetch(client)
    collection = {
        "type": "FeatureCollection",
        "metadata": {"crs": "EPSG:4326", "source_id": "osm-bajs", "osm_timestamp": osm_timestamp},
        "features": stations,
    }
    text = json.dumps(collection, ensure_ascii=False, separators=(",", ":"))
    OUT_PATH.write_text(text, encoding="utf-8", newline="\n")
    unchecked = sum(f["properties"]["position_unchecked"] for f in stations)
    log.info(
        "wrote %s: %d stations, %d with position to be checked",
        OUT_PATH.relative_to(ROOT),
        len(stations),
        unchecked,
    )


if __name__ == "__main__":
    main()
