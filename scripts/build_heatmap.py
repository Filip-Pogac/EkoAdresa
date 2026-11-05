"""EkoSkor heatmap: 250 x 250 m grid over the City of Zagreb -> data/heatmap.geojson.

Same formula as the address card (backend/app/services/ekoskor.py), evaluated at each
cell centre:
- flood:    hv-poplave rendered in large GetMap tiles at the same ~7 m/px scale as the
            point lookup (~300 requests instead of ~30 000); pixel at the cell centre
- noise:    zg-buka GetFeatureInfo per cell, exactly as the point lookup, through the
            SQLite cache (resumable), 2 requests at a time
- air:      mean PM10 Jan-Aug 2023 of the nearest City station (data/air_history.parquet)
- waste:    data/waste.geojson (fixed yards only, OSM green islands)
- mobility: data/transit.geojson (platforms)

Grid: EPSG:3765 (HTRS96/TM, metres), cells aligned to multiples of 250 m, kept if the
centre lies inside the City boundary (OpenStreetMap, ISO 3166-2 HR-21). Output in EPSG:4326.

Run from the repo root:  uv run --project backend python scripts/build_heatmap.py
Takes ~30 min on a cold cache (noise); re-runs read the cache and take ~1 min.
"""

import asyncio
import io
import json
import logging
import math
import sys
import time
from pathlib import Path

import httpx2 as httpx
import numpy as np
import pandas as pd
import shapely
from PIL import Image
from pyproj import Transformer
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.cache import Cache, cached_fetch  # noqa: E402
from app.services import ekoskor, flood, noise, wms  # noqa: E402

DATA = ROOT / "data"
RAW = DATA / "raw" / "heatmap"
OUT_PATH = DATA / "heatmap.geojson"
BOUNDARY_PATH = DATA / "zagreb_boundary.geojson"  # also used by the API (geocode filter)

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BOUNDARY_QUERY = (
    '[out:json][timeout:90];rel["ISO3166-2"="HR-21"]["boundary"="administrative"];out geom;'
)

CELL_M = 250
FLOOD_M_PER_PX = 7.0  # same scale as wms.get_map_pixel (707 m / 101 px), ~1:25 000
# 1000 px tiles were cut off mid-transfer ~2 of 3 times where there is much flood data;
# 500 px tiles succeeded every time (2026-11-05).
FLOOD_TILE_PX = 500
NOISE_CONCURRENCY = 2

to_htrs = Transformer.from_crs("EPSG:4326", "EPSG:3765", always_xy=True)  # lon/lat -> x/y m
to_wgs = Transformer.from_crs("EPSG:3765", "EPSG:4326", always_xy=True)

log = logging.getLogger("build_heatmap")


# --- boundary and grid -----------------------------------------------------------------


def fetch_boundary(client: httpx.Client) -> shapely.Geometry:
    """City of Zagreb boundary (EPSG:4326) from the OSM admin relation, cached in data/raw."""
    raw_path = RAW / "zagreb_boundary_osm.json"
    if not raw_path.exists():
        for attempt in range(1, 5):
            resp = client.post(OVERPASS_URL, data={"data": BOUNDARY_QUERY})
            if resp.status_code == 200:
                raw_path.write_bytes(resp.content)
                break
            log.warning("Overpass HTTP %s (attempt %d)", resp.status_code, attempt)
            time.sleep(5 * 2**attempt)
        else:
            raise RuntimeError("Overpass failed for the City boundary")
    relations = json.loads(raw_path.read_bytes())["elements"]
    if len(relations) != 1:
        raise RuntimeError(f"expected 1 boundary relation, got {len(relations)}")
    rel = relations[0]
    lines = [
        shapely.LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
        for m in rel["members"]
        if m["type"] == "way" and m.get("role") == "outer"
    ]
    boundary = unary_union(list(polygonize(lines)))
    log.info("boundary: OSM relation %s '%s'", rel["id"], rel["tags"].get("name"))
    return boundary


