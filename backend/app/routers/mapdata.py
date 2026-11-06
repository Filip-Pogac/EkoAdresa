import json
from typing import Annotated

import httpx2 as httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Response

from app.cache import Cache
from app.deps import get_cache, get_http_client
from app.services import tiles, wms
from app.services.map_layers import (
    SHAPE_FILES,
    MapLayer,
    heatmap_bytes,
    point_layer,
    shape_layer_bytes,
)

router = APIRouter(prefix="/api", tags=["map"])


@router.get(
    "/layers/{name}",
    summary="Sloj za kartu (GeoJSON)",
    description=(
        "Mjerne postaje kvalitete zraka, reciklažna dvorišta, zeleni otoci, stajališta ZET-a, "
        "biciklističke staze ili parkovi i šume iz spremljenih snimki podataka, kao GeoJSON "
        "FeatureCollection (EPSG:4326). Svaki objekt ima `source_id`."
    ),
    responses={200: {"content": {"application/json": {}}}},
    response_class=Response,
)
def get_map_layer(name: MapLayer) -> Response:
    headers = {"Cache-Control": "public, max-age=86400"}
    if name in SHAPE_FILES:
        return Response(shape_layer_bytes(name), media_type="application/json", headers=headers)  # type: ignore[arg-type]
    return Response(  # point layers: small, built once per process
        json.dumps(point_layer(name), ensure_ascii=False, separators=(",", ":")),  # type: ignore[arg-type]
        media_type="application/json",
        headers=headers,
    )


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


@router.get(
    "/heatmap",
    summary="EkoSkor za cijeli Grad Zagreb (mreža 250 × 250 m)",
    description=(
        "GeoJSON FeatureCollection (EPSG:4326): po jedna ćelija 250 × 250 m s EkoSkorom i "
        "ocjenama šest slojeva u središtu ćelije. Izračunato skriptom `scripts/build_heatmap.py`; "
        "metodologija u docs/ekoskor.md."
    ),
    responses={200: {"content": {"application/geo+json": {}}}},
    response_class=Response,
)
def get_heatmap() -> Response:
    return Response(
        heatmap_bytes(),
        media_type="application/geo+json",
        headers={"Cache-Control": "public, max-age=86400"},
    )
