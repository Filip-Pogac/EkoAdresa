import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2 as httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache import Cache
from app.http import USER_AGENT
from app.routers import geocode, health, profile
from app.services import geocode as geocode_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    geocode_service.warm_up()  # ~2 s at startup instead of on the first search
    app.state.cache = Cache()
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=10) as client:
        app.state.http = client  # one connection pool for all outgoing requests
        yield


app = FastAPI(
    title="EkoAdresa API",
    description="Okolišni profil adrese iz otvorenih podataka (Datathon 2026, izazov B).",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(geocode.router)
app.include_router(profile.router)
