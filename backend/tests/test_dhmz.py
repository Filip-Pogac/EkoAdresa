"""DHMZ state stations: last 24 h of raw values, on recorded pages (fixtures/dhmz/)."""

import asyncio
from collections.abc import Callable
from pathlib import Path

import httpx2 as httpx
import pytest

from app.cache import Cache
from app.models import DhmzValue
from app.services import dhmz
from app.sources import SOURCES
from tests.reference_points import POINTS

FIXTURES = Path(__file__).parent / "fixtures" / "dhmz"
POLLUTANT_BY_ID = {str(id_komp): p for p, (id_komp, _) in dhmz.COMPONENTS.items()}


def dhmz_replay(request: httpx.Request) -> httpx.Response:
    """Serve the recorded Zagreb 1 pages (recorded 2026-11-06) for any station."""
    assert str(request.url).startswith(dhmz.URL)
    pollutant = POLLUTANT_BY_ID[request.url.params["id_komp"]]
    return httpx.Response(200, text=(FIXTURES / f"zagreb_1_{pollutant}.html").read_text("utf-8"))


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    return Cache(tmp_path / "remote.sqlite")


def recording(handler: Callable[[httpx.Request], httpx.Response], log: list) -> httpx.AsyncClient:
    def wrapped(request: httpx.Request) -> httpx.Response:
        log.append(request)
        return handler(request)

    return httpx.AsyncClient(transport=httpx.MockTransport(wrapped))


def test_parse_hourly_chart_rows() -> None:
    rows = dhmz.parse_hourly((FIXTURES / "zagreb_1_pm10.html").read_text("utf-8"))
    assert len(rows) == 24
    # JavaScript months count from 0: new Date(2026,10,05,0) is 5 November
    assert rows[0] == ("2026-11-05T00:00", 31.84)
    assert rows[-1] == ("2026-11-05T23:00", 28.51)


def test_parse_page_without_data() -> None:
    # Zagreb 1 does not measure NO2: the page has no chart rows
    assert dhmz.parse_hourly((FIXTURES / "zagreb_1_no2.html").read_text("utf-8")) == []


@pytest.mark.anyio
async def test_nearest_station_and_values(cache: Cache) -> None:
    log: list[httpx.Request] = []
    async with recording(dhmz_replay, log) as c:
        reading = await dhmz.dhmz_at(c, cache, *POINTS["jelacic"])
    assert reading is not None
    assert reading.station.name == "Zagreb 1"  # ~1.4 km south of Trg bana Jelačića
    assert 1000 < reading.station.distance_m < 2000
    assert reading.validated is False
    assert reading.source_id in SOURCES
    by_pollutant = {v.pollutant: v for v in reading.values}
    assert set(by_pollutant) == {"pm10", "pm2_5"}  # no NO2 page rows
    pm10 = by_pollutant["pm10"]
    assert (pm10.hours, pm10.latest_ug_m3, pm10.latest_at_local) == (24, 28.5, "2026-11-05T23:00")
    assert 0 < pm10.mean_24h_ug_m3 < 100
    # recorded day: PM2.5 mean 27 µg/m³ is above the WHO interim target of 25
    assert by_pollutant["pm2_5"].mean_24h_ug_m3 > 25
    assert reading.status == "red"


def value(pollutant: str, mean: float, hours: int = 24) -> DhmzValue:
    return DhmzValue(
        pollutant=pollutant,  # type: ignore[arg-type]
        mean_24h_ug_m3=mean,
        latest_ug_m3=mean,
        latest_at_local="2026-11-05T23:00",
        hours=hours,
    )


@pytest.mark.parametrize(
    ("pollutant", "mean", "status"),
    [
        ("pm10", 45, "green"),  # WHO 24 h guideline, inclusive
        ("pm10", 45.1, "yellow"),
        ("pm10", 50, "yellow"),  # WHO interim target 4, inclusive
        ("pm10", 50.1, "red"),
        ("pm2_5", 15, "green"),
        ("pm2_5", 15.1, "yellow"),
        ("pm2_5", 25, "yellow"),
        ("pm2_5", 25.1, "red"),
        ("no2", 25, "green"),
        ("no2", 25.1, "yellow"),
        ("no2", 50, "yellow"),  # WHO interim target 2
        ("no2", 50.1, "red"),
    ],
)
def test_day_status_thresholds(pollutant: str, mean: float, status: str) -> None:
    assert dhmz.day_status([value(pollutant, mean)]) == status


def test_day_status_worst_pollutant_wins() -> None:
    assert dhmz.day_status([value("pm10", 20), value("pm2_5", 20)]) == "yellow"
    assert dhmz.day_status([value("pm10", 60), value("pm2_5", 5)]) == "red"


def test_day_status_needs_18_hours() -> None:
    # 17 h is not a 24-hour mean: ignored; nothing else left -> unavailable
    assert dhmz.day_status([value("pm10", 80, hours=17)]) == "unavailable"
    assert dhmz.day_status([value("pm10", 80, hours=17), value("pm2_5", 10)]) == "green"
    assert dhmz.day_status([value("pm10", 80, hours=18)]) == "red"


@pytest.mark.anyio
async def test_requests_name_the_station_not_the_user(cache: Cache) -> None:
    log: list[httpx.Request] = []
    async with recording(dhmz_replay, log) as c:
        await dhmz.dhmz_at(c, cache, *POINTS["jelacic"])
    assert len(log) == len(dhmz.COMPONENTS)  # one page per pollutant
    for request in log:
        assert set(request.url.params) == {"section", "post", "id_komp", "komp"}
        assert request.url.params["post"] == "Zagreb 1"


@pytest.mark.anyio
async def test_one_answer_per_station_serves_all_addresses(cache: Cache) -> None:
    log: list[httpx.Request] = []
    async with recording(dhmz_replay, log) as c:
        await dhmz.dhmz_at(c, cache, *POINTS["jelacic"])
        await dhmz.dhmz_at(c, cache, 45.8050, 15.9700)  # also nearest to Zagreb 1
    assert len(log) == len(dhmz.COMPONENTS)


@pytest.mark.anyio
async def test_service_down_returns_none(cache: Cache) -> None:
    async with recording(lambda r: httpx.Response(503), []) as c:
        assert await dhmz.dhmz_at(c, cache, *POINTS["savica"]) is None


@pytest.mark.anyio
async def test_slow_service_returns_none(cache: Cache, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dhmz, "TIMEOUT_S", 0.1)

    async def slow(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(1)
        return dhmz_replay(request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as c:  # type: ignore[arg-type]
        assert await dhmz.dhmz_at(c, cache, *POINTS["savica"]) is None


@pytest.mark.anyio
async def test_expired_answer_is_not_shown_when_service_is_down(cache: Cache) -> None:
    async with recording(dhmz_replay, []) as c:
        assert await dhmz.dhmz_at(c, cache, *POINTS["jelacic"]) is not None
    for pollutant in dhmz.COMPONENTS:  # age the cached pages past the TTL
        key = (f"{dhmz.SOURCE_ID}:{pollutant}", *dhmz.STATIONS["Zagreb 1"])
        hit = cache.get(*key)
        if hit is not None:
            cache.set(*key, hit[0], fetched_at=0.0)
    async with recording(lambda r: httpx.Response(503), []) as c:
        assert await dhmz.dhmz_at(c, cache, *POINTS["jelacic"]) is None
