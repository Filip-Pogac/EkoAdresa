"""Waste layer: nearest recycling yard and green island (data/waste.geojson).

Sources: zg-reciklaza (City recycling yards, 2022) and osm-reciklaza (OpenStreetMap
recycling containers for paper, plastic or glass). Only fixed yards count for the score;
mobile yards operate on certain days only (decision 2026-11-05) and are shown as extra
information. Scoring: ekoskor.waste_score (linear by distance, docs/ekoskor.md).
"""

import json
from dataclasses import dataclass
from functools import cache

import numpy as np

from app.models import GreenIsland, RecyclingYard, WasteLayer
from app.paths import DATA_DIR
from app.services.ekoskor import status, waste_score
from app.services.geo import distances_m, project

SOURCE_ID = "zg-reciklaza"
DATA_FILE = "waste.geojson"


@dataclass(frozen=True)
class _Points:
    features: list[dict]
    xy: np.ndarray  # EPSG:3765 metres

    def nearest(self, lat: float, lon: float) -> tuple[dict, int]:
        d = distances_m(self.xy, lat, lon)
        i = int(np.argmin(d))
        return self.features[i], round(float(d[i]))


def _points(features: list[dict]) -> _Points:
    lon, lat = np.array([f["geometry"]["coordinates"] for f in features]).T
    return _Points(features, project(lon, lat))


@cache
def _data() -> dict[str, _Points]:
    features = json.loads((DATA_DIR / DATA_FILE).read_text(encoding="utf-8"))["features"]

    def select(type_: str, kind: str | None = None) -> _Points:
        return _points(
            [
                f
                for f in features
                if f["properties"]["type"] == type_
                and (kind is None or f["properties"].get("kind") == kind)
            ]
        )

    return {
        "fixed": select("recycling_yard", "fixed"),
        "mobile": select("recycling_yard", "mobile"),
        "island": select("green_island"),
    }


def _yard(feature: dict, distance_m: int) -> RecyclingYard:
    p = feature["properties"]
    lon, lat = feature["geometry"]["coordinates"]
    return RecyclingYard(
        name=p["name"],
        address=p.get("address"),
        opening_hours=p.get("opening_hours"),
        lat=lat,
        lon=lon,
        distance_m=distance_m,
        source_id=p["source_id"],
    )


def waste_at(lat: float, lon: float) -> WasteLayer:
    data = _data()
    yard, yard_m = data["fixed"].nearest(lat, lon)
    mobile, mobile_m = data["mobile"].nearest(lat, lon)
    island, island_m = data["island"].nearest(lat, lon)
    island_lon, island_lat = island["geometry"]["coordinates"]
    score = waste_score(yard_m, island_m)
    return WasteLayer(
        status=status(score),
        score=round(score),
        source_id=SOURCE_ID,
        yard=_yard(yard, yard_m),
        mobile_yard=_yard(mobile, mobile_m),
        island=GreenIsland(
            name=island["properties"].get("name"),
            accepts=island["properties"]["accepts"],
            lat=island_lat,
            lon=island_lon,
            distance_m=island_m,
            source_id=island["properties"]["source_id"],
        ),
        yard_distance_m=yard_m,
        island_distance_m=island_m,
    )
