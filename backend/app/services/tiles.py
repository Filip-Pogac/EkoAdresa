"""Map tiles for the flood and noise WMS layers, proxied and cached on disk.

Why a proxy: zg-buka sends no CORS headers, so the browser map (WebGL) cannot use its
images directly. The cache also keeps the map working when a service is slow or down
(CLAUDE.md §3.11) and keeps our request rate to public services low.

Tiles are XYZ / EPSG:3857 (Web Mercator), as MapLibre requests them. hv-poplave draws
nothing below 1:20 000 (docs/data-sources.md), i.e. from zoom 15: those tiles are cut
from the zoom-14 tile and enlarged.
"""

import asyncio
import io
import math
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx2 as httpx
from PIL import Image

from app.services import wms
from app.services.flood import HV_POPLAVE_URL, layer_name
from app.services.noise import SOURCES, ZG_BUKA_URL

TILE_PX = 256
MIN_ZOOM, MAX_ZOOM = 10, 18
TTL_S = 30 * 24 * 3600  # static map datasets, as app.cache
EARTH_HALF_M = math.pi * 6_378_137  # half the EPSG:3857 world width
# Tiles must touch the City of Zagreb extent (zg-buka road layer, docs/data-sources.md),
# so the endpoint is not an open proxy for the rest of the world.
ZAGREB_LON = (15.77, 16.23)
ZAGREB_LAT = (45.62, 45.97)


@dataclass(frozen=True)
class TileLayer:
    url: str
    layers: list[str]
    max_native_zoom: int  # deeper tiles are enlarged from this zoom
    source_id: str


TILE_LAYERS = {
    # low-probability scenario: the widest flood extent; colour = depth class
    "flood": TileLayer(HV_POPLAVE_URL, [layer_name("low")], 14, "hv-poplave"),
    # Lden of every source; where sources overlap the last one listed is drawn on top
    "noise": TileLayer(ZG_BUKA_URL, [f"SKB_R4_{s}_Lden" for s in SOURCES], MAX_ZOOM, "zg-buka"),
}

_upstream = asyncio.Semaphore(4)  # be polite to the public services


class TileOutOfRange(ValueError):
    """Zoom or position outside what the endpoint serves."""


def tile_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """EPSG:3857 bbox (min_x, min_y, max_x, max_y) of an XYZ tile."""
    size = 2 * EARTH_HALF_M / 2**z
    min_x = -EARTH_HALF_M + x * size
    max_y = EARTH_HALF_M - y * size
    return min_x, max_y - size, min_x + size, max_y


def _lon_lat(x_m: float, y_m: float) -> tuple[float, float]:
    lon = math.degrees(x_m / 6_378_137)
    lat = math.degrees(2 * math.atan(math.exp(y_m / 6_378_137)) - math.pi / 2)
    return lon, lat


def check_tile(z: int, x: int, y: int) -> None:
    if not MIN_ZOOM <= z <= MAX_ZOOM or not (0 <= x < 2**z and 0 <= y < 2**z):
        raise TileOutOfRange("zoom or tile index out of range")
    min_x, min_y, max_x, max_y = tile_bounds(z, x, y)
    (lon0, lat0), (lon1, lat1) = _lon_lat(min_x, min_y), _lon_lat(max_x, max_y)
    if lon1 < ZAGREB_LON[0] or lon0 > ZAGREB_LON[1] or lat1 < ZAGREB_LAT[0] or lat0 > ZAGREB_LAT[1]:
        raise TileOutOfRange("tile outside the City of Zagreb")


async def _fetch(client: httpx.AsyncClient, layer: TileLayer, z: int, x: int, y: int) -> bytes:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": ",".join(layer.layers),
        "STYLES": "",
        "CRS": "EPSG:3857",
        "BBOX": ",".join(f"{v:.3f}" for v in tile_bounds(z, x, y)),
        "WIDTH": TILE_PX,
        "HEIGHT": TILE_PX,
        "FORMAT": "image/png",
        "TRANSPARENT": "TRUE",
    }

    def checked_png(resp: httpx.Response) -> bytes:
        Image.open(io.BytesIO(resp.content)).load()  # truncated / not a PNG -> retried
        return resp.content

    async with _upstream:
        return await wms._get(client, layer.url, params, checked_png)


def _enlarge(parent_png: bytes, dz: int, x: int, y: int) -> bytes:
    """Cut the part of the parent tile covering tile (x, y), dz zoom levels deeper."""
    sub = TILE_PX >> dz
    left, top = (x % 2**dz) * sub, (y % 2**dz) * sub
    image = Image.open(io.BytesIO(parent_png)).convert("RGBA")
    part = image.crop((left, top, left + sub, top + sub)).resize((TILE_PX, TILE_PX), Image.NEAREST)
    out = io.BytesIO()
    part.save(out, format="PNG", optimize=True)
    return out.getvalue()


async def get_tile(
    client: httpx.AsyncClient, cache_dir: Path, name: str, z: int, x: int, y: int
) -> bytes:
    """PNG tile, from the disk cache when fresh; a stale copy if the service fails.

    Raises KeyError for an unknown layer, TileOutOfRange, or wms.WMSError when the service
    fails and nothing is cached.
    """
    layer = TILE_LAYERS[name]
    check_tile(z, x, y)
    path = cache_dir / "tiles" / name / str(z) / str(x) / f"{y}.png"
    if path.exists() and time.time() - path.stat().st_mtime < TTL_S:
        return path.read_bytes()
    try:
        if z > layer.max_native_zoom:
            dz = z - layer.max_native_zoom
            parent = await get_tile(
                client, cache_dir, name, layer.max_native_zoom, x >> dz, y >> dz
            )
            png = _enlarge(parent, dz, x, y)
        else:
            png = await _fetch(client, layer, z, x, y)
    except wms.WMSError:
        if path.exists():
            return path.read_bytes()  # stale, better than an empty map
        raise
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{y}.{uuid.uuid4().hex}.tmp")
    tmp.write_bytes(png)
    tmp.replace(path)  # atomic: a parallel request never reads half a file
    return png
