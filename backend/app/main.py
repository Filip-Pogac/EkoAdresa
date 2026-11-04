import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health

app = FastAPI(
    title="EkoAdresa API",
    description="Okolišni profil adrese iz otvorenih podataka (Datathon 2026, izazov B).",
    version="0.1.0",
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
