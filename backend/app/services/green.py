"""Green space layer (Zelenilo): nearest park, forest, public garden or nature reserve of at
least 0.5 ha (data/parks.geojson, osm-parkovi, scripts/fetch_green_mobility.py).

Distance is to the nearest point of the area's outline, 0 if the address is inside it.
Scoring: ekoskor.green_score (docs/ekoskor.md), own layer since 2026-11-06.
"""

from app.models import GreenArea, GreenLayer
from app.services.ekoskor import green_score, status
from app.services.geo import lines_or_areas, nearest_geometry

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
