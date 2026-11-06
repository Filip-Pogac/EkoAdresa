"""EkoSkor v1: 0-100 score of an address from five layer sub-scores.

Formula and thresholds: CLAUDE.md §2.4 and docs/ekoskor.md. Changing a threshold or weight
requires updating tests/test_ekoskor.py and docs/ekoskor.md in the same commit.

Each `*_score` returns 0-100. A layer whose data is unavailable is passed to `ekoskor` as
None and the remaining weights are renormalised; with fewer than 3 layers there is no score.
"""

import math
from typing import Literal

FloodZone = Literal["high", "medium", "low", "none"]
Layer = Literal["flood", "noise", "air", "waste", "mobility"]

WEIGHTS: dict[Layer, float] = {
    "flood": 0.25,
    "noise": 0.25,
    "air": 0.20,
    "waste": 0.15,
    "mobility": 0.15,
}
MIN_LAYERS = 3

# Noise, Lden in dB. WHO 2018 guideline for road traffic: 53 dB Lden.
NOISE_GOOD_MAX_DB = 53
NOISE_POOR_MIN_DB = 65
# Air, PM10 mean in µg/m3. 100 at the WHO 2021 annual guideline (15), 0 at the EU annual
# limit value (40, Directive 2008/50/EC), linear in between.
PM10_GOOD_UG_M3 = 15.0
PM10_POOR_UG_M3 = 40.0
# Waste and mobility distances in metres.
# Waste: each distance scores 100 at "near" and 0 at "far", linear in between (decision
# 2026-11-05, replaces the 1 km / 300 m on-off rule, which scored 0 almost everywhere).
YARD_NEAR_M = 1000
YARD_FAR_M = 5000
ISLAND_NEAR_M = 300
ISLAND_FAR_M = 1500
STOPS_NEAR_M = 300
STOPS_WALK_M = 500
STOPS_GOOD_COUNT = 3
# Green mobility = 50 % public transport + 25 % cycling + 25 % walking & green (decision
# 2026-11-06). Cycling: nearest City bike path, 100 at ≤ 200 m -> 0 at ≥ 1 km. Walking &
# green: nearest park, forest, public garden or nature reserve of at least 0.5 ha, 100 at
# ≤ 300 m (WHO Europe 2017: green space of 0.5-1 ha within 300 m) -> 0 at ≥ 1 km.
MOBILITY_PARTS = {"transit": 0.50, "bike": 0.25, "green": 0.25}
BIKE_NEAR_M = 200
BIKE_FAR_M = 1000
GREEN_NEAR_M = 300
GREEN_FAR_M = 1000


def _linear_down(value: float, near: float, far: float) -> float:
    """100 at ≤ near, 0 at ≥ far, linear in between."""
    t = (value - near) / (far - near)
    return 100.0 * (1.0 - min(1.0, max(0.0, t)))


def flood_score(zone: FloodZone) -> float:
    """Outside all zones 100, low-probability zone 50, medium or high probability 0."""
    return {"none": 100.0, "low": 50.0, "medium": 0.0, "high": 0.0}[zone]


def noise_score(lden_db: float | None) -> float:
    """≤ 53 dB 100, 54-64 dB 50, ≥ 65 dB 0 (steps: the map only has 5 dB bands).

    zg-buka gives bands; pass the band's lower bound (50, 55, 60, 65, 70, 75). None = no
    mapped band at the point, read as below 50 dB (see noise.loudest, TODO(verify)).
    """
    if lden_db is None or lden_db <= NOISE_GOOD_MAX_DB:
        return 100.0
    if lden_db < NOISE_POOR_MIN_DB:
        return 50.0
    return 0.0


def air_score(pm10_ug_m3: float) -> float:
    """100 at ≤ 15 µg/m3, 0 at ≥ 40 µg/m3, linear in between."""
    return _linear_down(pm10_ug_m3, PM10_GOOD_UG_M3, PM10_POOR_UG_M3)


def waste_score(yard_distance_m: float, island_distance_m: float) -> float:
    """Mean of: fixed recycling yard 100 at ≤ 1 km -> 0 at ≥ 5 km, and green island
    100 at ≤ 300 m -> 0 at ≥ 1.5 km."""
    yard = _linear_down(yard_distance_m, YARD_NEAR_M, YARD_FAR_M)
    island = _linear_down(island_distance_m, ISLAND_NEAR_M, ISLAND_FAR_M)
    return (yard + island) / 2


def transit_score(stops_300m: int, stops_500m: int) -> float:
    """≥ 3 stops (platforms) within 300 m: 100; any stop within 500 m: 50; none: 0."""
    if stops_300m >= STOPS_GOOD_COUNT:
        return 100.0
    if stops_500m >= 1:
        return 50.0
    return 0.0


def bike_score(bike_path_m: float) -> float:
    """Nearest bike path: 100 at ≤ 200 m, 0 at ≥ 1 km, linear in between."""
    return _linear_down(bike_path_m, BIKE_NEAR_M, BIKE_FAR_M)


def green_score(green_m: float) -> float:
    """Nearest park or forest (≥ 0.5 ha): 100 at ≤ 300 m, 0 at ≥ 1 km; 0 m = inside it."""
    return _linear_down(green_m, GREEN_NEAR_M, GREEN_FAR_M)


def mobility_score(stops_300m: int, stops_500m: int, bike_path_m: float, green_m: float) -> float:
    """50 % public transport + 25 % cycling + 25 % walking & green."""
    parts = {
        "transit": transit_score(stops_300m, stops_500m),
        "bike": bike_score(bike_path_m),
        "green": green_score(green_m),
    }
    return sum(MOBILITY_PARTS[k] * v for k, v in parts.items())


# Traffic light per layer from its sub-score, in equal thirds. For the step layers (flood,
# noise) this is simply 100 -> green, 50 -> yellow, 0 -> red.
STATUS_GREEN_MIN = 67
STATUS_YELLOW_MIN = 34


def status(score: float) -> Literal["green", "yellow", "red"]:
    if score >= STATUS_GREEN_MIN:
        return "green"
    if score >= STATUS_YELLOW_MIN:
        return "yellow"
    return "red"


def ekoskor(scores: dict[Layer, float | None]) -> int | None:
    """Weighted mean of the available sub-scores, rounded half up; None if < 3 layers."""
    available = {layer: s for layer, s in scores.items() if s is not None}
    if len(available) < MIN_LAYERS:
        return None
    total_weight = sum(WEIGHTS[layer] for layer in available)
    value = sum(WEIGHTS[layer] * s for layer, s in available.items()) / total_weight
    # Round half up (68.5 -> 69), not Python's half-to-even; epsilon absorbs float noise.
    return math.floor(value + 0.5 + 1e-9)
