from typing import Annotated

from fastapi import APIRouter, Query

from app.models import GeocodeResponse
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
