from typing import Annotated

import httpx2 as httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Response

from app.cache import Cache
from app.deps import get_cache, get_http_client
from app.services import tiles, wms
from app.services.map_layers import PointLayer, point_layer

router = APIRouter(prefix="/api", tags=["map"])


@router.get(
    "/layers/{name}",
    summary="Točkasti sloj za kartu (GeoJSON)",
    description=(
        "Mjerne postaje kvalitete zraka, reciklažna dvorišta, zeleni otoci ili stajališta ZET-a "
        "iz spremljenih snimki podataka, kao GeoJSON FeatureCollection (EPSG:4326). Svaka "
        "točka ima `source_id`."
    ),
)
def get_point_layer(name: PointLayer, response: Response) -> dict:
    response.headers["Cache-Control"] = "public, max-age=86400"
    return point_layer(name)


@router.get(
    "/tiles/{layer}/{z}/{x}/{y}.png",
    summary="Kartografska pločica poplava ili buke",
    description=(
        "PNG pločica (XYZ, EPSG:3857) iz WMS-a Hrvatskih voda (poplave, scenarij male "
        "vjerojatnosti) ili strateške karte buke Grada Zagreba (Lden, svi izvori), "
        "spremljena u predmemoriju. Samo za područje Grada Zagreba, zoom 10–18."
    ),
    responses={200: {"content": {"image/png": {}}}, 404: {}, 502: {}},
    response_class=Response,
)
async def get_tile(
    layer: Annotated[str, Path(pattern="^(flood|noise)$")],
    z: int,
    x: int,
    y: int,
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    cache: Annotated[Cache, Depends(get_cache)],
) -> Response:
    try:
        png = await tiles.get_tile(client, cache.path.parent, layer, z, x, y)
    except tiles.TileOutOfRange as exc:
        raise HTTPException(status_code=404, detail="tile_out_of_range") from exc
    except wms.WMSError as exc:
        raise HTTPException(status_code=502, detail="tile_service_unavailable") from exc
    return Response(png, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})