def write_boundary(boundary: shapely.Geometry) -> None:
    """City boundary as GeoJSON (EPSG:4326, 6 decimals ~ 0.1 m), source osm-granice."""
    geometry = json.loads(shapely.to_geojson(shapely.set_precision(boundary, 1e-6)))
    collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {"name": "Grad Zagreb", "source_id": "osm-granice"},
            }
        ],
    }
    text = json.dumps(collection, separators=(",", ":"))
    BOUNDARY_PATH.write_text(text, encoding="utf-8", newline="\n")
    log.info("wrote %s", BOUNDARY_PATH.relative_to(ROOT))


def build_grid(boundary_wgs: shapely.Geometry) -> pd.DataFrame:
    boundary = shapely.transform(boundary_wgs, lambda xy: np.column_stack(to_htrs.transform(*xy.T)))
    min_x, min_y, max_x, max_y = boundary.bounds
    xs = np.arange(math.floor(min_x / CELL_M) * CELL_M, max_x, CELL_M) + CELL_M / 2
    ys = np.arange(math.floor(min_y / CELL_M) * CELL_M, max_y, CELL_M) + CELL_M / 2
    cx, cy = (a.ravel() for a in np.meshgrid(xs, ys))
    inside = shapely.contains_xy(boundary, cx, cy)
    cx, cy = cx[inside], cy[inside]
    lon, lat = to_wgs.transform(cx, cy)
    log.info("grid: %d cells of %d m (area %.0f km2)", len(cx), CELL_M, boundary.area / 1e6)
    return pd.DataFrame({"x": cx, "y": cy, "lon": lon, "lat": lat})


# --- flood -----------------------------------------------------------------------------


async def fetch_tile(
    client: httpx.AsyncClient, layer: str, bbox: tuple[float, float, float, float]
) -> bytes:
    """wms.get_map_png, plus patient retries: a batch job has no latency budget, and
    hv-poplave fails often where it has flood polygons (see docs/data-sources.md)."""
    for round_ in range(1, 6):
        try:
            return await wms.get_map_png(client, flood.HV_POPLAVE_URL, layer, bbox, FLOOD_TILE_PX)
        except wms.WMSError:
            if round_ == 5:
                raise
            log.warning("flood tile failed (round %d), waiting %d s", round_, 5 * 2**round_)
            await asyncio.sleep(5 * 2**round_)
    raise AssertionError("unreachable")


async def flood_zones(client: httpx.AsyncClient, grid: pd.DataFrame) -> list[str]:
    """Zone per cell from GetMap tiles; tiles are cached as PNG in data/raw/heatmap."""
    lat_mid = grid["lat"].mean()
    tile_dlat = FLOOD_M_PER_PX * FLOOD_TILE_PX / wms.M_PER_DEG_LAT
    m_per_deg_lon = wms.M_PER_DEG_LON_EQUATOR * math.cos(math.radians(lat_mid))
    tile_dlon = FLOOD_M_PER_PX * FLOOD_TILE_PX / m_per_deg_lon
    lon0, lat0 = grid["lon"].min() - 1e-4, grid["lat"].min() - 1e-4
    col = ((grid["lon"] - lon0) / tile_dlon).astype(int).to_numpy()
    row = ((grid["lat"] - lat0) / tile_dlat).astype(int).to_numpy()
    tiles = sorted(set(zip(col.tolist(), row.tolist(), strict=True)))

    inside: dict[str, np.ndarray] = {}
    for zone in flood.SCENARIOS:
        hit = np.zeros(len(grid), dtype=bool)
        for c, r in tiles:
            bbox = (lon0 + c * tile_dlon, lat0 + r * tile_dlat)
            bbox = (*bbox, bbox[0] + tile_dlon, bbox[1] + tile_dlat)
            tile_path = RAW / f"flood_{FLOOD_TILE_PX}px_{flood.SCENARIOS[zone]}_{c}_{r}.png"
            if not tile_path.exists():
                tile_path.write_bytes(await fetch_tile(client, flood.layer_name(zone), bbox))
            alpha = np.asarray(Image.open(io.BytesIO(tile_path.read_bytes())).convert("RGBA"))[
                :, :, 3
            ]
            sel = (col == c) & (row == r)
            px_x = ((grid["lon"].to_numpy()[sel] - bbox[0]) / tile_dlon * FLOOD_TILE_PX).astype(int)
            px_y = ((bbox[3] - grid["lat"].to_numpy()[sel]) / tile_dlat * FLOOD_TILE_PX).astype(int)
            hit[sel] = alpha[px_y.clip(0, FLOOD_TILE_PX - 1), px_x.clip(0, FLOOD_TILE_PX - 1)] > 0
        inside[zone] = hit
        log.info("flood %s: %d tiles, %d cells inside", zone, len(tiles), hit.sum())

    return [
        flood.zone_from_colours({z: "x" if inside[z][i] else None for z in flood.SCENARIOS})
        for i in range(len(grid))
    ]


