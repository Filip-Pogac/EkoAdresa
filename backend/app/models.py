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


class AirLayer(LayerBase):
    station: AirStation
    pm10_mean_ug_m3: float  # basis of the score
    period_from: date  # data period of the City measurements (2023)
    period_to: date
    latest: list[AirValue]  # last available day per pollutant
    history: list[AirValue]  # last 30 days of available data, all pollutants
    live_index: LiveAirIndex | None  # None if the national service did not answer in time


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


class MobilityLayer(LayerBase):
    stops_300m: int  # ZET platforms (one per stop and direction)
    stops_500m: int
    nearest_stop: Stop


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


class Location(BaseModel):
    lat: float  # EPSG:4326
    lon: float
    address: str | None  # label passed by the client, echoed back, never stored


class Profile(BaseModel):
    location: Location
    ekoskor: int | None  # None if fewer than 3 layers are available
    layers: Layers
    generated_at: datetime
