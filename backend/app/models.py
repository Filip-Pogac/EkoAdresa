"""Pydantic request/response schemas. The frontend types in src/api mirror these."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


class GeocodeResult(BaseModel):
    label: str  # e.g. "Radnička cesta 80, 10114 Zagreb"
    lat: float  # EPSG:4326
    lon: float
    kind: Literal["address", "street", "place"]  # address = with house number


class GeocodeResponse(BaseModel):
    results: list[GeocodeResult]
    source_id: str


class NearestAddress(BaseModel):
    """What to call a point picked on the map: the nearest address, or else the named park
    or forest the point lies in."""

    kind: Literal["address", "green_area"]
    label: str  # e.g. "Ilica 25, 10000 Zagreb" or "Park šuma Maksimir"
    lat: float  # EPSG:4326: the address point; for a green area, the requested point
    lon: float
    distance_m: int  # straight line from the requested point; 0 for a green area
    source_id: str  # osm-adrese or osm-parkovi


class ReverseResponse(BaseModel):
    """Nearest address within geocode.REVERSE_MAX_M, else the named park or forest the point
    is in, else None."""

    result: NearestAddress | None
    source_id: str


Status = Literal["green", "yellow", "red", "unavailable"]
NoiseSource = Literal["road", "tram", "rail", "industry"]


class LayerBase(BaseModel):
    status: Status
    score: int  # EkoSkor sub-score 0-100
    source_id: str  # dataset the score is computed from


class RemoteLayer(LayerBase):
    """A layer read from a remote service through app.cache."""

    fetched_at: datetime  # UTC, when the remote service answered (may be older if cached)
    stale: bool  # True = the service failed just now; this is the last cached answer


class FloodLayer(RemoteLayer):
    zone: Literal["high", "medium", "low", "none"]
    depth_class: str | None  # legend title of the flood depth, e.g. "dubina 1,5–2,5 m"


class NoiseLayer(RemoteLayer):
    # 5 dB bands of the loudest source. min None = no mapped band (max 49: below 50 dB);
    # max None = top band (≥ 75 dB).
    lden_db_min: int | None
    lden_db_max: int | None
    lnight_db_min: int | None
    lnight_db_max: int | None
    loudest_source: NoiseSource | None  # source of the loudest Lden band
    # None = band read at the point. Otherwise the point had no band (inside a building
    # footprint) and the bands are the loudest found this many metres around it.
    facade_m: int | None


Pollutant = Literal["no2", "o3", "pm10", "pm2_5"]


class AirStation(BaseModel):
    id: str
    name: str
    station_type: str | None  # as published: "Prometna", "Pozadinska", "Industrijska"
    lat: float
    lon: float
    distance_m: int
    source_id: str  # zg-zrak-postaje


class AirValue(BaseModel):
    pollutant: Pollutant
    value_ug_m3: float
    date: date  # daily value


class LiveAirIndex(BaseModel):
    """National air quality index at the nearest national station (extra information)."""

    value: float
    measured_at: datetime
    distance_m: int
    scale_verified: bool  # False until the index scale is confirmed (docs/data-sources.md)
    source_id: str  # rh-zrak-indeks


class DhmzStation(BaseModel):
    name: str  # as published by DHMZ, e.g. "Zagreb 1"
    lat: float
    lon: float
    distance_m: int


class DhmzValue(BaseModel):
    pollutant: Pollutant
    mean_24h_ug_m3: float  # mean of the hourly values on the page (last 24 h)
    latest_ug_m3: float
    latest_at_local: str  # 'YYYY-MM-DDTHH:00', local time in Croatia, as on the page
    hours: int  # hourly values behind the mean (missing hours are skipped)


class DhmzReading(BaseModel):
    """Last 24 h at the nearest DHMZ state station: raw, unvalidated (extra information)."""

    station: DhmzStation
    values: list[DhmzValue]
    status: Status  # own status vs WHO 24 h guidelines (services/dhmz.py); not the layer's
    validated: bool  # always False: DHMZ marks these values as raw
    source_id: str  # dhmz-kvaliteta-zraka


class AirLayer(LayerBase):
    station: AirStation
    pm10_mean_ug_m3: float  # basis of the score
    period_from: date  # data period of the City measurements (2023)
    period_to: date
    latest: list[AirValue]  # last available day per pollutant
    history: list[AirValue]  # last 30 days of available data, all pollutants
    live_index: LiveAirIndex | None  # None if the national service did not answer in time
    dhmz: DhmzReading | None  # None if DHMZ did not answer in time; never scored


class Place(BaseModel):
    """A point of interest near the address, with its straight-line distance."""

    name: str | None
    lat: float
    lon: float
    distance_m: int
    source_id: str


class RecyclingYard(Place):
    address: str | None
    opening_hours: str | None  # as published (2022 data)


class GreenIsland(Place):
    accepts: list[str]  # e.g. ["glass", "paper", "plastic"]


class WasteLayer(LayerBase):
    yard: RecyclingYard  # nearest fixed yard (scored)
    mobile_yard: RecyclingYard  # nearest mobile yard: extra information, not scored
    island: GreenIsland
    yard_distance_m: int
    island_distance_m: int


class Stop(Place):
    type: Literal["bus", "tram"]
    direction: str | None
    lines: list[str]


class BikePath(Place):
    """Nearest City bike path; lat/lon is the nearest point on it."""

    category: str | None  # kategorija_id as published, TODO(verify): codes not documented


class BikeStation(Place):
    """Nearest public bike station (sustav javnih bicikala, Grad Zagreb)."""

    location: str | None  # address as published
    racks: int | None  # number of bike racks


class GreenArea(Place):
    """Nearest park, forest, public garden or nature reserve of at least 0.5 ha; lat/lon is
    the nearest point of its outline, distance 0 if the address is inside it."""

    kind: Literal["park", "forest"]
    area_m2: int


class MobilityLayer(LayerBase):
    """Score = 4/5 transit + 1/5 bike, bike = the nearer of bike path and bike station
    (services/ekoskor.py)."""

    stops_300m: int  # ZET platforms (one per stop and direction)
    stops_500m: int
    nearest_stop: Stop
    nearest_bike_path: BikePath
    nearest_bike_station: BikeStation  # extra for the bike part: the nearer of the two counts
    transit_score: int  # parts of the score, 0-100 each
    bike_score: int


class GreenLayer(LayerBase):
    """Zelenilo: nearest park or forest of at least 0.5 ha (services/green.py)."""

    nearest: GreenArea


class UnavailableLayer(BaseModel):
    """A layer that could not be computed; the rest of the profile is still returned."""

    status: Literal["unavailable"]
    reason: Literal["timeout", "error"]
    source_id: str


class Layers(BaseModel):
    flood: FloodLayer | UnavailableLayer
    noise: NoiseLayer | UnavailableLayer
    air: AirLayer | UnavailableLayer
    waste: WasteLayer | UnavailableLayer
    mobility: MobilityLayer | UnavailableLayer
    green: GreenLayer | UnavailableLayer


class Location(BaseModel):
    lat: float  # EPSG:4326
    lon: float
    address: str | None  # label passed by the client, echoed back, never stored


class Profile(BaseModel):
    location: Location
    ekoskor: int | None  # None if fewer than 3 layers are available
    layers: Layers
    generated_at: datetime


LayerName = Literal["flood", "noise", "air", "waste", "mobility", "green"]


class LayerDiff(BaseModel):
    score_a: int | None  # None = layer unavailable for that address
    score_b: int | None
    better: Literal["a", "b"] | None  # None = equal sub-scores, or a layer is unavailable


class Comparison(BaseModel):
    a: Profile
    b: Profile
    ekoskor_diff: int | None  # b - a; None if either EkoSkor is missing
    layers: dict[LayerName, LayerDiff]


class Source(BaseModel):
    """One dataset or service, as registered in app.sources and docs/data-sources.md."""

    id: str
    name: str  # dataset title as published
    publisher: str
    access: Literal["live", "snapshot"]  # live = queried per request; snapshot = committed file
    urls: list[str]  # catalogue page or service endpoint
    licence: str | None  # exactly as stated by the publisher; None = no licence stated
    data_as_of: str  # data period or last update, as stated or observed
    used_for: str  # Croatian, shown on the "Izvori podataka" page
