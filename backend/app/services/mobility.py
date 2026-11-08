"""Green mobility layer: getting around without a car.

- ZET bus and tram platforms (data/transit.geojson); counts are platforms, one published
  point per stop and direction (decision 2026-11-05)
- bike: the nearer of the City bike path (data/bike_paths.geojson, zg-biciklisticke-staze)
  and the Bajs station (data/bike_stations.geojson, osm-bajs; decision 2026-11-07, OSM
  since 2026-11-08). Both use the same distance rule, so the nearer one decides the bike part.

From scripts/fetch_transit.py, scripts/fetch_green_mobility.py and scripts/fetch_bajs.py.
Scoring: ekoskor.mobility_score (docs/ekoskor.md), 4/5 transit + 1/5 bike (decision
2026-11-06). Parks and forests are their own layer (services/green.py).
"""

import json
from functools import cache

import numpy as np

from app.models import BikePath, BikeStation, MobilityLayer, Stop
from app.paths import DATA_DIR
from app.services.ekoskor import (
    STOPS_NEAR_M,
    STOPS_WALK_M,
    bike_score,
    mobility_score,
    status,
    transit_score,
)
from app.services.geo import distances_m, lines_or_areas, nearest_geometry, project

SOURCE_ID = "zg-zet"
DATA_FILE = "transit.geojson"
BIKE_FILE = "bike_paths.geojson"
STATIONS_FILE = "bike_stations.geojson"
STOP_TYPES = {"bus_stop": "bus", "tram_stop": "tram"}


@cache
def _data() -> tuple[list[dict], np.ndarray]:
    features = json.loads((DATA_DIR / DATA_FILE).read_text(encoding="utf-8"))["features"]
    lon, lat = np.array([f["geometry"]["coordinates"] for f in features]).T
    return features, project(lon, lat)


@cache
def _stations() -> tuple[list[dict], np.ndarray]:
    features = json.loads((DATA_DIR / STATIONS_FILE).read_text(encoding="utf-8"))["features"]
    lon, lat = np.array([f["geometry"]["coordinates"] for f in features]).T
    return features, project(lon, lat)


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


def _nearest_station(lat: float, lon: float) -> BikeStation:
    features, xy = _stations()
    d = distances_m(xy, lat, lon)
    i = int(np.argmin(d))
    p = features[i]["properties"]
    st_lon, st_lat = features[i]["geometry"]["coordinates"]
    return BikeStation(
        name=p["name"],
        ref=p["ref"],
        position_unchecked=p["position_unchecked"],
        lat=st_lat,
        lon=st_lon,
        distance_m=round(float(d[i])),
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
    station = _nearest_station(lat, lon)
    # bike_score falls with distance, so the nearer of the two gives the higher bike score
    bike_m = min(bike.distance_m, station.distance_m)
    score = mobility_score(stops_300m, stops_500m, bike_m)
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
        nearest_bike_station=station,
        transit_score=round(transit_score(stops_300m, stops_500m)),
        bike_score=round(bike_score(bike_m)),
    )
