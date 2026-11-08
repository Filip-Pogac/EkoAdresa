"""Mobility and green layers at the reference points, from the committed snapshots.

Mobility counts are the Phase 0 table in docs/data-sources.md (bus + tram platforms).
"""

import pytest

from app.services.green import green_at
from app.services.mobility import mobility_at
from tests.reference_points import POINTS

EXPECTED_MOBILITY = {  # (≤300 m, ≤500 m, nearest type, nearest distance m, score, status)
    "savica": (2, 7, "bus", 57, 60, "yellow"),  # 0.8 * 50 + 0.2 * 100
    "jelacic": (6, 16, "tram", 27, 100, "green"),
    "sljeme": (1, 3, "bus", 145, 40, "yellow"),
}
EXPECTED_BIKE = {  # (bike path m, transit part, bike part)
    "savica": (186, 50, 100),
    "jelacic": (191, 100, 100),
    "sljeme": (8272, 50, 0),
}
EXPECTED_GREEN = {  # (park/forest name, distance m, score, status)
    "savica": ("Park Marije Ružičke Strozzi", 153, 100, "green"),
    "jelacic": ("Zrinjevac", 196, 100, "green"),
    "sljeme": ("Park prirode Medvednica", 0, 100, "green"),  # inside the nature park
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
    bike = layer.nearest_bike_path
    assert (bike.distance_m, layer.transit_score, layer.bike_score) == EXPECTED_BIKE[point]
    assert bike.source_id == "zg-biciklisticke-staze"


@pytest.mark.parametrize("point", POINTS)
def test_green(point: str) -> None:
    layer = green_at(*POINTS[point])
    g = layer.nearest
    assert (g.name, g.distance_m, layer.score, layer.status) == EXPECTED_GREEN[point]
    assert layer.source_id == g.source_id == "osm-parkovi"
    assert g.area_m2 >= 5000


def test_middle_of_maksimir_is_green_space_not_mobility() -> None:
    # 2026-11-06: a point inside Park-šuma Maksimir, 713 m from the nearest ZET stop
    lat, lon = 45.8305, 16.0217
    assert green_at(lat, lon).status == "green"
    assert mobility_at(lat, lon).status == "red"


def test_bike_station_counts_when_nearer_than_a_lane() -> None:
    # 2026-11-08: Bajs station (OSM, position checked) 23 m away at the Sljeme cable car,
    # nearest bike lane 3.7 km away. A lane alone would give 0; the station gives 100.
    layer = mobility_at(45.860897, 15.983172)
    station = layer.nearest_bike_station
    assert (station.name, station.distance_m) == ("Bajs Žičara Sljeme", 23)
    assert station.source_id == "osm-bajs"
    assert layer.nearest_bike_path.distance_m > 3000
    assert layer.bike_score == 100
