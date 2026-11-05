"""Minimal OGC WMS 1.3.0 client for point queries.

Coordinates are EPSG:4326 (lat, lon) everywhere in EkoAdresa. Both WMS services we use
(hv-poplave, zg-buka) accept CRS:84 (WGS84 with lon/lat axis order), so no reprojection
is needed here. See docs/data-sources.md for the Phase 0 tests behind every parameter.

- get_feature_info: for queryable layers (zg-buka noise map)
- get_map_pixel:    for layers that refuse GetFeatureInfo (hv-poplave flood map): render a
                    small map around the point and read the colour of the centre pixel
"""

import asyncio
import io
import logging
import math
from collections.abc import Callable
from typing import TypeVar

import httpx2 as httpx
from PIL import Image

from app.http import USER_AGENT

log = logging.getLogger(__name__)
T = TypeVar("T")

# hv-poplave returns HTTP 502 for ~10 % of GetMap requests, but only where it has flood
# polygons to draw (Savica 4/40 vs 0/40 at two points outside zones, 2026-11-04), sometimes
# 3 in a row; it also once sent a truncated PNG. 4 attempts with 0.2, 0.4, 0.8 s backoff add
# at most ~2 s, which fits the 4 s per-layer budget of /api/profile. The cache is the real
# safety net.
MAX_ATTEMPTS = 4
RETRY_DELAY_S = 0.2

M_PER_DEG_LAT = 110_574.0
M_PER_DEG_LON_EQUATOR = 111_320.0


class WMSError(Exception):
    """The service answered, but not with usable data (ServiceException, bad image…)."""


def _common_params(request: str, layers: list[str], bbox: tuple[float, ...], px: int) -> dict:
    return {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": request,
        "LAYERS": ",".join(layers),
        "STYLES": "",
        "CRS": "CRS:84",  # lon/lat axis order, so BBOX = min_lon,min_lat,max_lon,max_lat
        "BBOX": ",".join(f"{v:.7f}" for v in bbox),
        "WIDTH": px,
        "HEIGHT": px,
    }


def _bbox_around(lat: float, lon: float, half_m: float) -> tuple[float, float, float, float]:
    dlat = half_m / M_PER_DEG_LAT
    dlon = half_m / (M_PER_DEG_LON_EQUATOR * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def _describe(exc: Exception) -> str:
    """Error without its URL: request URLs contain the queried coordinates, and addresses
    must not end up in logs (CLAUDE.md §2.7)."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return type(exc).__name__


async def _get(
    client: httpx.AsyncClient, url: str, params: dict, parse: Callable[[httpx.Response], T]
) -> T:
    """GET and parse, retrying on network errors, 5xx and unparseable (e.g. truncated) bodies."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = await client.get(url, params=params, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            if b"ServiceException" in resp.content[:2000]:
                # A definite answer (e.g. LayerNotQueryable): retrying will not help.
                raise WMSError(resp.text[:300])
            return parse(resp)
        except (httpx.HTTPError, ValueError, OSError) as exc:
            last_error = exc
            log.warning(
                "WMS %s %s failed (attempt %d): %s", url, params["REQUEST"], attempt, _describe(exc)
            )
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(RETRY_DELAY_S * 2 ** (attempt - 1))
    raise WMSError(f"{url}: {_describe(last_error)}") from last_error  # type: ignore[arg-type]


def _parse_features(resp: httpx.Response) -> list[dict]:
    features = resp.json().get("features")  # ValueError if not JSON -> retried
    if not isinstance(features, list):
        raise ValueError(f"not a GeoJSON FeatureCollection: {resp.text[:300]}")
    return features


async def get_feature_info(
    client: httpx.AsyncClient,
    service_url: str,
    layers: list[str],
    lat: float,
    lon: float,
    feature_count: int = 20,
    property_names: list[str] | None = None,
) -> list[dict]:
    """Return the GeoJSON features of `layers` at the point (may be empty).

    BUFFER=0 and a ~20 m box: without them the server's pixel tolerance can return two
    adjacent bands at a band edge (seen at Savica in Phase 0).

    `property_names` uses the GeoServer vendor parameter `propertyName` to return only those
    attributes and no geometry. For zg-buka at Savica this cuts the response from 1.1 MB /
    1.4 s to 394 B / 0.3 s (2026-11-05), because the noise bands are huge polygons.
    """
    d_deg = 0.0001
    params = _common_params(
        "GetFeatureInfo", layers, (lon - d_deg, lat - d_deg, lon + d_deg, lat + d_deg), 101
    )
    params |= {
        "QUERY_LAYERS": ",".join(layers),
        "I": 50,
        "J": 50,
        "INFO_FORMAT": "application/json",
        "FEATURE_COUNT": feature_count,
        "BUFFER": 0,
    }
    if property_names:
        # one parenthesised list per layer, in LAYERS order
        params["propertyName"] = f"({','.join(property_names)})" * len(layers)
    return await _get(client, service_url, params, _parse_features)


async def get_map_pixel(
    client: httpx.AsyncClient,
    service_url: str,
    layer: str,
    lat: float,
    lon: float,
    half_m: float = 353.5,
    px: int = 101,
) -> str | None:
    """Colour of the rendered `layer` at the point as '#RRGGBB', or None if transparent.

    Defaults give a ~707 m box at ~7 m/px (~1:25 000). The hv-poplave layers draw nothing
    when zoomed in past 1:20 000, so do not shrink the box without re-checking that.
    """
    png = await get_map_png(client, service_url, layer, _bbox_around(lat, lon, half_m), px)
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    r, g, b, a = image.getpixel((px // 2, px // 2))  # type: ignore[misc]
    return None if a == 0 else f"#{r:02X}{g:02X}{b:02X}"


async def get_map_png(
    client: httpx.AsyncClient,
    service_url: str,
    layer: str,
    bbox: tuple[float, float, float, float],
    px: int,
) -> bytes:
    """Square transparent PNG of `layer` for bbox (min_lon, min_lat, max_lon, max_lat).

    The body is fully decoded before it is returned, so a truncated PNG is retried.
    """
    params = _common_params("GetMap", [layer], bbox, px)
    params |= {"FORMAT": "image/png", "TRANSPARENT": "TRUE"}

    def checked_png(resp: httpx.Response) -> bytes:
        # UnidentifiedImageError and truncated-PNG errors are OSError subclasses -> retried
        Image.open(io.BytesIO(resp.content)).load()
        return resp.content

    return await _get(client, service_url, params, checked_png)