# --- noise -----------------------------------------------------------------------------


async def noise_lden(client: httpx.AsyncClient, grid: pd.DataFrame) -> list[int | None | str]:
    """Loudest Lden band per cell; 'unavailable' where the service failed with no cache."""
    cache = Cache()
    sem = asyncio.Semaphore(NOISE_CONCURRENCY)
    done = 0
    started = time.perf_counter()

    async def one(lat: float, lon: float) -> int | None | str:
        nonlocal done
        async with sem:
            try:
                result = await cached_fetch(
                    cache,
                    noise.CACHE_NAMESPACE,
                    lat,
                    lon,
                    lambda: wms.get_feature_info(
                        client,
                        noise.ZG_BUKA_URL,
                        noise.LAYERS,
                        lat,
                        lon,
                        property_names=noise.PROPERTY_NAMES,
                    ),
                )
                value: int | None | str = noise.loudest(noise.bands_from_features(result.value))
            except wms.WMSError:
                value = "unavailable"
        done += 1
        if done % 500 == 0:
            log.info("noise: %d / %d (%.0f s)", done, len(grid), time.perf_counter() - started)
        return value

    return await asyncio.gather(
        *(one(lat, lon) for lat, lon in zip(grid["lat"], grid["lon"], strict=True))
    )


# --- local layers ----------------------------------------------------------------------


def project(features: list[dict]) -> np.ndarray:
    lon, lat = np.array([f["geometry"]["coordinates"] for f in features]).T
    return np.column_stack(to_htrs.transform(lon, lat))


def nearest_m(cells: np.ndarray, points: np.ndarray) -> np.ndarray:
    out = np.empty(len(cells))
    for i in range(0, len(cells), 2000):  # chunks keep the distance matrix small
        d = np.hypot(*(cells[i : i + 2000, None, :] - points[None, :, :]).transpose(2, 0, 1))
        out[i : i + 2000] = d.min(axis=1)
    return out


def count_within(cells: np.ndarray, points: np.ndarray, radius_m: float) -> np.ndarray:
    out = np.empty(len(cells), dtype=int)
    for i in range(0, len(cells), 2000):
        d = np.hypot(*(cells[i : i + 2000, None, :] - points[None, :, :]).transpose(2, 0, 1))
        out[i : i + 2000] = (d <= radius_m).sum(axis=1)
    return out


