"""Point layers for the map (stations, recycling yards, green islands, ZET stops).

Served from the committed snapshots in data/, trimmed to the properties the map shows, so
the browser loads less than half of the raw files. Coordinates EPSG:4326.
"""

import json
from collections.abc import Callable
from functools import cache
from typing import Literal

from app.paths import DATA_DIR

PointLayer = Literal["air_stations", "recycling_yards", "green_islands", "stops"]

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
