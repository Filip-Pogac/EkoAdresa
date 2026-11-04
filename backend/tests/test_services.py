"""Reference-point tests (CLAUDE.md §2.6): the three Phase 0 points, replayed offline.

Fixtures in tests/fixtures/wms/ are real responses recorded by tests/record_fixtures.py.
The mock transport serves the fixture for the point at the centre of the requested BBOX,
so a wrong coordinate or axis order fails the test instead of silently reading another
point. Expected values are the Phase 0 results in docs/data-sources.md.

Checks both the raw WMS answers (pixel colour, noise bands) and their interpretation
(flood zone, loudest Lden) in flood.py / noise.py.
"""

from pathlib import Path

import httpx2 as httpx
import pytest

from app.services import flood, noise, wms
from tests.reference_points import FIXTURES_DIR_NAME, POINTS

FIXTURES = Path(__file__).parent / "fixtures" / FIXTURES_DIR_NAME

EXPECTED_FLOOD = {  # zone -> legend colour at the point, None = outside that zone
    "savica": {"high": None, "medium": None, "low": "#73B2FF"},  # 1.5-2.5 m depth class
    "jelacic": {"high": None, "medium": None, "low": None},
    "sljeme": {"high": None, "medium": None, "low": None},
}
EXPECTED_ZONE = {"savica": "low", "jelacic": "none", "sljeme": "none"}
EXPECTED_NOISE = {  # layer -> razina (lower bound of the 5 dB band)
    "savica": {"Cestovni_promet_Lden": 70, "Cestovni_promet_Lnight": 60},
    "jelacic": {
        "Cestovni_promet_Lden": 50,
        "Tramvajski_promet_Lden": 70,
        "Tramvajski_promet_Lnight": 60,
    },
    "sljeme": {},
}
EXPECTED_LOUDEST_LDEN = {"savica": 70, "jelacic": 70, "sljeme": None}  # jelacic: tram


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
        assert str(request.url).startswith(flood.HV_POPLAVE_URL)
        scenario = q["LAYERS"].split("-")[-2]  # hr.fd.opasnost-od-poplave-<scenario>-vjerojatnost
        body = (FIXTURES / f"flood_{point}_{scenario}.png").read_bytes()
        return httpx.Response(200, content=body, headers={"content-type": "image/png"})
    if q["REQUEST"] == "GetFeatureInfo":
        assert str(request.url).startswith(noise.ZG_BUKA_URL)
        body = (FIXTURES / f"noise_{point}.json").read_bytes()
        return httpx.Response(200, content=body, headers={"content-type": "application/json"})
    raise AssertionError(f"unexpected request {request.url}")


@pytest.fixture
async def client():  # noqa: ANN201
    async with httpx.AsyncClient(transport=httpx.MockTransport(replay)) as c:
        yield c


@pytest.mark.anyio
@pytest.mark.parametrize("point", POINTS)
async def test_flood_at_reference_point(client: httpx.AsyncClient, point: str) -> None:
    lat, lon = POINTS[point]
    colours = {
        zone: await wms.get_map_pixel(
            client, flood.HV_POPLAVE_URL, flood.layer_name(zone), lat, lon
        )
        for zone in flood.SCENARIOS
    }
    assert colours == EXPECTED_FLOOD[point]
    assert flood.zone_from_colours(colours) == EXPECTED_ZONE[point]


@pytest.mark.anyio
@pytest.mark.parametrize("point", POINTS)
async def test_noise_at_reference_point(client: httpx.AsyncClient, point: str) -> None:
    lat, lon = POINTS[point]
    features = await wms.get_feature_info(
        client, noise.ZG_BUKA_URL, noise.LAYERS, lat, lon, property_names=noise.PROPERTY_NAMES
    )
    bands = noise.bands_from_features(features)
    assert bands == EXPECTED_NOISE[point]
    assert noise.loudest(bands) == EXPECTED_LOUDEST_LDEN[point]
