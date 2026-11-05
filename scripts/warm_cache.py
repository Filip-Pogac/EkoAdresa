"""Pre-warm the remote-service cache for the demo addresses -> data/cache_seed.json.

Computes the full profile (flood, noise incl. façade rings, air) for each demo address
through the normal services, then exports the cache entries. The backend loads the seed
at startup (app.cache.Cache.load_seed), so the demo addresses answer instantly and still
work if a public map service is down, also on hosts with a temporary disk (Vercel).
The seed holds only rounded coordinates and the services' answers, no typed addresses.

Run from the repo root:  uv run --project backend python scripts/warm_cache.py
"""

import asyncio
import json
import logging
import sys
import tempfile
from pathlib import Path

import httpx2 as httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.cache import Cache  # noqa: E402
from app.http import USER_AGENT  # noqa: E402
from app.services import geocode  # noqa: E402
from app.services.profile import build_profile  # noqa: E402

OUT_PATH = ROOT / "data" / "cache_seed.json"
# Demo and test addresses (PLAN.md Phase 6): centre, Savica, Sljeme, Novi Zagreb, Sesvete,
# Dubrava, Maksimir, Trnje, Jarun, Špansko, Črnomerec, Remetinec, Gajnice, Kozari bok
DEMO_QUERIES = [
    "Trg bana Josipa Jelačića 6",
    "Ulica Vladimira Ruždjaka 20",
    "Sljemenska cesta 8",
    "Ilica 10",
    "Avenija Dubrovnik 15",
    "Maksimirska cesta 51",
    "Sesvete",
    "Dubrava",
    "Vrbik 5",
    "Savska cesta 41",
    "Ulica grada Vukovara 11",
    "Jarun",
    "Špansko",
    "Trnje",
    "Črnomerec",
    "Remetinec",
    "Gajnice",
    "Kozari bok",
]
# Live index for air: 1 h cache shared by all addresses, not worth seeding
SKIP_NAMESPACE_PREFIXES = ("rh-zrak-indeks",)

log = logging.getLogger("warm_cache")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)  # request URLs: too verbose
    with tempfile.TemporaryDirectory() as tmp:
        cache = Cache(Path(tmp) / "warm.sqlite")
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=20) as client:
            for query in DEMO_QUERIES:
                results = geocode.search(query, 1)
                if not results:
                    log.warning("not found: %s", query)
                    continue
                r = results[0]
                profile = await build_profile(client, cache, r.lat, r.lon, None)
                missing = [n for n, layer in profile.layers if layer.status == "unavailable"]
                log.info("%-40s EkoSkor %s %s", r.label, profile.ekoskor,
                         f"unavailable: {missing}" if missing else "")  # fmt: skip
        entries = [
            e for e in cache.export() if not e["namespace"].startswith(SKIP_NAMESPACE_PREFIXES)
        ]
    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    log.info("%d cache entries -> %s", len(entries), OUT_PATH.relative_to(ROOT))


if __name__ == "__main__":
    asyncio.run(main())
