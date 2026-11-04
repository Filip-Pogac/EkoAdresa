"""Phase 0 reference points (docs/data-sources.md), shared by the tests and the recorder."""

FIXTURES_DIR_NAME = "wms"

# name -> (lat, lon), EPSG:4326
POINTS = {
    "savica": (45.7905, 15.9950),  # near the Sava, inside the low-probability flood zone
    "jelacic": (45.8131, 15.9772),  # Trg bana Jelačića, dense stops, central noise
    "sljeme": (45.8986, 15.9486),  # Sljeme, quiet, outside all zones
}
