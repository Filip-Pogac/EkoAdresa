"""Environmental profile of a point: the six layers in parallel, then EkoSkor.

Each layer gets LAYER_TIMEOUT_S; a layer that fails or times out is returned as
UnavailableLayer and the other layers are unaffected (CLAUDE.md §1.3, graceful
degradation). EkoSkor uses the rounded sub-scores shown on the card, so a reader can
recompute it by hand (docs/ekoskor.md).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TypeVar

import httpx2 as httpx

from app.cache import Cache
from app.models import Layers, Location, Profile, UnavailableLayer
from app.services import air, ekoskor, flood, green, mobility, noise, waste

LAYER_TIMEOUT_S = 4.0
SOURCE_IDS = {
    "flood": flood.SOURCE_ID,
    "noise": noise.SOURCE_ID,
    "air": air.SOURCE_ID,
    "waste": waste.SOURCE_ID,
    "mobility": mobility.SOURCE_ID,
    "green": green.SOURCE_ID,
}

log = logging.getLogger(__name__)
L = TypeVar("L")


async def _layer(name: str, compute: Callable[[], Awaitable[L]]) -> L | UnavailableLayer:
    try:
        return await asyncio.wait_for(compute(), LAYER_TIMEOUT_S)
    except TimeoutError:
        log.warning("layer %s timed out after %.1f s", name, LAYER_TIMEOUT_S)
        reason = "timeout"
    except Exception as exc:  # any failure: the other layers must still render
        # No coordinates in the log (CLAUDE.md §2.7): layer name and error type only
        log.warning("layer %s unavailable: %s", name, type(exc).__name__)
        reason = "error"
    return UnavailableLayer(status="unavailable", reason=reason, source_id=SOURCE_IDS[name])


async def _local(fn: Callable[[float, float], L], lat: float, lon: float) -> L:
    return fn(lat, lon)  # in-memory data, well under a millisecond


async def build_profile(
    client: httpx.AsyncClient, cache: Cache, lat: float, lon: float, address: str | None
) -> Profile:
    flood_l, noise_l, air_l, waste_l, mobility_l, green_l = await asyncio.gather(
        _layer("flood", lambda: flood.flood_at(client, cache, lat, lon)),
        _layer("noise", lambda: noise.noise_at(client, cache, lat, lon)),
        _layer("air", lambda: air.air_at(client, cache, lat, lon)),
        _layer("waste", lambda: _local(waste.waste_at, lat, lon)),
        _layer("mobility", lambda: _local(mobility.mobility_at, lat, lon)),
        _layer("green", lambda: _local(green.green_at, lat, lon)),
    )
    layers = Layers(
        flood=flood_l, noise=noise_l, air=air_l, waste=waste_l, mobility=mobility_l, green=green_l
    )
    scores: dict[ekoskor.Layer, float | None] = {
        name: getattr(layer, "score", None)  # UnavailableLayer has no score
        for name, layer in layers  # type: ignore[misc]
    }
    return Profile(
        location=Location(lat=lat, lon=lon, address=address),
        ekoskor=ekoskor.ekoskor(scores),
        layers=layers,
        generated_at=datetime.now(UTC),
    )
