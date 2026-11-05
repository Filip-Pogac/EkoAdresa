"""SQLite cache for slow / flaky remote point queries (WMS today, WFS later).

Key = (namespace, lat, lon) with coordinates rounded to 4 decimals (~11 m x 8 m in Zagreb).
Only rounded coordinates are stored, never the typed address (CLAUDE.md §2.7).

If a fetch fails and an expired entry exists, that entry is served with `stale=True` and
its `fetched_at`, so a service outage does not blank a layer and the UI can show the date.
"""

import json
import logging
import os
import sqlite3
import time
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

log = logging.getLogger(__name__)
T = TypeVar("T")

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "cache" / "remote.sqlite"
# hv-poplave and zg-buka are static map datasets; 30 days only bounds how long we go
# without noticing a republished map.
DEFAULT_TTL_S = 30 * 24 * 3600
# On Vercel (which sets VERCEL=1) only /tmp is writable, and it is wiped when a new
# instance starts; data/cache_seed.json refills the demo addresses (Cache.load_seed).
VERCEL_PATH = Path("/tmp/ekoadresa/remote.sqlite")


def _default_path() -> Path:
    return VERCEL_PATH if os.getenv("VERCEL") else DEFAULT_PATH


@dataclass(frozen=True)
class Cached(Generic[T]):
    value: T
    fetched_at: datetime  # UTC, when the value was fetched from the remote service
    stale: bool  # True = fetch just failed, this is an expired entry served as fallback


class Cache:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path or os.getenv("CACHE_PATH") or _default_path())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS entries ("
                " namespace TEXT NOT NULL, lat TEXT NOT NULL, lon TEXT NOT NULL,"
                " value TEXT NOT NULL, fetched_at REAL NOT NULL,"
                " PRIMARY KEY (namespace, lat, lon))"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        # One short-lived connection per operation: safe across threads/tasks, and each
        # query is sub-millisecond, so blocking the event loop is not a concern here.
        # (`with sqlite3.connect()` alone commits but never closes the connection.)
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _key(namespace: str, lat: float, lon: float) -> tuple[str, str, str]:
        return (namespace, f"{lat:.4f}", f"{lon:.4f}")

    def get(self, namespace: str, lat: float, lon: float) -> tuple[Any, float] | None:
        """(value, fetched_at epoch s) or None on a miss. A stored None is a hit."""
        with self._connect() as db:
            row = db.execute(
                "SELECT value, fetched_at FROM entries WHERE namespace=? AND lat=? AND lon=?",
                self._key(namespace, lat, lon),
            ).fetchone()
        return None if row is None else (json.loads(row[0]), row[1])

    def set(self, namespace: str, lat: float, lon: float, value: Any, fetched_at: float) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, ?)",
                (*self._key(namespace, lat, lon), json.dumps(value), fetched_at),
            )

    def export(self) -> list[dict]:
        """All entries as JSON-ready dicts (rounded coordinates only, no addresses)."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT namespace, lat, lon, value, fetched_at FROM entries"
                " ORDER BY namespace, lat, lon"
            ).fetchall()
        return [
            {"namespace": n, "lat": la, "lon": lo, "value": json.loads(v), "fetched_at": f}
            for n, la, lo, v, f in rows
        ]

    def load_seed(self, path: Path) -> int:
        """Add entries from a seed file (Cache.export format) that are not cached yet.

        The committed seed (data/cache_seed.json, scripts/warm_cache.py) keeps the demo
        addresses fast and working when a public service is down, also on hosts whose
        disk is wiped between instances (CLAUDE.md §3.11). Returns the number added.
        """
        if not path.exists():
            return 0
        added = 0
        with self._connect() as db:
            for e in json.loads(path.read_text(encoding="utf-8")):
                cur = db.execute(
                    "INSERT OR IGNORE INTO entries VALUES (?, ?, ?, ?, ?)",
                    (e["namespace"], e["lat"], e["lon"], json.dumps(e["value"]), e["fetched_at"]),
                )
                added += cur.rowcount
        return added


async def cached_fetch(
    cache: Cache,
    namespace: str,
    lat: float,
    lon: float,
    fetch: Callable[[], Awaitable[T]],
    ttl_s: float = DEFAULT_TTL_S,
    now: Callable[[], float] = time.time,
) -> Cached[T]:
    """Fresh cache hit, else fetch and store; on fetch failure fall back to a stale entry.

    Re-raises the fetch error when there is nothing cached to fall back to. `value` must be
    JSON-serialisable.
    """
    hit = cache.get(namespace, lat, lon)
    if hit is not None and now() - hit[1] < ttl_s:
        return Cached(hit[0], datetime.fromtimestamp(hit[1], UTC), stale=False)

    try:
        value = await fetch()
    except Exception:
        if hit is None:
            raise
        log.warning("fetch failed for %s, serving stale cache entry", namespace)
        return Cached(hit[0], datetime.fromtimestamp(hit[1], UTC), stale=True)

    fetched_at = now()
    cache.set(namespace, lat, lon, value, fetched_at)
    return Cached(value, datetime.fromtimestamp(fetched_at, UTC), stale=False)
