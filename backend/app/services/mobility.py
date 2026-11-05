"""Green mobility layer: ZET bus and tram platforms near the address (data/transit.geojson).

Counts are platforms, one published point per stop and direction (decision 2026-11-05).
Scoring: ekoskor.mobility_score (docs/ekoskor.md).
"""

import json
from functools import cache

import numpy as np

from app.models import MobilityLayer, Stop
from app.paths import DATA_DIR
from app.services.ekoskor import STOPS_NEAR_M, STOPS_WALK_M, mobility_score, status
from app.services.geo import distances_m, project

SOURCE_ID = "zg-zet"
DATA_FILE = "transit.geojson"
STOP_TYPES = {"bus_stop": "bus", "tram_stop": "tram"}


@cache
def _data() -> tuple[list[dict], np.ndarray]:
    features = json.loads((DATA_DIR / DATA_FILE).read_text(encoding="utf-8"))["features"]
    lon, lat = np.array([f["geometry"]["coordinates"] for f in features]).T
    return features, project(lon, lat)


def mobility_at(lat: float, lon: float) -> MobilityLayer:
    features, xy = _data()
    d = distances_m(xy, lat, lon)
    stops_300m = int((d <= STOPS_NEAR_M).sum())
    stops_500m = int((d <= STOPS_WALK_M).sum())
    i = int(np.argmin(d))
    nearest = features[i]
    p = nearest["properties"]
    stop_lon, stop_lat = nearest["geometry"]["coordinates"]
    score = mobility_score(stops_300m, stops_500m)
    return MobilityLayer(
        status=status(score),
        score=round(score),
        source_id=SOURCE_ID,
        stops_300m=stops_300m,
        stops_500m=stops_500m,
        nearest_stop=Stop(
            name=p["name"],
            type=STOP_TYPES[p["type"]],  # type: ignore[arg-type]
            direction=p.get("direction"),
            lines=p["lines"],
            lat=stop_lat,
            lon=stop_lon,
            distance_m=round(float(d[i])),
            source_id=p["source_id"],
        ),
    )
