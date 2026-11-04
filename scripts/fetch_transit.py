"""Fetch ZET bus and tram stops (Grad Zagreb) into data/transit.geojson.

Source zg-zet (see docs/data-sources.md):
- bus:  data.zagreb.hr "Geoportal Autobusna stajališta ZET", GeoJSON, WGS84 lon/lat
- tram: data.zagreb.hr "Geoportal Tramvajska stajališta ZET", ArcGIS Hub GeoJSON export, EPSG:4326

One feature per platform/direction, as published. Grouping platforms into named stops is
decided in Phase 3 (services/mobility.py), so nothing is merged or dropped here.

Run from the repo root:  uv run --project backend python scripts/fetch_transit.py
"""

import json
import logging
import time
from pathlib import Path

import httpx2 as httpx

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "transit.geojson"

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"

SOURCES = {
    "bus_stop": (
        "https://data.zagreb.hr/dataset/cc7e45ae-4bad-4a07-bca2-25e82f1e082c"
        "/resource/3b12a182-afa3-4b07-833f-17d8bcf80ea9/download/data.geojson"
    ),
    "tram_stop": (
        "https://opendata.arcgis.com/api/v3/datasets/8f84d42e684141eaa7ceb26d9c9b8f5a_0"
        "/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1"
    ),
}

log = logging.getLogger("fetch_transit")


def get_with_retry(client: httpx.Client, url: str) -> bytes:
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
    """Collapse repeated / trailing whitespace; empty -> None."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def parse_lines(value: str | None) -> list[str]:
    """'121,137,143, 147' -> ['121', '137', '143', '147']."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def fetch(client: httpx.Client, stop_type: str, url: str) -> list[dict]:
    raw = get_with_retry(client, url)
    (RAW_DIR / f"zg_zet_{stop_type}.geojson").write_bytes(raw)
    features = json.loads(raw.decode("utf-8-sig"))["features"]

    out = []
    for f in features:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        out.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "type": stop_type,
                    "id": f"zg-zet/{stop_type}/{p['OBJECTID']}",
                    "name": clean(p.get("Naziv_stajališta")),
                    "direction": clean(p.get("Opis")),
                    "lines": parse_lines(p.get("Linije")),
                    "source_id": "zg-zet",
                },
            }
        )
    unnamed = sum(1 for f in out if f["properties"]["name"] is None)
    no_lines = sum(1 for f in out if not f["properties"]["lines"])
    log.info("%s: %d stops (%d unnamed, %d without lines)", stop_type, len(out), unnamed, no_lines)
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120, follow_redirects=True) as c:
        features = [f for stop_type, url in SOURCES.items() for f in fetch(c, stop_type, url)]

    collection = {
        "type": "FeatureCollection",
        "metadata": {"crs": "EPSG:4326", "sources": {"zg-zet": SOURCES}},
        "features": features,
    }
    text = json.dumps(collection, ensure_ascii=False, indent=1)
    OUT_PATH.write_text(text, encoding="utf-8", newline="\n")
    log.info("wrote %s: %d stops", OUT_PATH.relative_to(ROOT), len(features))


if __name__ == "__main__":
    main()
