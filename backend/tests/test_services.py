"""Reference-point tests (CLAUDE.md §2.6): the three Phase 0 points, replayed offline.

Fixtures in tests/fixtures/wms/ are real responses recorded by tests/record_fixtures.py.
The mock transport serves the fixture for the point at the centre of the requested BBOX,
so a wrong coordinate or axis order fails the test instead of silently reading another
point. Expected values are the Phase 0 results in docs/data-sources.md.

Checks both the raw WMS answers (pixel colour, noise bands) and their interpretation
(flood zone, loudest Lden) in flood.py / noise.py.
"""

import math
from collections.abc import Callable
from pathlib import Path

import httpx2 as httpx
import pytest

from app.cache import Cache
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
    """Reference point name; '<name>_ring' for a façade ring point around it (noise.ring)."""
    min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    lat, lon = (min_lat + max_lat) / 2, (min_lon + max_lon) / 2
    for name, (p_lat, p_lon) in POINTS.items():
        if abs(lat - p_lat) < 1e-6 and abs(lon - p_lon) < 1e-6:
            return name
        if abs(lat - p_lat) < 0.0005 and abs(lon - p_lon) < 0.0005:  # within ~40 m
            return f"{name}_ring"
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


# --- flood_at / noise_at: the layer objects the address card shows ---------------------

EXPECTED_FLOOD_LAYER = {  # (zone, depth_class, status, score)
    "savica": ("low", "dubina 1,5–2,5 m", "yellow", 50),
    "jelacic": ("none", None, "green", 100),
    "sljeme": ("none", None, "green", 100),
}
EXPECTED_NOISE_LAYER = {  # (lden min, max, lnight min, max, loudest source, status, score)
    "savica": (70, 74, 60, 64, "road", "red", 0),
    "jelacic": (70, 74, 60, 64, "tram", "red", 0),
    "sljeme": (None, 49, None, 49, None, "green", 100),  # no band, rings empty: < 50 dB
}


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    return Cache(tmp_path / "remote.sqlite")


@pytest.mark.anyio
@pytest.mark.parametrize("point", POINTS)
async def test_flood_layer(client: httpx.AsyncClient, cache: Cache, point: str) -> None:
    layer = await flood.flood_at(client, cache, *POINTS[point])
    assert (layer.zone, layer.depth_class, layer.status, layer.score) == EXPECTED_FLOOD_LAYER[point]
    assert layer.source_id == "hv-poplave"
    assert not layer.stale


@pytest.mark.anyio
@pytest.mark.parametrize("point", POINTS)
async def test_noise_layer(client: httpx.AsyncClient, cache: Cache, point: str) -> None:
    layer = await noise.noise_at(client, cache, *POINTS[point])
    got = (
        layer.lden_db_min,
        layer.lden_db_max,
        layer.lnight_db_min,
        layer.lnight_db_max,
        layer.loudest_source,
        layer.status,
        layer.score,
    )
    assert got == EXPECTED_NOISE_LAYER[point]
    assert layer.facade_m is None  # savica, jelacic: band at the point; sljeme: none found
    assert layer.source_id == "zg-buka"


def bands_where(band_at: Callable[[float, float], dict[str, int]]) -> Callable:
    """Fake zg-buka GetFeatureInfo: features from band_at(lat, lon) at the bbox centre."""

    def handler(request: httpx.Request) -> httpx.Response:
        min_lon, min_lat, max_lon, max_lat = map(float, request.url.params["BBOX"].split(","))
        bands = band_at((min_lat + max_lat) / 2, (min_lon + max_lon) / 2)
        features = [{"id": f"SKB_R4_{k}.fid-1", "properties": {"razina": db}}
                    for k, db in bands.items()]  # fmt: skip
        return httpx.Response(200, json={"type": "FeatureCollection", "features": features})

    return handler


ADDRESS = (45.8134, 15.9773)  # inside a building; the street is to the south


def south_street(distance_m: float) -> Callable[[float, float], dict[str, int]]:
    """Tram 70 dB Lden / 60 dB Lnight, road 55 dB, at points >= distance_m south."""

    def band_at(lat: float, lon: float) -> dict[str, int]:
        if (ADDRESS[0] - lat) * noise.M_PER_DEG_LAT >= distance_m - 0.5:
            return {"Tramvajski_promet_Lden": 70, "Tramvajski_promet_Lnight": 60,
                    "Cestovni_promet_Lden": 55}  # fmt: skip
        return {}

    return band_at


@pytest.mark.anyio
@pytest.mark.parametrize(("street_m", "facade_m"), [(15, 15), (30, 30)])
async def test_point_in_building_uses_most_exposed_facade(
    cache: Cache, street_m: int, facade_m: int
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(bands_where(south_street(street_m)))
    ) as c:
        layer = await noise.noise_at(c, cache, *ADDRESS)
    assert layer.facade_m == facade_m
    assert (layer.lden_db_min, layer.lnight_db_min, layer.loudest_source) == (70, 60, "tram")
    assert (layer.status, layer.score) == ("red", 0)


@pytest.mark.anyio
async def test_quiet_building_beyond_the_rings_stays_quiet(cache: Cache) -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(bands_where(south_street(60)))) as c:
        layer = await noise.noise_at(c, cache, *ADDRESS)
    assert (layer.facade_m, layer.lden_db_max, layer.status) == (None, 49, "green")


def test_ring_radius_in_metres() -> None:
    from app.services.geo import to_htrs

    x0, y0 = to_htrs.transform(ADDRESS[1], ADDRESS[0])
    for lat, lon in noise.ring(*ADDRESS, 15):
        x, y = to_htrs.transform(lon, lat)
        assert abs(math.hypot(x - x0, y - y0) - 15) < 0.2  # EPSG:3765 metres


def down(request: httpx.Request) -> httpx.Response:
    return httpx.Response(502)


@pytest.mark.anyio
async def test_service_down_serves_last_cached_answer(
    client: httpx.AsyncClient, cache: Cache, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wms, "RETRY_DELAY_S", 0)
    lat, lon = POINTS["savica"]
    await flood.flood_at(client, cache, lat, lon)
    # Age the cached answers past the TTL, then take the service down
    for zone in flood.SCENARIOS:
        namespace = f"{flood.SOURCE_ID}:{flood.layer_name(zone)}"
        value, _ = cache.get(namespace, lat, lon)  # type: ignore[misc]
        cache.set(namespace, lat, lon, value, fetched_at=0.0)  # 1970: long expired
    async with httpx.AsyncClient(transport=httpx.MockTransport(down)) as broken:
        layer = await flood.flood_at(broken, cache, lat, lon)
    assert layer.stale
    assert layer.zone == "low"
    assert layer.fetched_at.year == 1970  # the UI shows the age of the cached answer


@pytest.mark.anyio
async def test_service_down_without_cache_raises(
    cache: Cache, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wms, "RETRY_DELAY_S", 0)
    async with httpx.AsyncClient(transport=httpx.MockTransport(down)) as broken:
        with pytest.raises(wms.WMSError):
            await noise.noise_at(broken, cache, *POINTS["jelacic"])
