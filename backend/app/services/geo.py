"""Straight-line distances in metres via EPSG:3765 (HTRS96/TM, the Croatian projection).

Used by the air, waste and mobility layers and by scripts/build_heatmap.py, so a point's
nearest station / yard / stop is the same on the address card and in the heatmap.
"""

from functools import cache

import numpy as np
import shapely
from pyproj import Transformer

from app.paths import DATA_DIR

BOUNDARY_FILE = "zagreb_boundary.geojson"

to_htrs = Transformer.from_crs("EPSG:4326", "EPSG:3765", always_xy=True)  # lon/lat -> x/y m
from_htrs = Transformer.from_crs("EPSG:3765", "EPSG:4326", always_xy=True)


def project(lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
    """EPSG:4326 lon/lat arrays -> (n, 2) array of EPSG:3765 metres."""
    return np.column_stack(to_htrs.transform(lons, lats))


def distances_m(points_xy: np.ndarray, lat: float, lon: float) -> np.ndarray:
    """Distance in metres from (lat, lon) to each projected point."""
    x, y = to_htrs.transform(lon, lat)
    return np.hypot(points_xy[:, 0] - x, points_xy[:, 1] - y)


@cache
def _pilot_area() -> shapely.Geometry:
    """City of Zagreb boundary (osm-granice), written by scripts/build_heatmap.py."""
    area = shapely.from_geojson((DATA_DIR / BOUNDARY_FILE).read_text(encoding="utf-8"))
    shapely.prepare(area)
    return area


def in_pilot_area(lat: float, lon: float) -> bool:
    return bool(shapely.contains_xy(_pilot_area(), lon, lat))
