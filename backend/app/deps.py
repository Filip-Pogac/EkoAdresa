"""FastAPI dependencies for resources created once at startup (see main.lifespan).

Tests override them: a MockTransport HTTP client and a temporary cache.
"""

import httpx2 as httpx
from fastapi import Request

from app.cache import Cache


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


def get_cache(request: Request) -> Cache:
    return request.app.state.cache
