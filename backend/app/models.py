"""Pydantic request/response schemas. The frontend types in src/api mirror these."""

from datetime import datetime
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


class RemoteLayer(BaseModel):
    """Fields shared by layers read from a remote service through app.cache."""

    status: Status
    score: int  # EkoSkor sub-score 0-100
    source_id: str
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
