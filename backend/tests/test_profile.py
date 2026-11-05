"""GET /api/profile end to end, offline: recorded WMS/WFS responses + committed data."""

import asyncio
from collections.abc import Callable
from pathlib import Path

import httpx2 as httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import air, dhmz, ekoskor, flood, profile
from tests import test_services
from tests.conftest import Handler
from tests.reference_points import POINTS
from tests.test_dhmz import dhmz_replay

WFS_FIXTURE = Path(__file__).parent / "fixtures" / "wfs" / "rh_zrak_indeks.xml"


def recorded(request: httpx.Request) -> httpx.Response:
    if str(request.url).startswith(air.LIVE_URL):
        return httpx.Response(200, content=WFS_FIXTURE.read_bytes())
    if str(request.url).startswith(dhmz.URL):
        return dhmz_replay(request)
    return test_services.replay(request)  # flood + noise WMS fixtures per reference point


api = TestClient(app)


def get_profile(point: str, **params: object) -> dict:
    lat, lon = POINTS[point]
    resp = api.get("/api/profile", params={"lat": lat, "lon": lon, **params})
    assert resp.status_code == 200, resp.text
    return resp.json()


EXPECTED = {  # status per layer at the reference points
    "savica": {"flood": "yellow", "noise": "red", "air": "yellow", "waste": "green",
               "mobility": "yellow"},
    "jelacic": {"flood": "green", "noise": "red", "air": "green", "waste": "green",
                "mobility": "green"},
    "sljeme": {"flood": "green", "noise": "green", "air": "green", "waste": "red",
               "mobility": "yellow"},
}  # fmt: skip


@pytest.mark.parametrize("point", POINTS)
def test_reference_points(use: Callable[[Handler], None], point: str) -> None:
    use(recorded)
    body = get_profile(point, address="Test 1, Zagreb")
    layers = body["layers"]
    assert {name: layer["status"] for name, layer in layers.items()} == EXPECTED[point]
    scores = {name: layer["score"] for name, layer in layers.items()}
    assert body["ekoskor"] == ekoskor.ekoskor(scores)  # from the sub-scores shown on the card
    assert body["location"] == {"lat": POINTS[point][0], "lon": POINTS[point][1],
                                "address": "Test 1, Zagreb"}  # fmt: skip
    assert all(layer["source_id"] for layer in layers.values())


def test_savica_is_in_the_low_flood_zone(use: Callable[[Handler], None]) -> None:
    use(recorded)
    assert get_profile("savica")["layers"]["flood"]["zone"] == "low"


def test_flood_service_down_other_layers_still_render(use: Callable[[Handler], None]) -> None:
    def flood_down(request: httpx.Request) -> httpx.Response:
        if str(request.url).startswith(flood.HV_POPLAVE_URL):
            return httpx.Response(502)
        return recorded(request)

    use(flood_down)
    body = get_profile("jelacic")
    assert body["layers"]["flood"] == {"status": "unavailable", "reason": "error",
                                       "source_id": "hv-poplave"}  # fmt: skip
    others = {k: v for k, v in body["layers"].items() if k != "flood"}
    assert all(layer["status"] != "unavailable" for layer in others.values())
    # EkoSkor over the 4 remaining layers, weights renormalised
    assert body["ekoskor"] == ekoskor.ekoskor({k: v["score"] for k, v in others.items()})


def test_slow_layer_times_out(
    use: Callable[[Handler], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(profile, "LAYER_TIMEOUT_S", 0.2)

    async def slow_noise(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("REQUEST") == "GetFeatureInfo":
            await asyncio.sleep(1)
        return recorded(request)

    use(slow_noise)  # type: ignore[arg-type]
    body = get_profile("jelacic")
    assert body["layers"]["noise"]["reason"] == "timeout"
    assert body["layers"]["flood"]["status"] == "green"


def test_all_remote_services_down_still_scores_three_local_layers(
    use: Callable[[Handler], None],
) -> None:
    use(lambda request: httpx.Response(502))  # flood, noise down; air without live index
    body = get_profile("jelacic")
    assert body["layers"]["flood"]["status"] == body["layers"]["noise"]["status"] == "unavailable"
    # air (2023 data), waste and mobility are local: 3 layers, so there is still a score.
    # Fewer than 3 cannot happen through the API; covered in test_ekoskor.py.
    assert body["ekoskor"] is not None
    assert body["layers"]["air"]["live_index"] is None


@pytest.mark.parametrize(
    ("lat", "lon"),
    [(45.8704, 15.7929), (43.5081, 16.4402)],  # Zaprešić (next to Zagreb), Split
)
def test_outside_pilot_area(use: Callable[[Handler], None], lat: float, lon: float) -> None:
    use(recorded)
    resp = api.get("/api/profile", params={"lat": lat, "lon": lon})
    assert resp.status_code == 422
    assert resp.json() == {"detail": "outside_pilot_area"}


def test_openapi_documents_profile() -> None:
    assert "/api/profile" in api.get("/openapi.json").json()["paths"]
