"""EkoSkor v1 thresholds, edges, missing layers and renormalisation (docs/ekoskor.md)."""

import pytest

from app.services.ekoskor import (
    WEIGHTS,
    air_score,
    bike_score,
    ekoskor,
    flood_score,
    green_score,
    mobility_score,
    noise_score,
    status,
    transit_score,
    waste_score,
)


def test_weights_sum_to_one() -> None:
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_six_layer_weights() -> None:  # decision 2026-11-06
    assert WEIGHTS == {
        "flood": 0.20,
        "noise": 0.20,
        "air": 0.20,
        "waste": 0.15,
        "mobility": 0.15,
        "green": 0.10,
    }


@pytest.mark.parametrize(
    ("zone", "expected"), [("none", 100), ("low", 50), ("medium", 0), ("high", 0)]
)
def test_flood(zone: str, expected: float) -> None:
    assert flood_score(zone) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("lden_db", "expected"),
    [
        (None, 100),  # no mapped band = below 50 dB
        (40, 100),
        (53, 100),  # WHO road-traffic guideline, inclusive
        (54, 50),
        (64, 50),
        (65, 0),
        (80, 0),
        # zg-buka band lower bounds
        (50, 100),
        (55, 50),
        (60, 50),
        (70, 0),
        (75, 0),
    ],
)
def test_noise(lden_db: float | None, expected: float) -> None:
    assert noise_score(lden_db) == expected


@pytest.mark.parametrize(
    ("pm10", "expected"),
    [(5, 100), (15, 100), (27.5, 50), (40, 0), (60, 0), (20, 80)],
)
def test_air(pm10: float, expected: float) -> None:
    assert air_score(pm10) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("yard_m", "island_m", "expected"),
    [
        (1000, 300, 100),  # both "near" edges inclusive
        (200, 50, 100),
        (5000, 1500, 0),  # both "far" edges
        (9000, 4000, 0),
        (5000, 300, 50),  # island perfect, yard at far edge
        (1000, 1500, 50),  # yard perfect, island at far edge
        (3000, 900, 50),  # both halfway: 50 and 50
        (2000, 300, 87.5),  # yard 75, island 100
        (1000, 600, 87.5),  # yard 100, island 75
    ],
)
def test_waste(yard_m: float, island_m: float, expected: float) -> None:
    assert waste_score(yard_m, island_m) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("n300", "n500", "expected"),
    [
        (3, 3, 100),
        (10, 12, 100),
        (2, 2, 50),
        (1, 4, 50),
        (0, 1, 50),  # nothing within 300 m but a stop within walking distance
        (0, 0, 0),
    ],
)
def test_transit(n300: int, n500: int, expected: float) -> None:
    assert transit_score(n300, n500) == expected


@pytest.mark.parametrize(
    ("distance_m", "expected"),
    [(0, 100), (200, 100), (600, 50), (1000, 0), (5000, 0)],
)
def test_bike(distance_m: float, expected: float) -> None:
    assert bike_score(distance_m) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("distance_m", "expected"),
    [(0, 100), (300, 100), (650, 50), (1000, 0), (3000, 0)],  # 0 m = inside the park
)
def test_green(distance_m: float, expected: float) -> None:
    assert green_score(distance_m) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("n300", "n500", "bike_m", "expected"),
    [
        (3, 3, 100, 100),
        (0, 0, 5000, 0),
        (3, 3, 5000, 200 / 3),  # transit alone is two thirds of the layer
        (0, 0, 0, 100 / 3),  # bike path only, no stop within 500 m
        (0, 1, 600, 50),  # 2/3 * 50 + 1/3 * 50
        (0, 0, 920, 10 / 3),  # middle of Maksimir: no stop within 500 m, bike path 920 m
    ],
)
def test_mobility(n300: int, n500: int, bike_m: float, expected: float) -> None:
    assert mobility_score(n300, n500, bike_m) == pytest.approx(expected)


def test_all_layers_weighted_mean() -> None:
    scores = {"flood": 100.0, "noise": 0.0, "air": 50.0, "waste": 100.0, "mobility": 50.0,
              "green": 100.0}  # fmt: skip
    # 20 + 0 + 10 + 15 + 7.5 + 10 = 62.5 -> rounded half up -> 63
    assert ekoskor(scores) == 63  # type: ignore[arg-type]


def test_extremes() -> None:
    assert ekoskor(dict.fromkeys(WEIGHTS, 100.0)) == 100  # type: ignore[arg-type]
    assert ekoskor(dict.fromkeys(WEIGHTS, 0.0)) == 0  # type: ignore[arg-type]


def test_missing_layer_renormalises() -> None:
    # air unavailable: (20*100 + 20*0 + 15*100 + 15*100 + 10*0) / 0.80 = 5000 / 80 = 62.5 -> 63
    scores = {"flood": 100.0, "noise": 0.0, "air": None, "waste": 100.0, "mobility": 100.0,
              "green": 0.0}  # fmt: skip
    assert ekoskor(scores) == 63  # type: ignore[arg-type]


def test_rounds_half_up() -> None:
    # 0 + 20 + 10 + 7.5 + 0 + 5 = 42.5 -> 43 (Python's round() would give 42)
    scores = {"flood": 0.0, "noise": 100.0, "air": 50.0, "waste": 50.0, "mobility": 0.0,
              "green": 50.0}  # fmt: skip
    assert ekoskor(scores) == 43  # type: ignore[arg-type]


def test_three_layers_is_enough_two_is_not() -> None:
    three = {"flood": 100.0, "noise": 100.0, "air": None, "waste": 0.0, "mobility": None,
             "green": None}  # fmt: skip
    # (2000 + 2000 + 0) / 55 = 72.7 -> 73
    assert ekoskor(three) == 73  # type: ignore[arg-type]
    two = {"flood": 100.0, "noise": 100.0, "air": None, "waste": None, "mobility": None,
           "green": None}  # fmt: skip
    assert ekoskor(two) is None  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("score", "expected"),
    [(100, "green"), (67, "green"), (66.7, "green"), (66.4, "yellow"), (50, "yellow"),
     (34, "yellow"), (33.6, "yellow"), (33.4, "red"), (0, "red")],
)  # fmt: skip
def test_status_in_thirds(score: float, expected: str) -> None:
    # status follows the rounded sub-score the card shows: 66.7 is shown as 67 -> green
    assert status(score) == expected
