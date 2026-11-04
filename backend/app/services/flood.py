"""Flood zone at a point from hv-poplave (Hrvatske vode, Karte opasnosti od poplava).

The WMS refuses GetFeatureInfo, so each probability scenario is rendered with GetMap and
the pixel colour at the point is read (app.services.wms.get_map_pixel). Opaque = inside
that scenario's flood extent; the colour encodes the depth class. See docs/data-sources.md.
"""

from app.services.ekoskor import FloodZone

HV_POPLAVE_URL = "https://servisi.voda.hr/poplave_opasnosti/wms"
SOURCE_ID = "hv-poplave"

# zone -> scenario word in the layer name, checked from highest to lowest probability
SCENARIOS: dict[FloodZone, str] = {"high": "velika", "medium": "srednja", "low": "mala"}

# Legend (GetLegendGraphic JSON, attribute m_kl_dub), titles as published. Interpretation
# of the depth classes is taken from the legend titles; flagged for a human to confirm.
DEPTH_CLASSES = {
    "#BEE8FF": "dubina < 0,5 m",
    "#73DFFF": "dubina 0,5–1,5 m",
    "#73B2FF": "dubina 1,5–2,5 m",
    "#7A8EF5": "dubina > 2,5 m",
}


def layer_name(zone: FloodZone) -> str:
    return f"hr.fd.opasnost-od-poplave-{SCENARIOS[zone]}-vjerojatnost"


def zone_from_colours(colours: dict[FloodZone, str | None]) -> FloodZone:
    """Highest-probability scenario whose layer is drawn at the point, else 'none'.

    `colours` maps zone -> '#RRGGBB' or None (transparent), one entry per scenario.
    """
    for zone in SCENARIOS:  # high, medium, low
        if colours.get(zone) is not None:
            return zone
    return "none"
