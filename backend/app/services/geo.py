"""Straight-line distances in metres via EPSG:3765 (HTRS96/TM, the Croatian projection).

Used by the air, waste and mobility layers and by scripts/build_heatmap.py, so a point's
nearest station / yard / stop is the same on the address card and in the heatmap.
"""

from functools import cache

import numpy as np
import shapely
import shapely.geometry
import shapely.ops
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


def _lonlat_to_xy(lonlat: np.ndarray) -> np.ndarray:
    return np.column_stack(to_htrs.transform(lonlat[:, 0], lonlat[:, 1]))


def project_geometries(features: list[dict]) -> list[shapely.Geometry]:
    """GeoJSON features (EPSG:4326) -> shapely geometries in EPSG:3765 metres."""
    return [
        shapely.transform(shapely.geometry.shape(f["geometry"]), _lonlat_to_xy) for f in features
    ]


def nearest_geometry(
    tree: shapely.STRtree, geoms: list[shapely.Geometry], lat: float, lon: float
) -> tuple[int, float, float, float]:
    """(index, distance m, lat, lon of the nearest point on it) for lines or areas in
    EPSG:3765; distance 0 if the point is inside an area."""
    x, y = to_htrs.transform(lon, lat)
    point = shapely.Point(x, y)
    i = int(tree.nearest(point))
    near = shapely.ops.nearest_points(geoms[i], point)[0]
    near_lon, near_lat = from_htrs.transform(near.x, near.y)
    return i, float(geoms[i].distance(point)), near_lat, near_lon
