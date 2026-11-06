from typing import Annotated

from fastapi import APIRouter, Query

from app.models import GeocodeResponse, ReverseResponse
from app.services import geocode

router = APIRouter(prefix="/api", tags=["geocode"])


@router.get(
    "/geocode",
    response_model=GeocodeResponse,
    summary="Pretraga adresa (autocomplete)",
    description=(
        "Prijedlozi adresa, ulica i naselja u Gradu Zagrebu (pilot područje) iz lokalne "
        "snimke OpenStreetMap podataka (© OpenStreetMap contributors, ODbL). Pretraga ne "
        "razlikuje dijakritičke znakove; broj na kraju upita traži kućni broj."
    ),
)
def search_addresses(
    q: Annotated[str, Query(min_length=3, max_length=100, description="Upisani tekst")],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> GeocodeResponse:
    return GeocodeResponse(results=geocode.search(q, limit), source_id=geocode.SOURCE_ID)


@router.get(
    "/reverse",
    response_model=ReverseResponse,
    summary="Najbliža adresa točki na karti",
    description=(
        "Najbliža adresa iz lokalne snimke OpenStreetMap podataka (© OpenStreetMap "
        "contributors, ODbL) zračnom linijom, ako je unutar 150 m; inače `result` je null. "
        "Točka se ne sprema."
    ),
)
def nearest_address(
    lat: Annotated[float, Query(ge=-90, le=90, description="Geografska širina, EPSG:4326")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Geografska dužina, EPSG:4326")],
) -> ReverseResponse:
    return ReverseResponse(result=geocode.nearest(lat, lon), source_id=geocode.SOURCE_ID)
