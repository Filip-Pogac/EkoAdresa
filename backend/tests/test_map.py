"""Map endpoints: point layers from data/ and the cached WMS tile proxy (offline)."""

import io
import os
import time
from collections.abc import Callable
from pathlib import Path

import httpx2 as httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.deps import get_cache, get_http_client
from app.main import app
from app.services import tiles, wms
from app.sources import SOURCES

api = TestClient(app)
# XYZ tiles over Trg bana Jelačića (45.8131 N, 15.9772 E)
JELACIC_Z14 = (14, 8919, 5841)
JELACIC_Z16 = (16, 8919 * 4 + 1, 5841 * 4 + 2)


def png(colour: tuple[int, int, int, int], size: int = 256) -> bytes:
    out = io.BytesIO()
    Image.new("RGBA", (size, size), colour).save(out, format="PNG")
    return out.getvalue()


def quadrant_png() -> bytes:
    """256 px tile: a different colour in each 64 px column, to check the enlarged crop."""
    image = Image.new("RGBA", (256, 256))
    for col in range(4):
        image.paste((col * 60, 0, 0, 255), (col * 64, 0, col * 64 + 64, 256))
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


@pytest.mark.parametrize(
    ("name", "count"),
    [
        ("air_stations", 6),
        ("recycling_yards", 20),
        ("green_islands", 628),
        ("stops", 2148),
        ("bike_paths", 2889),
        ("parks", 3466),  # all sizes on the map; the score uses 1 136 of them
        ("bike_stations", 200),
    ],
)
def test_map_layers(name: str, count: int) -> None:
    resp = api.get(f"/api/layers/{name}")
    assert resp.status_code == 200
    features = resp.json()["features"]
    assert len(features) == count
    assert all(f["properties"]["source_id"] in SOURCES for f in features)


def test_unknown_point_layer() -> None:
    assert api.get("/api/layers/restaurants").status_code == 422


def test_tile_bounds_cover_jelacic() -> None:
    min_x, min_y, max_x, max_y = tiles.tile_bounds(*JELACIC_Z14)
    lon0, lat0 = tiles._lon_lat(min_x, min_y)
    lon1, lat1 = tiles._lon_lat(max_x, max_y)
    assert lon0 < 15.9772 < lon1 and lat0 < 45.8131 < lat1


@pytest.mark.parametrize(
    "tile", [(9, 279, 182), (19, 0, 0), (14, 0, 0), (14, 8919, 99999)]
)  # too far out, too deep, outside Zagreb, index out of range
def test_tiles_outside_range_are_refused(tile: tuple[int, int, int]) -> None:
    with pytest.raises(tiles.TileOutOfRange):
        tiles.check_tile(*tile)


@pytest.fixture
def served(tmp_path: Path) -> Callable[[Callable[[httpx.Request], httpx.Response]], list]:
    """served(handler) -> list of upstream requests; tile cache in tmp_path."""

    class FakeCache:
        path = tmp_path / "remote.sqlite"

    requests: list[httpx.Request] = []

    def install(handler: Callable[[httpx.Request], httpx.Response]) -> list:
        def recording(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return handler(request)

        app.dependency_overrides[get_http_client] = lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(recording)
        )
        return requests

    app.dependency_overrides[get_cache] = lambda: FakeCache()
    yield install
    app.dependency_overrides.clear()


def tile_url(layer: str, tile: tuple[int, int, int]) -> str:
    z, x, y = tile
    return f"/api/tiles/{layer}/{z}/{x}/{y}.png"


def test_noise_tile_is_fetched_once_then_cached(served: Callable) -> None:
    requests = served(lambda r: httpx.Response(200, content=png((205, 70, 62, 255))))
    for _ in range(2):
        resp = api.get(tile_url("noise", JELACIC_Z14))
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
    assert len(requests) == 1
    q = requests[0].url.params
    assert q["CRS"] == "EPSG:3857" and q["WIDTH"] == "256"
    assert q["LAYERS"].count("_Lden") == 4  # road, tram, rail, industry


def test_deep_flood_tile_is_cut_from_zoom_14(served: Callable) -> None:
    requests = served(lambda r: httpx.Response(200, content=quadrant_png()))
    resp = api.get(tile_url("flood", JELACIC_Z16))
    assert resp.status_code == 200
    assert len(requests) == 1  # only the zoom-14 parent was requested
    assert requests[0].url.params["BBOX"] == ",".join(
        f"{v:.3f}" for v in tiles.tile_bounds(*JELACIC_Z14)
    )
    image = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    # x = 4*8919 + 1 -> second 64 px column of the parent, enlarged to the whole tile
    assert image.getpixel((0, 0)) == image.getpixel((255, 255)) == (60, 0, 0, 255)


def test_stale_tile_served_when_service_down(
    served: Callable, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wms, "RETRY_DELAY_S", 0)
    served(lambda r: httpx.Response(200, content=png((1, 2, 3, 255))))
    assert api.get(tile_url("noise", JELACIC_Z14)).status_code == 200
    cached = next((tmp_path / "tiles").rglob("*.png"))
    old = time.time() - tiles.TTL_S - 1
    os.utime(cached, (old, old))
    served(lambda r: httpx.Response(502))
    resp = api.get(tile_url("noise", JELACIC_Z14))
    assert resp.status_code == 200
    assert resp.content == cached.read_bytes()


def test_service_down_without_cache_is_502(
    served: Callable, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wms, "RETRY_DELAY_S", 0)
    served(lambda r: httpx.Response(502))
    assert api.get(tile_url("noise", JELACIC_Z14)).status_code == 502


def test_tile_outside_zagreb_is_404(served: Callable) -> None:
    requests = served(lambda r: httpx.Response(200, content=png((0, 0, 0, 0))))
    assert api.get(tile_url("noise", (14, 0, 0))).status_code == 404
    assert api.get("/api/tiles/elsewhere/14/8919/5841.png").status_code == 422
    assert requests == []


def test_heatmap() -> None:
    resp = api.get("/api/heatmap", headers={"Accept-Encoding": "gzip"})
    assert resp.status_code == 200
    assert resp.headers["content-encoding"] == "gzip"  # 2.5 MB raw
    body = resp.json()
    assert len(body["features"]) == 10_260  # build of 2026-11-05, docs/ekoskor.md
    assert set(body["metadata"]["sources"]) <= SOURCES.keys()
    cell = body["features"][0]["properties"]
    assert set(cell) == {"ekoskor", "flood", "noise", "air", "waste", "mobility", "green"}
