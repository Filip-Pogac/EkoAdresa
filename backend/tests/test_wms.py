"""Unit tests for app.services.wms, offline (httpx2.MockTransport)."""

import io
from collections.abc import Coroutine
from typing import Any

import httpx2 as httpx
import pytest
from PIL import Image

from app.services import wms

URL = "https://example.test/wms"
LAT, LON = 45.7905, 15.9950  # Savica


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(wms, "RETRY_DELAY_S", 0)


def png(centre_rgba: tuple[int, int, int, int], px: int = 101) -> bytes:
    image = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    image.putpixel((px // 2, px // 2), centre_rgba)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def client_with(responses: list[httpx.Response], seen: list[httpx.Request]) -> httpx.AsyncClient:
    queue = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return next(queue)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def map_pixel(c: httpx.AsyncClient) -> Coroutine[Any, Any, str | None]:
    return wms.get_map_pixel(c, URL, "flood-layer", LAT, LON)


@pytest.mark.anyio
async def test_get_feature_info_params_and_features() -> None:
    features = [{"id": "SKB_R4_Cestovni_promet_Lden.1", "properties": {"razina": 70}}]
    seen: list[httpx.Request] = []
    async with client_with(
        [httpx.Response(200, json={"type": "FeatureCollection", "features": features})], seen
    ) as c:
        result = await wms.get_feature_info(c, URL, ["a", "b"], LAT, LON)

    assert result == features
    q = seen[0].url.params
    assert q["REQUEST"] == "GetFeatureInfo"
    assert q["CRS"] == "CRS:84"
    assert q["BUFFER"] == "0"
    assert q["LAYERS"] == q["QUERY_LAYERS"] == "a,b"
    min_lon, min_lat, max_lon, max_lat = map(float, q["BBOX"].split(","))
    assert min_lon < LON < max_lon and min_lat < LAT < max_lat  # lon/lat axis order


@pytest.mark.anyio
async def test_get_feature_info_empty() -> None:
    async with client_with([httpx.Response(200, json={"features": []})], []) as c:
        assert await wms.get_feature_info(c, URL, ["a"], LAT, LON) == []


@pytest.mark.anyio
async def test_map_pixel_opaque_and_transparent() -> None:
    async with client_with([httpx.Response(200, content=png((115, 178, 255, 255)))], []) as c:
        assert await map_pixel(c) == "#73B2FF"
    async with client_with([httpx.Response(200, content=png((0, 0, 0, 0)))], []) as c:
        assert await map_pixel(c) is None


@pytest.mark.anyio
async def test_map_pixel_box_is_about_707_m() -> None:
    seen: list[httpx.Request] = []
    async with client_with([httpx.Response(200, content=png((0, 0, 0, 0)))], seen) as c:
        await map_pixel(c)
    q = seen[0].url.params
    min_lon, min_lat, max_lon, max_lat = map(float, q["BBOX"].split(","))
    assert (max_lat - min_lat) * wms.M_PER_DEG_LAT == pytest.approx(707, abs=1)
    assert q["WIDTH"] == q["HEIGHT"] == "101"


@pytest.mark.anyio
async def test_retries_502_then_succeeds() -> None:
    seen: list[httpx.Request] = []
    responses = [
        httpx.Response(502),
        httpx.Response(502),
        httpx.Response(200, content=png((1, 2, 3, 255))),
    ]
    async with client_with(responses, seen) as c:
        assert await map_pixel(c) == "#010203"
    assert len(seen) == 3


@pytest.mark.anyio
async def test_retries_truncated_png() -> None:
    good = png((1, 2, 3, 255))
    seen: list[httpx.Request] = []
    responses = [
        httpx.Response(200, content=good[: len(good) // 2]),
        httpx.Response(200, content=good),
    ]
    async with client_with(responses, seen) as c:
        assert await map_pixel(c) == "#010203"
    assert len(seen) == 2


@pytest.mark.anyio
async def test_service_exception_is_not_retried() -> None:
    body = (
        b"<ServiceExceptionReport>"
        b'<ServiceException code="LayerNotQueryable"/>'
        b"</ServiceExceptionReport>"
    )
    seen: list[httpx.Request] = []
    async with client_with([httpx.Response(200, content=body)], seen) as c:
        with pytest.raises(wms.WMSError, match="LayerNotQueryable"):
            await wms.get_feature_info(c, URL, ["a"], LAT, LON)
    assert len(seen) == 1


@pytest.mark.anyio
async def test_gives_up_after_max_attempts() -> None:
    seen: list[httpx.Request] = []
    async with client_with([httpx.Response(502)] * wms.MAX_ATTEMPTS, seen) as c:
        with pytest.raises(wms.WMSError):
            await map_pixel(c)
    assert len(seen) == wms.MAX_ATTEMPTS
