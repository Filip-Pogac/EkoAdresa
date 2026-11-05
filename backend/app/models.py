"""Pydantic request/response schemas. The frontend types in src/api mirror these."""

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