def local_layers(grid: pd.DataFrame) -> pd.DataFrame:
    cells = grid[["x", "y"]].to_numpy()

    waste = json.loads((DATA / "waste.geojson").read_text(encoding="utf-8"))["features"]
    yards = [
        f
        for f in waste
        if f["properties"]["type"] == "recycling_yard" and f["properties"]["kind"] == "fixed"
    ]
    islands = [f for f in waste if f["properties"]["type"] == "green_island"]
    stops = json.loads((DATA / "transit.geojson").read_text(encoding="utf-8"))["features"]

    stations = json.loads((DATA / "air_stations.geojson").read_text(encoding="utf-8"))["features"]
    history = pd.read_parquet(DATA / "air_history.parquet")
    pm10 = history[history["pollutant"] == "pm10"].groupby("station_id")["value_ug_m3"].mean()
    station_xy = project(stations)
    nearest_station = np.argmin(
        np.hypot(*(cells[:, None, :] - station_xy[None, :, :]).transpose(2, 0, 1)), axis=1
    )
    station_ids = [s["properties"]["id"] for s in stations]
    log.info("air: PM10 mean Jan-Aug 2023 per station %s", pm10.round(1).to_dict())

    stop_xy = project(stops)
    return pd.DataFrame(
        {
            "yard_m": nearest_m(cells, project(yards)),
            "island_m": nearest_m(cells, project(islands)),
            "stops_300m": count_within(cells, stop_xy, ekoskor.STOPS_NEAR_M),
            "stops_500m": count_within(cells, stop_xy, ekoskor.STOPS_WALK_M),
            "air_station": [station_ids[i] for i in nearest_station],
            "pm10": [pm10[station_ids[i]] for i in nearest_station],
        }
    )


# --- output ----------------------------------------------------------------------------


def cell_polygon(x: float, y: float) -> list[list[list[float]]]:
    h = CELL_M / 2
    xs = [x - h, x + h, x + h, x - h, x - h]
    ys = [y - h, y - h, y + h, y + h, y - h]
    lon, lat = to_wgs.transform(xs, ys)
    return [[[round(a, 5), round(b, 5)] for a, b in zip(lon, lat, strict=True)]]


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    RAW.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120) as c:
        boundary = fetch_boundary(c)
    write_boundary(boundary)
    grid = build_grid(boundary)

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=30) as client:
        zones = await flood_zones(client, grid)
        ldens = await noise_lden(client, grid)
    local = local_layers(grid)

    features = []
    unavailable_noise = 0
    for i, cell in grid.iterrows():
        loc = local.iloc[i]
        lden = ldens[i]
        if lden == "unavailable":
            unavailable_noise += 1
        scores: dict[ekoskor.Layer, float | None] = {
            "flood": ekoskor.flood_score(zones[i]),  # type: ignore[arg-type]
            "noise": None if lden == "unavailable" else ekoskor.noise_score(lden),  # type: ignore[arg-type]
            "air": ekoskor.air_score(loc["pm10"]),
            "waste": ekoskor.waste_score(loc["yard_m"], loc["island_m"]),
            "mobility": ekoskor.mobility_score(int(loc["stops_300m"]), int(loc["stops_500m"])),
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": cell_polygon(cell["x"], cell["y"])},
                "properties": {
                    "ekoskor": ekoskor.ekoskor(scores),
                    **{k: None if v is None else round(v) for k, v in scores.items()},
                },
            }
        )

    collection = {
        "type": "FeatureCollection",
        "metadata": {
            "crs": "EPSG:4326",
            "grid": f"{CELL_M} m cells in EPSG:3765, centre inside City of Zagreb (OSM HR-21)",
            "formula": "docs/ekoskor.md",
            "air": "PM10 mean Jan-Aug 2023, nearest City station",
            "sources": [
                "hv-poplave",
                "zg-buka",
                "zg-zrak-mjerenja",
                "zg-zrak-postaje",
                "zg-reciklaza",
                "osm-reciklaza",
                "zg-zet",
                "osm-granice",
            ],
        },
        "features": features,
    }
    text = json.dumps(collection, ensure_ascii=False, separators=(",", ":"))
    OUT_PATH.write_text(text, encoding="utf-8", newline="\n")
    scored = [s for f in features if (s := f["properties"]["ekoskor"]) is not None]
    log.info(
        "wrote %s: %d cells, noise unavailable in %d, EkoSkor min %d / median %d / max %d",
        OUT_PATH.relative_to(ROOT),
        len(features),
        unavailable_noise,
        min(scored),
        int(np.median(scored)),
        max(scored),
    )


if __name__ == "__main__":
    asyncio.run(main())
