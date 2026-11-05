from fastapi import APIRouter

from app.models import Source
from app.sources import SOURCES

router = APIRouter(prefix="/api", tags=["sources"])


@router.get(
    "/sources",
    response_model=list[Source],
    summary="Izvori podataka",
    description=(
        "Svi skupovi podataka i servisi koje EkoAdresa koristi: izdavač, poveznice, licencija "
        "kako je navedena (`null` = licencija nije navedena) i datum podataka. Svaki "
        "`source_id` u odgovorima API-ja nalazi se na ovom popisu."
    ),
)
def list_sources() -> list[Source]:
    return list(SOURCES.values())
