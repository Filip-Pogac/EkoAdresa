"""Air layer: committed City station data + the national index WFS (recorded fixture)."""

from datetime import date, timedelta
from pathlib import Path

import httpx2 as httpx
import pytest

from app.cache import Cache
from app.services import air, dhmz
from tests.reference_points import POINTS
from tests.test_dhmz import dhmz_replay

WFS_FIXTURE = Path(__file__).parent / "fixtures" / "wfs" / "rh_zrak_indeks.xml"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    return Cache(tmp_path / "remote.sqlite")


class FakeWfs:
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if str(request.url).startswith(dhmz.URL):
            return dhmz_replay(request)  # DHMZ pages are not WFS calls
        self.calls += 1
        assert str(request.url).startswith(air.LIVE_URL)
        body = WFS_FIXTURE.read_bytes() if self.status == 200 else b""
        return httpx.Response(self.status, content=body)


def client(fake: FakeWfs) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(fake))


# Nearest City station per reference point (same as the heatmap build of 2026-11-05)
@pytest.mark.anyio
@pytest.mark.parametrize(
    ("point", "station"),
    [("savica", "siget"), ("jelacic", "djordjiceva"), ("sljeme", "ksaverska")],
)
async def test_nearest_station(cache: Cache, point: str, station: str) -> None:
    async with client(FakeWfs()) as c:
        layer = await air.air_at(c, cache, *POINTS[point])
    assert layer.station.id == station
    assert layer.station.source_id == "zg-zrak-postaje"
    assert 0 < layer.station.distance_m < 8000


@pytest.mark.anyio
async def test_score_from_2023_pm10_mean(cache: Cache) -> None:
    async with client(FakeWfs()) as c:
        layer = await air.air_at(c, cache, *POINTS["jelacic"])  # Đorđićeva, PM10 mean 20.9
    assert layer.source_id == "zg-zrak-mjerenja"
    assert layer.pm10_mean_ug_m3 == pytest.approx(20.9, abs=0.05)
    assert layer.score == 77  # 100 * (40 - 20.858) / 25 = 76.57
    assert layer.status == "green"
    assert (layer.period_from, layer.period_to) == (date(2023, 1, 1), date(2023, 8, 31))


@pytest.mark.anyio
async def test_latest_and_30_day_history(cache: Cache) -> None:
    async with client(FakeWfs()) as c:
        layer = await air.air_at(c, cache, *POINTS["jelacic"])
    assert {v.pollutant for v in layer.latest} == {"no2", "o3", "pm10"}  # Đorđićeva measures
    # each pollutant's own last day with data: PM10 is missing on 28-31 August
    assert {v.pollutant: v.date for v in layer.latest} == {
        "no2": date(2023, 8, 31),
        "o3": date(2023, 8, 31),
        "pm10": date(2023, 8, 27),
    }
    dates = {v.date for v in layer.history}
    assert min(dates) == date(2023, 8, 31) - timedelta(days=29)
    assert max(dates) == date(2023, 8, 31)


@pytest.mark.anyio
async def test_live_index_from_nearest_national_station(cache: Cache) -> None:
    async with client(FakeWfs()) as c:
        layer = await air.air_at(c, cache, *POINTS["jelacic"])
    live = layer.live_index
    assert live is not None
    assert live.value == 1.0  # EnvHealthDeterminantMeasure.155, ~1.4 km south of the square
    assert live.measured_at.isoformat() == "2026-11-05T07:00:00+00:00"
    assert 1000 < live.distance_m < 2000
    assert live.scale_verified is False
    assert live.source_id == "rh-zrak-indeks"


@pytest.mark.anyio
async def test_live_index_cached_for_all_addresses(cache: Cache) -> None:
    fake = FakeWfs()
    async with client(fake) as c:
        await air.air_at(c, cache, *POINTS["jelacic"])
        await air.air_at(c, cache, *POINTS["savica"])
    assert fake.calls == 1


@pytest.mark.anyio
async def test_live_index_failure_does_not_fail_the_layer(cache: Cache) -> None:
    async with client(FakeWfs(status=502)) as c:
        layer = await air.air_at(c, cache, *POINTS["savica"])
    assert layer.live_index is None
    assert layer.status in ("green", "yellow", "red")


@pytest.mark.anyio
async def test_dhmz_reading_is_extra_and_unscored(cache: Cache) -> None:
    async with client(FakeWfs()) as c:
        layer = await air.air_at(c, cache, *POINTS["jelacic"])
    assert layer.dhmz is not None and layer.dhmz.station.name == "Zagreb 1"
    async with client(FakeWfs()) as c:
        without = await air.air_at(
            c, Cache(cache.path.with_name("other.sqlite")), *POINTS["jelacic"]
        )
    assert layer.score == without.score  # the score comes from the 2023 City data only
