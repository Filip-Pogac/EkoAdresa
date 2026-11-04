"""Pydantic request/response schemas. The frontend types in src/api mirror these."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
