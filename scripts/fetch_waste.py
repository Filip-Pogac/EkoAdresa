"""Fetch recycling yards (Grad Zagreb) and green islands (OpenStreetMap) into data/waste.geojson.

Sources (see docs/data-sources.md):
- zg-reciklaza: Geoportal Reciklažna dvorišta grada Zagreba, ArcGIS Hub GeoJSON export, EPSG:4326
- osm-reciklaza: OSM amenity=recycling + recycling_type=container inside Grad Zagreb, via Overpass

Output: one GeoJSON FeatureCollection, EPSG:4326, every feature has `type`
(`recycling_yard` | `green_island`) and `source_id`. Raw downloads go to data/raw/.

Run from the repo root:  uv run --project backend python scripts/fetch_waste.py
"""

import json
import logging
import time
from pathlib import Path

import httpx2 as httpx

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "waste.geojson"

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"

YARDS_URL = (
    "https://opendata.arcgis.com/api/v3/datasets/249fa384ccf9481abf4fd2de73a822f5_0"
    "/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1"
)

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
# Grad Zagreb = ISO 3166-2 HR-21. `out center` gives a point for the few containers mapped as ways.
OVERPASS_QUERY = (
    "[out:json][timeout:90];"
    'area["ISO3166-2"="HR-21"]["admin_level"]->.zg;'
    'nwr["amenity"="recycling"]["recycling_type"="container"](area.zg);'
    "out center tags;"
)
# A green island (zeleni otok) takes paper, plastic or glass. Containers that only take
# garden waste, clothes or scrap metal are not green islands.
GREEN_ISLAND_PREFIXES = ("recycling:paper", "recycling:plastic", "recycling:glass")

# Accepted-waste flags in zg-reciklaza (values "DA"/"NE").
YARD_WASTE_FLAGS = {
    "PAPIR": "paper",
    "PLASTIKA": "plastic",
    "STAKLO": "glass",
    "METALNA_AM": "metal_packaging",
    "STARE_BATE": "batteries",
    "BIOOTPAD": "bio_waste",
    "OTPAD_GUME": "tyres",
    "OTPAD_MU": "OTPAD_MU",  # TODO(verify): meaning of the abbreviation not documented
    "GRADJ_OTPA": "construction_waste",
    "ELEK_OTPAD": "electronic_waste",
    "OSTALO": "other",
}

log = logging.getLogger("fetch_waste")


def get_with_retry(client: httpx.Client, url: str, **kwargs: object) -> httpx.Response:
    """GET/POST with exponential backoff; both public services sometimes return 5xx."""
    method = "POST" if "data" in kwargs else "GET"
    delay_s = 5.0
    for attempt in range(1, 5):
        try:
            resp = client.request(method, url, **kwargs)  # type: ignore[arg-type]
            if resp.status_code == 200:
                return resp
            log.warning("%s -> HTTP %s (attempt %d)", url, resp.status_code, attempt)
        except httpx.HTTPError as exc:
            log.warning("%s -> %s (attempt %d)", url, exc, attempt)
        time.sleep(delay_s)
        delay_s *= 2
    raise RuntimeError(f"giving up on {url}")


def clean(value: object) -> str | None:
    """Collapse embedded newlines / repeated spaces; empty -> None."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def fetch_yards(client: httpx.Client) -> list[dict]:
    raw = get_with_retry(client, YARDS_URL).content
    (RAW_DIR / "zg_reciklazna_dvorista.geojson").write_bytes(raw)
    features = json.loads(raw)["features"]
    log.info("zg-reciklaza: %d raw features", len(features))

    out = []
    for f in features:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        kind_text = clean(p["VRSTA"]) or ""
        out.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "type": "recycling_yard",
                    "kind": "mobile" if kind_text.startswith("MOBILNO") else "fixed",
                    "id": f"zg-reciklaza/{p['OBJECTID_1']}",
                    "name": clean(p["NAZIV"]),
                    "address": clean(p["ADRESA_LOK"]),
                    "opening_hours": clean(p["RADNO_VRIJ"]),
                    "accepts": sorted(
                        name for col, name in YARD_WASTE_FLAGS.items() if p.get(col) == "DA"
                    ),
                    "note": clean(p["NAPOMENA"]),
                    "source_id": "zg-reciklaza",
                },
            }
        )
    return out


def fetch_green_islands(client: httpx.Client) -> tuple[list[dict], str]:
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            resp = get_with_retry(client, url, data={"data": OVERPASS_QUERY})
            break
        except RuntimeError as exc:
            last_error = exc
    else:
        raise RuntimeError("all Overpass endpoints failed") from last_error

    (RAW_DIR / "osm_recycling_containers.json").write_bytes(resp.content)
    payload = resp.json()
    osm_timestamp = payload["osm3s"]["timestamp_osm_base"]
    elements = payload["elements"]
    log.info("osm-reciklaza: %d raw elements (OSM data as of %s)", len(elements), osm_timestamp)

    out = []
    for el in elements:
        tags = el.get("tags", {})
        accepts = sorted(
            k.removeprefix("recycling:")
            for k, v in tags.items()
            if k.startswith(GREEN_ISLAND_PREFIXES) and v == "yes"
        )
        if not accepts:
            continue
        lat = el.get("lat", el.get("center", {}).get("lat"))
        lon = el.get("lon", el.get("center", {}).get("lon"))
        out.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "type": "green_island",
                    "id": f"osm/{el['type']}/{el['id']}",
                    "name": tags.get("name"),
                    "accepts": accepts,
                    "source_id": "osm-reciklaza",
                },
            }
        )
    log.info("osm-reciklaza: %d kept as green islands", len(out))
    return out, osm_timestamp


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120, follow_redirects=True) as c:
        yards = fetch_yards(c)
        islands, osm_timestamp = fetch_green_islands(c)

    features = yards + islands
    collection = {
        "type": "FeatureCollection",
        "metadata": {
            "crs": "EPSG:4326",
            "sources": {
                "zg-reciklaza": {"url": YARDS_URL},
                "osm-reciklaza": {
                    "url": OVERPASS_URLS[0],
                    "query": OVERPASS_QUERY,
                    "osm_data_as_of": osm_timestamp,
                },
            },
        },
        "features": features,
    }
    OUT_PATH.write_text(json.dumps(collection, ensure_ascii=False, indent=1), encoding="utf-8")
    fixed = sum(1 for f in yards if f["properties"]["kind"] == "fixed")
    log.info(
        "wrote %s: %d yards (%d fixed, %d mobile), %d green islands",
        OUT_PATH.relative_to(ROOT),
        len(yards),
        fixed,
        len(yards) - fixed,
        len(islands),
    )


if __name__ == "__main__":
    main()
