"""Noise at a point from zg-buka (Strateška karta buke Grada Zagreba, round 4).

GetFeatureInfo returns one feature per source and indicator; attribute `razina` is the
lower bound of a 5 dB band (50 = 50-54 dB ... 75 = ≥ 75 dB). See docs/data-sources.md.

Combining sources: the loudest source (decision 2026-11-05), not an energetic sum.
"""

import httpx2 as httpx

from app.cache import Cache, cached_fetch
from app.models import NoiseLayer, NoiseSource
from app.services import wms
from app.services.ekoskor import noise_score, status

ZG_BUKA_URL = "https://geoportal.zagreb.hr/Public/StrategijskoPlaniranje_Public/MapServer/WMSServer"
SOURCE_ID = "zg-buka"

SOURCES = ("Cestovni_promet", "Tramvajski_promet", "Zeljeznicki_promet", "Industrijski_pogon")
INDICATORS = ("Lden", "Lnight")
LAYERS = [f"SKB_R4_{source}_{indicator}" for source in SOURCES for indicator in INDICATORS]
PROPERTY_NAMES = ["razina"]  # no geometry: 394 B instead of 1.1 MB per query
LAYER_PREFIX = "SKB_R4_"
# app.cache namespace for the GetFeatureInfo features of LAYERS with PROPERTY_NAMES
CACHE_NAMESPACE = "zg-buka:SKB_R4:razina"


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


SOURCE_CODES: dict[str, NoiseSource] = {
    "Cestovni_promet": "road",
    "Tramvajski_promet": "tram",
    "Zeljeznicki_promet": "rail",
    "Industrijski_pogon": "industry",
}
BAND_WIDTH_DB = 5
TOP_BAND_DB = 75  # legend: "≥ 75"
LOWEST_BAND_DB = 50


def band_range(lower_db: int | None) -> tuple[int | None, int | None]:
    """Band lower bound -> (min, max) dB. None -> (None, 49); 75 -> (75, None)."""
    if lower_db is None:
        return None, LOWEST_BAND_DB - 1
    if lower_db >= TOP_BAND_DB:
        return lower_db, None
    return lower_db, lower_db + BAND_WIDTH_DB - 1


async def noise_at(client: httpx.AsyncClient, cache: Cache, lat: float, lon: float) -> NoiseLayer:
    """Loudest-source Lden and Lnight bands at the point, cached.

    Raises wms.WMSError if the service fails and there is no cached answer.
    """
    answer = await cached_fetch(
        cache,
        CACHE_NAMESPACE,
        lat,
        lon,
        lambda: wms.get_feature_info(
            client, ZG_BUKA_URL, LAYERS, lat, lon, property_names=PROPERTY_NAMES
        ),
    )
    bands = bands_from_features(answer.value)
    lden = loudest(bands, "Lden")
    lnight = loudest(bands, "Lnight")
    loudest_key = max((k for k in bands if k.endswith("_Lden")), key=bands.get, default=None)
    score = noise_score(lden)
    lden_min, lden_max = band_range(lden)
    lnight_min, lnight_max = band_range(lnight)
    return NoiseLayer(
        status=status(score),
        score=round(score),
        lden_db_min=lden_min,
        lden_db_max=lden_max,
        lnight_db_min=lnight_min,
        lnight_db_max=lnight_max,
        loudest_source=SOURCE_CODES[loudest_key.removesuffix("_Lden")] if loudest_key else None,
        source_id=SOURCE_ID,
        fetched_at=answer.fetched_at,
        stale=answer.stale,
    )
