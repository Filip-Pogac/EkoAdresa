import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import geocode, health
from app.services import geocode as geocode_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    geocode_service.warm_up()  # ~2 s at startup instead of on the first search
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
