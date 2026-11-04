"""Reference-point tests (CLAUDE.md §2.6): the three Phase 0 points, replayed offline.

Fixtures in tests/fixtures/wms/ are real responses recorded by tests/record_fixtures.py.
The mock transport serves the fixture for the point at the centre of the requested BBOX,
so a wrong coordinate or axis order fails the test instead of silently reading another
point. Expected values are the Phase 0 results in docs/data-sources.md.

Phase 2 checks the raw WMS answers (pixel colour, noise bands). Phase 3 adds the
interpretation (flood zone, dB values, status) in flood.py / noise.py on the same fixtures.
"""

from pathlib import Path

import httpx2 as httpx
import pytest

from app.services import wms
from tests.reference_points import (
    FIXTURES_DIR_NAME,
    FLOOD_SCENARIOS,
    HV_POPLAVE_URL,
    NOISE_LAYERS,
    NOISE_PROPERTIES,
    POINTS,
    ZG_BUKA_URL,
    flood_layer,
)

FIXTURES = Path(__file__).parent / "fixtures" / FIXTURES_DIR_NAME

EXPECTED_FLOOD = {  # scenario -> legend colour at the point, None = outside that zone
    "savica": {"velika": None, "srednja": None, "mala": "#73B2FF"},  # low prob., 1.5-2.5 m
    "jelacic": {"velika": None, "srednja": None, "mala": None},
    "sljeme": {"velika": None, "srednja": None, "mala": None},
}
EXPECTED_NOISE = {  # layer -> razina (lower bound of the 5 dB band)
    "savica": {"Cestovni_promet_Lden": 70, "Cestovni_promet_Lnight": 60},
    "jelacic": {
        "Cestovni_promet_Lden": 50,
        "Tramvajski_promet_Lden": 70,
        "Tramvajski_promet_Lnight": 60,
    },
    "sljeme": {},
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def point_at_bbox_centre(bbox: str) -> str:
    min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    lat, lon = (min_lat + max_lat) / 2, (min_lon + max_lon) / 2
    for name, (p_lat, p_lon) in POINTS.items():
        if abs(lat - p_lat) < 1e-6 and abs(lon - p_lon) < 1e-6:
            return name
    raise AssertionError(f"request for an unknown point {lat}, {lon}")


def replay(request: httpx.Request) -> httpx.Response:
    q = request.url.params
    point = point_at_bbox_centre(q["BBOX"])
    if q["REQUEST"] == "GetMap":
        assert str(request.url).startswith(HV_POPLAVE_URL)
        scenario = q["LAYERS"].split("-")[-2]  # hr.fd.opasnost-od-poplave-<scenario>-vjerojatnost
        body = (FIXTURES / f"flood_{point}_{scenario}.png").read_bytes()
        return httpx.Response(200, content=body, headers={"content-type": "image/png"})
    if q["REQUEST"] == "GetFeatureInfo":
        assert str(request.url).startswith(ZG_BUKA_URL)
        body = (FIXTURES / f"noise_{point}.json").read_bytes()
        return httpx.Response(200, content=body, headers={"content-type": "application/json"})
    raise AssertionError(f"unexpected request {request.url}")


@pytest.fixture
async def client():  # noqa: ANN201
    async with httpx.AsyncClient(transport=httpx.MockTransport(replay)) as c:
        yield c


@pytest.mark.anyio
@pytest.mark.parametrize("point", POINTS)
async def test_flood_pixel_at_reference_point(client: httpx.AsyncClient, point: str) -> None:
    lat, lon = POINTS[point]
    result = {
        s: await wms.get_map_pixel(client, HV_POPLAVE_URL, flood_layer(s), lat, lon)
        for s in FLOOD_SCENARIOS
    }
    assert result == EXPECTED_FLOOD[point]


@pytest.mark.anyio
@pytest.mark.parametrize("point", POINTS)
async def test_noise_bands_at_reference_point(client: httpx.AsyncClient, point: str) -> None:
    lat, lon = POINTS[point]
    features = await wms.get_feature_info(
        client, ZG_BUKA_URL, NOISE_LAYERS, lat, lon, property_names=NOISE_PROPERTIES
    )
    result = {
        f["id"].split(".")[0].removeprefix("SKB_R4_"): f["properties"]["razina"] for f in features
    }
    assert result == EXPECTED_NOISE[point]
