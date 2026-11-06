"""Green space layer (Zelenilo): nearest park, forest, public garden or nature reserve of at
least 0.5 ha (data/parks.geojson, osm-parkovi, scripts/fetch_green_mobility.py).

Distance is to the nearest point of the area's outline, 0 if the address is inside it.
Scoring: ekoskor.green_score (docs/ekoskor.md), own layer since 2026-11-06.
"""

import shapely

from app.models import GreenArea, GreenLayer
from app.services.ekoskor import green_score, status
from app.services.geo import lines_or_areas, nearest_geometry, to_htrs

SOURCE_ID = "osm-parkovi"
DATA_FILE = "parks.geojson"


def green_at(lat: float, lon: float) -> GreenLayer:
    features, geoms, tree = lines_or_areas(DATA_FILE)
    i, d, near_lat, near_lon = nearest_geometry(tree, geoms, lat, lon)
    p = features[i]["properties"]
    score = green_score(d)
    return GreenLayer(
        status=status(score),
        score=round(score),
        source_id=SOURCE_ID,
        nearest=GreenArea(
            name=p["name"],
            kind=p["kind"],
            area_m2=p["area_m2"],
            lat=round(near_lat, 6),
            lon=round(near_lon, 6),
            distance_m=round(d),
            source_id=p["source_id"],
        ),
    )


def named_area_at(lat: float, lon: float) -> str | None:
    """Name of the park or forest the point lies in; the smallest one if several overlap
    (a named park inside a named forest), None if the point is in no named area."""
    features, geoms, tree = lines_or_areas(DATA_FILE)
    point = shapely.Point(*to_htrs.transform(lon, lat))
    inside = [
        int(i)
        for i in tree.query(point, predicate="intersects")
        if features[int(i)]["properties"]["name"]
    ]
    if not inside:
        return None
    return features[min(inside, key=lambda i: geoms[i].area)]["properties"]["name"]
