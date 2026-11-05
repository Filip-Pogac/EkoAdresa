"""GET /api/compare offline, on the recorded reference-point responses."""

from collections.abc import Callable

import httpx2 as httpx

from app.services import flood
from tests.conftest import Handler
from tests.reference_points import POINTS
from tests.test_profile import api, get_profile, recorded


def get_compare(a: str, b: str) -> httpx.Response:
    (a_lat, a_lon), (b_lat, b_lon) = POINTS[a], POINTS[b]
    return api.get("/api/compare", params={"a_lat": a_lat, "a_lon": a_lon, "b_lat": b_lat,
                                           "b_lon": b_lon, "a_address": "A 1"})  # fmt: skip


def test_savica_vs_jelacic(use: Callable[[Handler], None]) -> None:
    use(recorded)
    resp = get_compare("savica", "jelacic")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    savica, jelacic = get_profile("savica"), get_profile("jelacic")
    # same profiles as /api/profile (generated_at differs)
    assert body["a"]["layers"] == savica["layers"]
    assert body["b"]["layers"] == jelacic["layers"]
    assert body["a"]["location"]["address"] == "A 1"
    assert body["b"]["location"]["address"] is None
    assert body["ekoskor_diff"] == jelacic["ekoskor"] - savica["ekoskor"]
    for name, diff in body["layers"].items():
        sa, sb = savica["layers"][name]["score"], jelacic["layers"][name]["score"]
        assert (diff["score_a"], diff["score_b"]) == (sa, sb)
        assert diff["better"] == (None if sa == sb else "a" if sa > sb else "b")
    # Savica is in the low-probability flood zone, Jelačić outside all zones
    assert body["layers"]["flood"]["better"] == "b"


def test_same_point_has_no_differences(use: Callable[[Handler], None]) -> None:
    use(recorded)
    body = get_compare("sljeme", "sljeme").json()
    assert body["ekoskor_diff"] == 0
    assert all(diff["better"] is None for diff in body["layers"].values())


def test_unavailable_layer_is_not_compared(use: Callable[[Handler], None]) -> None:
    def flood_down(request: httpx.Request) -> httpx.Response:
        if str(request.url).startswith(flood.HV_POPLAVE_URL):
            return httpx.Response(502)
        return recorded(request)

    use(flood_down)
    body = get_compare("savica", "jelacic").json()
    assert body["layers"]["flood"] == {"score_a": None, "score_b": None, "better": None}
    assert body["ekoskor_diff"] is not None  # 4 layers left on both sides


def test_outside_pilot_area_names_the_point(use: Callable[[Handler], None]) -> None:
    use(recorded)
    lat, lon = POINTS["jelacic"]
    resp = api.get("/api/compare", params={"a_lat": lat, "a_lon": lon,
                                           "b_lat": 43.5081, "b_lon": 16.4402})  # fmt: skip
    assert resp.status_code == 422
    assert resp.json() == {"detail": "outside_pilot_area:b"}
