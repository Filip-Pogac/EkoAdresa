"""EkoSkor v1 thresholds, edges, missing layers and renormalisation (docs/ekoskor.md)."""

import pytest

from app.services.ekoskor import (
    WEIGHTS,
    air_score,
    ekoskor,
    flood_score,
    mobility_score,
    noise_score,
    waste_score,
)


def test_weights_sum_to_one() -> None:
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


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
        (1000, 300, 100),  # both edges inclusive
        (1001, 300, 50),
        (1000, 301, 50),
        (1001, 301, 0),
        (200, 50, 100),
    ],
)
def test_waste(yard_m: float, island_m: float, expected: float) -> None:
    assert waste_score(yard_m, island_m) == expected


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
def test_mobility(n300: int, n500: int, expected: float) -> None:
    assert mobility_score(n300, n500) == expected


def test_all_layers_weighted_mean() -> None:
    scores = {"flood": 100.0, "noise": 0.0, "air": 50.0, "waste": 100.0, "mobility": 50.0}
    # 25 + 0 + 10 + 15 + 7.5 = 57.5 -> rounded half up -> 58
    assert ekoskor(scores) == 58  # type: ignore[arg-type]


def test_extremes() -> None:
    assert ekoskor(dict.fromkeys(WEIGHTS, 100.0)) == 100  # type: ignore[arg-type]
    assert ekoskor(dict.fromkeys(WEIGHTS, 0.0)) == 0  # type: ignore[arg-type]


def test_missing_layer_renormalises() -> None:
    # air unavailable: (25*100 + 25*0 + 15*100 + 15*100) / 0.80 = 5500 / 80 = 68.75 -> 69
    scores = {"flood": 100.0, "noise": 0.0, "air": None, "waste": 100.0, "mobility": 100.0}
    assert ekoskor(scores) == 69  # type: ignore[arg-type]


def test_rounds_half_up() -> None:
    # 0 + 25 + 10 + 7.5 + 0 = 42.5 -> 43 (Python's round() would give 42)
    scores = {"flood": 0.0, "noise": 100.0, "air": 50.0, "waste": 50.0, "mobility": 0.0}
    assert ekoskor(scores) == 43  # type: ignore[arg-type]


def test_three_layers_is_enough_two_is_not() -> None:
    three = {"flood": 100.0, "noise": 100.0, "air": None, "waste": 0.0, "mobility": None}
    # (2500 + 2500 + 0) / 65 = 76.9 -> 77
    assert ekoskor(three) == 77  # type: ignore[arg-type]
    two = {"flood": 100.0, "noise": 100.0, "air": None, "waste": None, "mobility": None}
    assert ekoskor(two) is None  # type: ignore[arg-type]
