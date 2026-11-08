from typing import Annotated

import httpx2 as httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.cache import Cache
from app.deps import get_cache, get_http_client
from app.models import Profile
from app.services.geo import in_pilot_area
from app.services.profile import LAYER_TIMEOUT_S, build_profile

router = APIRouter(prefix="/api", tags=["profile"])


@router.get(
    "/profile",
    response_model=Profile,
    summary="Okolišni profil lokacije",
    description=(
        "Poplave, buka, zrak, otpad i zelena mobilnost za točku u Gradu Zagrebu, te EkoSkor "
        f"0–100. Slojevi se računaju paralelno; sloj koji ne odgovori u {LAYER_TIMEOUT_S:g} s "
        "vraća se sa `status: unavailable`, a ostali slojevi i dalje stižu. Koordinate su "
        "EPSG:4326. Metodologija: docs/ekoskor.md."
    ),
    responses={422: {"description": "Točka je izvan pilot područja (Grad Zagreb)"}},
)
async def get_profile(
    lat: Annotated[float, Query(ge=-90, le=90, description="Geografska širina (EPSG:4326)")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Geografska dužina (EPSG:4326)")],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    cache: Annotated[Cache, Depends(get_cache)],
    address: Annotated[
        str | None, Query(max_length=200, description="Oznaka adrese za prikaz (ne sprema se)")
    ] = None,
) -> Profile:
    if not in_pilot_area(lat, lon):
        raise HTTPException(status_code=422, detail="outside_pilot_area")
    return await build_profile(client, cache, lat, lon, address)
