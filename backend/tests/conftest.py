"""Shared fixtures."""

from collections.abc import Callable, Iterator
from pathlib import Path

import httpx2 as httpx
import pytest

from app.cache import Cache
from app.deps import get_cache, get_http_client
from app.main import app
from app.services import wms

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def use(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[Handler], None]]:
    """use(handler): route the API's outgoing requests to `handler`, with a fresh cache."""
    monkeypatch.setattr(wms, "RETRY_DELAY_S", 0)
    cache = Cache(tmp_path / "remote.sqlite")
    app.dependency_overrides[get_cache] = lambda: cache

    def install(handler: Handler) -> None:
        app.dependency_overrides[get_http_client] = lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )

    yield install
    app.dependency_overrides.clear()
