from typing import Annotated

import httpx2 as httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.cache import Cache
from app.deps import get_cache, get_http_client
from app.models import Comparison
from app.services.compare import compare
from app.services.geo import in_pilot_area

router = APIRouter(prefix="/api", tags=["compare"])

Lat = Annotated[float, Query(ge=-90, le=90, description="Geografska širina (EPSG:4326)")]
Lon = Annotated[float, Query(ge=-180, le=180, description="Geografska dužina (EPSG:4326)")]
Label = Annotated[str | None, Query(max_length=200, description="Oznaka adrese (ne sprema se)")]


@router.get(
    "/compare",
    response_model=Comparison,
    summary="Usporedba dviju lokacija",
    description=(
        "Dva okolišna profila (kao `/api/profile`) i razlike po slojevima: `better` kaže koja "
        "adresa ima bolju ocjenu sloja (0–100), `ekoskor_diff` je EkoSkor B minus EkoSkor A."
    ),
    responses={422: {"description": "Točka A ili B je izvan pilot područja (Grad Zagreb)"}},
)
async def get_compare(
    a_lat: Lat,
    a_lon: Lon,
    b_lat: Lat,
    b_lon: Lon,
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    cache: Annotated[Cache, Depends(get_cache)],
    a_address: Label = None,
    b_address: Label = None,
) -> Comparison:
    for name, lat, lon in (("a", a_lat, a_lon), ("b", b_lat, b_lon)):
        if not in_pilot_area(lat, lon):
            raise HTTPException(status_code=422, detail=f"outside_pilot_area:{name}")
    return await compare(client, cache, (a_lat, a_lon, a_address), (b_lat, b_lon, b_address))
