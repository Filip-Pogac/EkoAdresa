"""Layers for the map: points (stations, recycling yards, green islands, ZET stops) and
lines/areas (bike paths, parks and forests). Bike stations and bike parking are points.

Served from the committed snapshots in data/. Points are trimmed to the properties the map
shows, so the browser loads less than half of the raw files; the line/area files are
already compact (scripts/fetch_green_mobility.py) and served as they are. EPSG:4326.
"""

import json
from collections.abc import Callable
from functools import cache
from typing import Literal

from app.paths import DATA_DIR

PointLayer = Literal[
    "air_stations", "recycling_yards", "green_islands", "stops", "bike_stations", "bike_parking"
]
ShapeLayer = Literal["bike_paths", "parks"]
MapLayer = PointLayer | ShapeLayer
SHAPE_FILES: dict[str, str] = {"bike_paths": "bike_paths.geojson", "parks": "parks.geojson"}

# layer -> (data file, feature filter, properties kept besides source_id)
_LAYERS: dict[str, tuple[str, Callable[[dict], bool], list[str]]] = {
    "air_stations": ("air_stations.geojson", lambda p: True, ["name", "station_type"]),
    "recycling_yards": (
        "waste.geojson",
        lambda p: p["type"] == "recycling_yard",
        ["name", "kind", "address", "opening_hours"],
    ),
    "green_islands": ("waste.geojson", lambda p: p["type"] == "green_island", ["accepts"]),
    "stops": ("transit.geojson", lambda p: True, ["name", "type", "lines"]),
    "bike_stations": ("bike_stations.geojson", lambda p: True, ["name", "location", "racks"]),
    "bike_parking": ("bike_parking.geojson", lambda p: True, ["name", "location", "kind", "racks"]),
}


@cache
def point_layer(name: PointLayer) -> dict:
    """GeoJSON FeatureCollection of the layer, built once per process."""
    file, keep, props = _LAYERS[name]
    data = json.loads((DATA_DIR / file).read_text(encoding="utf-8"))
    features = []
    for f in data["features"]:
        p = f["properties"]
        if not keep(p):
            continue
        lon, lat = f["geometry"]["coordinates"]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {k: p.get(k) for k in props} | {"source_id": p["source_id"]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


@cache
def shape_layer_bytes(name: ShapeLayer) -> bytes:
    """data/bike_paths.geojson or data/parks.geojson as is, read once per process."""
    return (DATA_DIR / SHAPE_FILES[name]).read_bytes()


@cache
def heatmap_bytes() -> bytes:
    """data/heatmap.geojson as is (scripts/build_heatmap.py), read once per process."""
    return (DATA_DIR / "heatmap.geojson").read_bytes()
