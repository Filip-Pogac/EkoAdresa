"""Unit tests for app.cache."""

from pathlib import Path

import pytest

from app.cache import Cache, cached_fetch

NS = "hv-poplave:mala"
LAT, LON = 45.7905, 15.9950


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class Fetcher:
    """Async fetch stub: returns queued values or raises queued exceptions, counts calls."""

    def __init__(self, *results: object) -> None:
        self.results = list(results)
        self.calls = 0

    async def __call__(self) -> object:
        self.calls += 1
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class Clock:
    def __init__(self, t: float = 1_000_000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    return Cache(tmp_path / "test.sqlite")


@pytest.mark.anyio
async def test_miss_fetches_then_hit_does_not(cache: Cache) -> None:
    fetch, clock = Fetcher("#73B2FF"), Clock()
    first = await cached_fetch(cache, NS, LAT, LON, fetch, now=clock)
    clock.t += 60
    second = await cached_fetch(cache, NS, LAT, LON, fetch, now=clock)
    assert first.value == second.value == "#73B2FF"
    assert fetch.calls == 1
    assert second.fetched_at == first.fetched_at
    assert not second.stale


@pytest.mark.anyio
async def test_none_is_cached_not_a_miss(cache: Cache) -> None:
    fetch = Fetcher(None)
    await cached_fetch(cache, NS, LAT, LON, fetch)
    assert (await cached_fetch(cache, NS, LAT, LON, fetch)).value is None
    assert fetch.calls == 1


@pytest.mark.anyio
async def test_key_rounds_to_4_decimals(cache: Cache) -> None:
    fetch = Fetcher([{"razina": 70}])
    await cached_fetch(cache, NS, 45.79052, 15.99498, fetch)
    hit = await cached_fetch(cache, NS, 45.79049, 15.99503, fetch)  # same 4-decimal cell
    assert hit.value == [{"razina": 70}]
    assert fetch.calls == 1


@pytest.mark.anyio
async def test_namespaces_and_cells_are_separate(cache: Cache) -> None:
    fetch = Fetcher("a", "b", "c")
    await cached_fetch(cache, NS, LAT, LON, fetch)
    await cached_fetch(cache, "other", LAT, LON, fetch)
    await cached_fetch(cache, NS, LAT + 0.001, LON, fetch)
    assert fetch.calls == 3


@pytest.mark.anyio
async def test_expired_entry_is_refetched(cache: Cache) -> None:
    fetch, clock = Fetcher("old", "new"), Clock()
    await cached_fetch(cache, NS, LAT, LON, fetch, ttl_s=100, now=clock)
    clock.t += 101
    result = await cached_fetch(cache, NS, LAT, LON, fetch, ttl_s=100, now=clock)
    assert result.value == "new"
    assert not result.stale


@pytest.mark.anyio
async def test_failure_serves_stale_entry(cache: Cache) -> None:
    fetch, clock = Fetcher("#73B2FF", RuntimeError("502")), Clock()
    first = await cached_fetch(cache, NS, LAT, LON, fetch, ttl_s=100, now=clock)
    clock.t += 101
    result = await cached_fetch(cache, NS, LAT, LON, fetch, ttl_s=100, now=clock)
    assert result.value == "#73B2FF"
    assert result.stale
    assert result.fetched_at == first.fetched_at


@pytest.mark.anyio
async def test_failure_without_entry_raises(cache: Cache) -> None:
    with pytest.raises(RuntimeError, match="502"):
        await cached_fetch(cache, NS, LAT, LON, Fetcher(RuntimeError("502")))


@pytest.mark.anyio
async def test_failure_is_not_cached(cache: Cache) -> None:
    fetch = Fetcher(RuntimeError("502"), "#73B2FF")
    with pytest.raises(RuntimeError):
        await cached_fetch(cache, NS, LAT, LON, fetch)
    assert (await cached_fetch(cache, NS, LAT, LON, fetch)).value == "#73B2FF"


def test_persists_across_instances(tmp_path: Path) -> None:
    Cache(tmp_path / "c.sqlite").set(NS, LAT, LON, {"a": 1}, 123.0)
    assert Cache(tmp_path / "c.sqlite").get(NS, LAT, LON) == ({"a": 1}, 123.0)
