"""Fetch bike paths (Grad Zagreb) and parks and forests (OpenStreetMap) for green mobility.

Sources (see docs/data-sources.md):
- zg-biciklisticke-staze: Geoportal Biciklističke staze, data.zagreb.hr, ArcGIS Hub GeoJSON
  export, EPSG:4326 -> data/bike_paths.geojson (lines)
- osm-parkovi: OSM leisure=park, leisure=garden (not private), leisure=nature_reserve,
  landuse=forest and natural=wood inside Grad Zagreb, via Overpass, written twice from the
  same download:
  - data/parks.geojson: areas of at least MIN_AREA_M2, used for the Zelenilo score
  - data/parks_all.geojson: every area, any size, used only for the map layer (2026-11-08)

Geometries are simplified in EPSG:3765 (HTRS96/TM, metres) by SIMPLIFY_M and written in
EPSG:4326. Raw downloads go to data/raw/.

Run from the repo root:  uv run --project backend python scripts/fetch_green_mobility.py
Add --offline to rebuild the files from the raw downloads in data/raw/ without fetching.
"""

import json
import logging
import sys
import time
from pathlib import Path

import httpx2 as httpx
import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
BIKE_PATH = ROOT / "data" / "bike_paths.geojson"
PARKS_PATH = ROOT / "data" / "parks.geojson"
PARKS_ALL_PATH = ROOT / "data" / "parks_all.geojson"

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"

BIKE_URL = (
    "https://opendata.arcgis.com/api/v3/datasets/b10db2ae3a5b4e4b8dbee85a89d4b5b1_4"
    "/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1"
)
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
# Grad Zagreb = ISO 3166-2 HR-21
OVERPASS_QUERY = (
    "[out:json][timeout:180];"
    'area["ISO3166-2"="HR-21"]["admin_level"]->.zg;'
    "("
    'way["leisure"="park"](area.zg);rel["leisure"="park"](area.zg);'
    'way["leisure"="garden"]["access"!="private"](area.zg);'
    'rel["leisure"="garden"]["access"!="private"](area.zg);'
    'way["leisure"="nature_reserve"](area.zg);rel["leisure"="nature_reserve"](area.zg);'
    'way["landuse"="forest"](area.zg);rel["landuse"="forest"](area.zg);'
    'way["natural"="wood"](area.zg);rel["natural"="wood"](area.zg);'
    ");out geom;"
)
# WHO Regional Office for Europe (2017), Urban green spaces: a brief for action: green space
# of at least 0.5-1 ha within 300 m linear distance. Smaller patches are left out.
MIN_AREA_M2 = 5000
SIMPLIFY_M = 2.0

to_htrs = Transformer.from_crs("EPSG:4326", "EPSG:3765", always_xy=True)
to_wgs = Transformer.from_crs("EPSG:3765", "EPSG:4326", always_xy=True)

log = logging.getLogger("fetch_green_mobility")


def request_with_retry(client: httpx.Client, url: str, **kwargs: object) -> httpx.Response:
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


def _xy_to_wgs(xy: np.ndarray) -> np.ndarray:
    lon, lat = to_wgs.transform(xy[:, 0], xy[:, 1])
    return np.column_stack([lon, lat])


def _wgs_to_xy(lonlat: np.ndarray) -> np.ndarray:
    x, y = to_htrs.transform(lonlat[:, 0], lonlat[:, 1])
    return np.column_stack([x, y])


def to_wgs_rounded(geom_m: shapely.Geometry) -> dict:
    """Simplify in metres, back to EPSG:4326, coordinates rounded to 6 decimals (~0.1 m)."""
    simple = geom_m.simplify(SIMPLIFY_M, preserve_topology=True)
    return mapping(shapely.set_precision(shapely.transform(simple, _xy_to_wgs), 1e-6))


def download_bike_paths(client: httpx.Client) -> bytes:
    raw = request_with_retry(client, BIKE_URL).content
    (RAW_DIR / "zg_biciklisticke_staze.geojson").write_bytes(raw)
    return raw


def build_bike_paths(raw: bytes) -> list[dict]:
    features = json.loads(raw)["features"]
    log.info("zg-biciklisticke-staze: %d raw features", len(features))
    out = []
    for f in features:
        if not f["geometry"]:
            continue
        p = f["properties"]
        geom_m = shapely.transform(shape(f["geometry"]), _wgs_to_xy)
        out.append(
            {
                "type": "Feature",
                "geometry": to_wgs_rounded(geom_m),
                "properties": {
                    "id": f"zg-biciklisticke-staze/{p['OBJECTID']}",
                    "name": " ".join(str(p.get("lokacija") or "").split()) or None,
                    "category": p.get("kategorija_id"),  # TODO(verify): codes not documented
                    "source_id": "zg-biciklisticke-staze",
                },
            }
        )
    return out


