"""Noise at a point from zg-buka (Strateška karta buke Grada Zagreba, round 4).

GetFeatureInfo returns one feature per source and indicator; attribute `razina` is the
lower bound of a 5 dB band (50 = 50-54 dB ... 75 = ≥ 75 dB). See docs/data-sources.md.

Combining sources: the loudest source (decision 2026-11-05), not an energetic sum.
"""

ZG_BUKA_URL = "https://geoportal.zagreb.hr/Public/StrategijskoPlaniranje_Public/MapServer/WMSServer"
SOURCE_ID = "zg-buka"

SOURCES = ("Cestovni_promet", "Tramvajski_promet", "Zeljeznicki_promet", "Industrijski_pogon")
INDICATORS = ("Lden", "Lnight")
LAYERS = [f"SKB_R4_{source}_{indicator}" for source in SOURCES for indicator in INDICATORS]
PROPERTY_NAMES = ["razina"]  # no geometry: 394 B instead of 1.1 MB per query
LAYER_PREFIX = "SKB_R4_"


def bands_from_features(features: list[dict]) -> dict[str, int]:
    """GeoJSON features -> {'Cestovni_promet_Lden': 70, ...}.

    Feature ids look like 'SKB_R4_Cestovni_promet_Lden.fid-…'. If a layer returns more than
    one feature (should not happen with BUFFER=0), the louder band is kept.
    """
    bands: dict[str, int] = {}
    for f in features:
        key = f["id"].split(".")[0].removeprefix(LAYER_PREFIX)
        bands[key] = max(bands.get(key, 0), int(f["properties"]["razina"]))
    return bands


def loudest(bands: dict[str, int], indicator: str = "Lden") -> int | None:
    """Band lower bound of the loudest source for `indicator`, or None if no source is mapped.

    None inside the City most likely means below the lowest mapped band (< 50 dB): the road
    layer's extent covers the whole City. TODO(verify) against the noise map report.
    """
    values = [db for key, db in bands.items() if key.endswith(f"_{indicator}")]
    return max(values) if values else None
