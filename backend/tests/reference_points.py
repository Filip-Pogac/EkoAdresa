"""Phase 0 reference points and the WMS layers queried for them (docs/data-sources.md)."""

FIXTURES_DIR_NAME = "wms"

# name -> (lat, lon), EPSG:4326
POINTS = {
    "savica": (45.7905, 15.9950),  # near the Sava, inside the low-probability flood zone
    "jelacic": (45.8131, 15.9772),  # Trg bana Jelačića, dense stops, central noise
    "sljeme": (45.8986, 15.9486),  # Sljeme, quiet, outside all zones
}

HV_POPLAVE_URL = "https://servisi.voda.hr/poplave_opasnosti/wms"
FLOOD_SCENARIOS = ("velika", "srednja", "mala")  # high, medium, low probability


def flood_layer(scenario: str) -> str:
    return f"hr.fd.opasnost-od-poplave-{scenario}-vjerojatnost"


ZG_BUKA_URL = "https://geoportal.zagreb.hr/Public/StrategijskoPlaniranje_Public/MapServer/WMSServer"
NOISE_LAYERS = [
    f"SKB_R4_{source}_{indicator}"
    for source in (
        "Cestovni_promet",
        "Tramvajski_promet",
        "Zeljeznicki_promet",
        "Industrijski_pogon",
    )
    for indicator in ("Lden", "Lnight")
]
NOISE_PROPERTIES = ["razina"]  # lower bound of the 5 dB band; geometry not needed
