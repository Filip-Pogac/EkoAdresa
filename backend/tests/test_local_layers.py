"""Waste and mobility layers at the reference points, from the committed snapshots.

Mobility counts are the Phase 0 table in docs/data-sources.md (bus + tram platforms).
"""

import pytest

from app.services.ekoskor import waste_score
from app.services.mobility import mobility_at
from app.services.waste import waste_at
from tests.reference_points import POINTS

EXPECTED_MOBILITY = {  # (≤300 m, ≤500 m, nearest type, nearest distance m, score, status)
    "savica": (2, 7, "bus", 57, 75, "green"),
    "jelacic": (6, 16, "tram", 27, 100, "green"),
    "sljeme": (1, 3, "bus", 145, 50, "yellow"),
}
EXPECTED_BIKE_GREEN = {  # (bike path m, park/forest name, park m, transit, bike, green parts)
    "savica": (186, "Park Marije Ružičke Strozzi", 153, 50, 100, 100),
    "jelacic": (191, "Zrinjevac", 196, 100, 100, 100),
    "sljeme": (8272, "Park prirode Medvednica", 0, 50, 0, 100),  # inside the nature park
}
EXPECTED_WASTE = {  # (nearest fixed yard, yard m, nearest mobile yard, island m), ±10 m
    "savica": ("RD KAJZERICA", 2636, "MRD TRNJE", 521),
    "jelacic": ("RD TREŠNJEVKA - SJEVER", 2398, "MRD GORNJI GRAD - MEDVEŠČAK", 332),
    "sljeme": ("RD PRILESJE", 9680, "MRD PODSLJEME, KRALJIČIN ZDENAC", 4589),
}


@pytest.mark.parametrize("point", POINTS)
def test_mobility(point: str) -> None:
    layer = mobility_at(*POINTS[point])
    stop = layer.nearest_stop
    got = (
        layer.stops_300m,
        layer.stops_500m,
        stop.type,
        stop.distance_m,
        layer.score,
        layer.status,
    )
    assert got == EXPECTED_MOBILITY[point]
    assert layer.source_id == stop.source_id == "zg-zet"
    assert stop.lines and stop.name
    bike, green = layer.nearest_bike_path, layer.nearest_green
    assert (
        bike.distance_m,
        green.name,
        green.distance_m,
        layer.transit_score,
        layer.bike_score,
        layer.green_score,
    ) == EXPECTED_BIKE_GREEN[point]
    assert bike.source_id == "zg-biciklisticke-staze"
    assert green.source_id == "osm-parkovi"
    assert green.area_m2 >= 5000


@pytest.mark.parametrize("point", POINTS)
def test_waste(point: str) -> None:
    layer = waste_at(*POINTS[point])
    yard, yard_m, mobile, island_m = EXPECTED_WASTE[point]
    assert layer.yard.name == yard
    assert layer.yard_distance_m == pytest.approx(yard_m, abs=10)
    assert layer.mobile_yard.name == mobile
    assert layer.island_distance_m == pytest.approx(island_m, abs=10)
    assert layer.score == round(waste_score(layer.yard_distance_m, layer.island_distance_m))
    assert layer.yard.source_id == "zg-reciklaza"
    assert layer.island.source_id == "osm-reciklaza"


def test_mobile_yard_does_not_count_for_the_score() -> None:
    # At Savica the mobile yard (1.3 km) is much closer than the fixed one (2.6 km)
    layer = waste_at(*POINTS["savica"])
    assert layer.mobile_yard.distance_m < layer.yard_distance_m
    assert layer.score == round(waste_score(layer.yard.distance_m, layer.island_distance_m))


def test_sljeme_scores_zero_for_waste() -> None:
    layer = waste_at(*POINTS["sljeme"])
    assert (layer.score, layer.status) == (0, "red")
