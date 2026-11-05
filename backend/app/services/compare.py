"""Two profiles side by side, with the per-layer differences the compare view highlights."""

import asyncio
from typing import get_args

import httpx2 as httpx

from app.cache import Cache
from app.models import Comparison, LayerDiff, LayerName, Profile
from app.services.profile import build_profile

Point = tuple[float, float, str | None]  # lat, lon (EPSG:4326), address label


def _diff(a: Profile, b: Profile, name: LayerName) -> LayerDiff:
    score_a = getattr(getattr(a.layers, name), "score", None)  # UnavailableLayer: no score
    score_b = getattr(getattr(b.layers, name), "score", None)
    better = None
    if score_a is not None and score_b is not None and score_a != score_b:
        better = "a" if score_a > score_b else "b"
    return LayerDiff(score_a=score_a, score_b=score_b, better=better)


async def compare(client: httpx.AsyncClient, cache: Cache, a: Point, b: Point) -> Comparison:
    pa, pb = await asyncio.gather(
        build_profile(client, cache, *a), build_profile(client, cache, *b)
    )
    return Comparison(
        a=pa,
        b=pb,
        ekoskor_diff=None if pa.ekoskor is None or pb.ekoskor is None else pb.ekoskor - pa.ekoskor,
        layers={name: _diff(pa, pb, name) for name in get_args(LayerName)},
    )
