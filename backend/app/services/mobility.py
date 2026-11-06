"""Green mobility layer: public transport, cycling, and walking & green near the address.

- ZET bus and tram platforms (data/transit.geojson); counts are platforms, one published
  point per stop and direction (decision 2026-11-05)
- nearest City bike path (data/bike_paths.geojson, zg-biciklisticke-staze)
- nearest park, forest, public garden or nature reserve of at least 0.5 ha
  (data/parks.geojson, osm-parkovi)

All three from scripts/fetch_transit.py and scripts/fetch_green_mobility.py.
Scoring: ekoskor.mobility_score (docs/ekoskor.md), 50 % / 25 % / 25 % (decision 2026-11-06).
"""

import json
from functools import cache

import numpy as np
import shapely

from app.models import BikePath, GreenArea, MobilityLayer, Stop
from app.paths import DATA_DIR
from app.services.ekoskor import (
    STOPS_NEAR_M,
    STOPS_WALK_M,
    bike_score,
    green_score,
    mobility_score,
    status,
    transit_score,
)
from app.services.geo import distances_m, nearest_geometry, project, project_geometries

SOURCE_ID = "zg-zet"
DATA_FILE = "transit.geojson"
BIKE_FILE = "bike_paths.geojson"
GREEN_FILE = "parks.geojson"
STOP_TYPES = {"bus_stop": "bus", "tram_stop": "tram"}


@cache
def _data() -> tuple[list[dict], np.ndarray]:
    features = json.loads((DATA_DIR / DATA_FILE).read_text(encoding="utf-8"))["features"]
    lon, lat = np.array([f["geometry"]["coordinates"] for f in features]).T
    return features, project(lon, lat)


@cache
def lines_or_areas(file: str) -> tuple[list[dict], list[shapely.Geometry], shapely.STRtree]:
    """Features of a line/area snapshot, their EPSG:3765 geometries and a spatial index."""
    features = json.loads((DATA_DIR / file).read_text(encoding="utf-8"))["features"]
    geoms = project_geometries(features)
    return features, geoms, shapely.STRtree(geoms)


def _nearest_bike_path(lat: float, lon: float) -> BikePath:
    features, geoms, tree = lines_or_areas(BIKE_FILE)
    i, d, near_lat, near_lon = nearest_geometry(tree, geoms, lat, lon)
    p = features[i]["properties"]
    return BikePath(
        name=p["name"],
        category=p["category"],
        lat=round(near_lat, 6),
        lon=round(near_lon, 6),
        distance_m=round(d),
        source_id=p["source_id"],
    )


def _nearest_green(lat: float, lon: float) -> GreenArea:
    features, geoms, tree = lines_or_areas(GREEN_FILE)
    i, d, near_lat, near_lon = nearest_geometry(tree, geoms, lat, lon)
    p = features[i]["properties"]
    return GreenArea(
        name=p["name"],
        kind=p["kind"],
        area_m2=p["area_m2"],
        lat=round(near_lat, 6),
        lon=round(near_lon, 6),
        distance_m=round(d),
        source_id=p["source_id"],
    )


def mobility_at(lat: float, lon: float) -> MobilityLayer:
    features, xy = _data()
    d = distances_m(xy, lat, lon)
    stops_300m = int((d <= STOPS_NEAR_M).sum())
    stops_500m = int((d <= STOPS_WALK_M).sum())
    i = int(np.argmin(d))
    nearest = features[i]
    p = nearest["properties"]
    stop_lon, stop_lat = nearest["geometry"]["coordinates"]
    bike = _nearest_bike_path(lat, lon)
    green = _nearest_green(lat, lon)
    score = mobility_score(stops_300m, stops_500m, bike.distance_m, green.distance_m)
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
        nearest_bike_path=bike,
        nearest_green=green,
        transit_score=round(transit_score(stops_300m, stops_500m)),
        bike_score=round(bike_score(bike.distance_m)),
        green_score=round(green_score(green.distance_m)),
    )