def _ring(way_geometry: list[dict]) -> list[tuple[float, float]]:
    return [(n["lon"], n["lat"]) for n in way_geometry]


def _area(el: dict) -> shapely.Geometry | None:
    """Polygon of a closed way or a multipolygon relation, in EPSG:4326; None if not closed."""
    if el["type"] == "way":
        ring = _ring(el.get("geometry", []))
        if len(ring) < 4 or ring[0] != ring[-1]:
            return None
        return shapely.Polygon(ring)
    outer = [
        shapely.LineString(_ring(m["geometry"]))
        for m in el.get("members", [])
        if m.get("role") in ("outer", "") and m["type"] == "way" and m.get("geometry")
    ]
    inner = [
        shapely.LineString(_ring(m["geometry"]))
        for m in el.get("members", [])
        if m.get("role") == "inner" and m["type"] == "way" and m.get("geometry")
    ]
    outer_poly = unary_union(list(polygonize(unary_union(outer)))) if outer else None
    if outer_poly is None or outer_poly.is_empty:
        return None
    if inner:
        holes = unary_union(list(polygonize(unary_union(inner))))
        outer_poly = outer_poly.difference(holes)
    return outer_poly


def download_parks(client: httpx.Client) -> bytes:
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            resp = request_with_retry(client, url, data={"data": OVERPASS_QUERY})
            break
        except RuntimeError as exc:
            last_error = exc
    else:
        raise RuntimeError("all Overpass endpoints failed") from last_error
    (RAW_DIR / "osm_parks_forests.json").write_bytes(resp.content)
    return resp.content


def build_parks(raw: bytes) -> tuple[list[dict], list[dict], str]:
    """(areas of at least MIN_AREA_M2 for the score, every area for the map, OSM timestamp)."""
    payload = json.loads(raw)
    osm_timestamp = payload["osm3s"]["timestamp_osm_base"]
    elements = payload["elements"]
    log.info("osm-parkovi: %d raw elements (OSM data as of %s)", len(elements), osm_timestamp)

    out, all_areas, small, broken = [], [], 0, 0
    for el in elements:
        tags = el.get("tags", {})
        geom = _area(el)
        if geom is None or geom.is_empty:
            broken += 1
            continue
        geom_m = shapely.make_valid(shapely.transform(geom, _wgs_to_xy))
        kind = "park" if tags.get("leisure") in ("park", "garden", "nature_reserve") else "forest"
        feature = {
            "type": "Feature",
            "geometry": to_wgs_rounded(geom_m),
            "properties": {
                "id": f"osm/{el['type']}/{el['id']}",
                "name": tags.get("name"),
                "kind": kind,
                "area_m2": round(geom_m.area),
                "source_id": "osm-parkovi",
            },
        }
        all_areas.append(feature)
        if geom_m.area < MIN_AREA_M2:
            small += 1
            continue
        out.append(feature)
    log.info(
        "osm-parkovi: kept %d for the score, %d below %d m2 (map only), %d not closed",
        len(out),
        small,
        MIN_AREA_M2,
        broken,
    )
    return out, all_areas, osm_timestamp


def write(path: Path, features: list[dict], metadata: dict) -> None:
    collection = {"type": "FeatureCollection", "metadata": metadata, "features": features}
    text = json.dumps(collection, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8", newline="\n")
    log.info(
        "wrote %s: %d features, %d kB", path.relative_to(ROOT), len(features), len(text) // 1024
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if "--offline" in sys.argv:
        bikes_raw = (RAW_DIR / "zg_biciklisticke_staze.geojson").read_bytes()
        parks_raw = (RAW_DIR / "osm_parks_forests.json").read_bytes()
    else:
        with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=240) as client:
            bikes_raw = download_bike_paths(client)
            parks_raw = download_parks(client)
    bikes = build_bike_paths(bikes_raw)
    parks, parks_all, osm_timestamp = build_parks(parks_raw)
    write(BIKE_PATH, bikes, {"crs": "EPSG:4326", "source_id": "zg-biciklisticke-staze"})
    meta = {"crs": "EPSG:4326", "source_id": "osm-parkovi", "osm_timestamp": osm_timestamp}
    write(PARKS_PATH, parks, meta | {"min_area_m2": MIN_AREA_M2})
    write(PARKS_ALL_PATH, parks_all, meta | {"min_area_m2": 0, "use": "map only"})


if __name__ == "__main__":
    main()
