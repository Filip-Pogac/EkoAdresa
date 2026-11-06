"""Address search for the autocomplete box, over a local snapshot of OpenStreetMap addresses.

Data: data/addresses.parquet (scripts/fetch_addresses.py, source osm-adrese), City of
Zagreb only (pilot area). No external service at runtime: Nominatim's usage policy forbids
autocomplete, and the public Photon server throttled us during testing (2026-11-05).
Nothing a user types is stored or logged (CLAUDE.md §2.7).

Matching: accent-insensitive ("jelacica" finds "Jelačića"); every typed word must be the
start of a word in the name, in any order ("trg bana jel" finds "Trg bana Josipa
Jelačića"). If the last typed word starts with a digit and follows a word, it is a house
number ("ilica 1" lists Ilica 1, 1A, 10, 11…).

Reverse: `nearest` gives the closest address to a point picked on the map, if one is within
REVERSE_MAX_M (straight line, EPSG:3765). The point itself is not stored or logged.
"""

import re
import unicodedata
from dataclasses import dataclass
from functools import cache

import numpy as np
import pandas as pd

from app.models import GeocodeResult, NearestAddress
from app.paths import DATA_DIR
from app.services.geo import distances_m, project

SOURCE_ID = "osm-adrese"
DATA_FILE = "addresses.parquet"
_NOT_WORD = re.compile(r"[^0-9a-z/]+")
REVERSE_MAX_M = 150  # farther than this, the map point keeps its generic title


def normalise(text: str) -> str:
    """'Đorđićeva ulica 10/1' -> 'dordiceva ulica 10/1' (đ has no Unicode decomposition)."""
    text = text.lower().replace("đ", "d")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return " ".join(_NOT_WORD.sub(" ", text).split())


@dataclass(frozen=True)
class _Entry:
    kind: str  # "street" | "place"
    name: str
    words: tuple[str, ...]
    town: str  # "10000 Zagreb", "Sesvete", ...
    lat: float
    lon: float
    size: int  # number of addresses (ranking: well-mapped streets first)
    street_id: int


@dataclass(frozen=True)
class _Index:
    entries: list[_Entry]
    houses: dict[int, list[tuple[str, str, float, float]]]  # street_id -> (number, key, lat, lon)
    labels: list[str]  # every address as "Street 12, 10000 Zagreb", aligned with xy
    lonlat: np.ndarray  # (n, 2) EPSG:4326
    xy: np.ndarray  # (n, 2) EPSG:3765 metres


def _natural_key(number: str) -> tuple[int, str]:
    digits = re.match(r"\d+", number)
    return (int(digits.group()) if digits else 10**9, number)


def _town(postcode: object, city: object) -> str:
    return " ".join(x for x in (postcode, city) if isinstance(x, str))


@cache
def _index() -> _Index:
    df = pd.read_parquet(DATA_DIR / DATA_FILE)
    entries: list[_Entry] = []
    houses: dict[int, list[tuple[str, str, float, float]]] = {}

    for street_id, group in df[df["kind"] == "address"].groupby("street_id"):
        # Representative point: the address closest to the street's median position
        d2 = (group["lat"] - group["lat"].median()) ** 2 + (
            group["lon"] - group["lon"].median()
        ) ** 2
        rep = group.iloc[int(np.argmin(d2.to_numpy()))]
        sid = int(street_id)  # type: ignore[arg-type]
        entries.append(
            _Entry(
                kind="street",
                name=rep["name"],
                words=tuple(normalise(rep["name"]).split()),
                town=_town(rep["postcode"], rep["city"]),
                lat=float(rep["lat"]),
                lon=float(rep["lon"]),
                size=len(group),
                street_id=sid,
            )
        )
        numbers = zip(group["housenumber"], group["lat"], group["lon"], strict=True)
        houses[sid] = sorted(
            ((h, normalise(h), float(la), float(lo)) for h, la, lo in numbers),
            key=lambda item: _natural_key(item[1]),
        )

    addresses = df[df["kind"] == "address"]
    labels = [
        f"{name} {number}, {town}" if (town := _town(pc, city)) else f"{name} {number}"
        for name, number, pc, city in zip(
            addresses["name"], addresses["housenumber"], addresses["postcode"],
            addresses["city"], strict=True,
        )
    ]  # fmt: skip
    lonlat = addresses[["lon", "lat"]].to_numpy(dtype=float)
    xy = project(lonlat[:, 0], lonlat[:, 1])

    places = df[df["kind"] == "place"]
    for name, postcode, city, lat, lon in zip(
        places["name"], places["postcode"], places["city"], places["lat"], places["lon"],
        strict=True,
    ):  # fmt: skip
        entries.append(
            _Entry(
                kind="place",
                name=name,
                words=tuple(normalise(name).split()),
                town=_town(postcode, city),
                lat=float(lat),
                lon=float(lon),
                size=0,
                street_id=-1,
            )
        )
    return _Index(entries, houses, labels, lonlat, xy)


def warm_up() -> None:
    """Load the address index now (called at app startup)."""
    _index()


def _matches(entry: _Entry, words: list[str]) -> bool:
    return all(any(w.startswith(q) for w in entry.words) for q in words)


def _rank(entry: _Entry, words: list[str]) -> tuple[bool, bool, int, str]:
    return (
        entry.words != tuple(words),  # exact name first ("Savica" the place)
        not entry.words[0].startswith(words[0]),  # then names starting with the first word
        -entry.size,  # then streets with more mapped addresses
        entry.name,
    )


def _result(kind: str, main: str, entry: _Entry, lat: float, lon: float) -> GeocodeResult:
    label = f"{main}, {entry.town}" if entry.town else main
    return GeocodeResult(label=label, lat=lat, lon=lon, kind=kind)  # type: ignore[arg-type]


def search(query: str, limit: int) -> list[GeocodeResult]:
    tokens = normalise(query).split()
    if not tokens:
        return []
    number = tokens[-1] if len(tokens) > 1 and tokens[-1][0].isdigit() else None
    words = tokens[:-1] if number else tokens

    index = _index()
    found = sorted((e for e in index.entries if _matches(e, words)), key=lambda e: _rank(e, words))
    if number:
        results: list[GeocodeResult] = []
        for entry in found:
            if entry.kind != "street":
                continue
            hits = [h for h in index.houses[entry.street_id] if h[1].startswith(number)]
            hits.sort(key=lambda h: h[1] != number)  # exact number first, natural order kept
            results += [_result("address", f"{entry.name} {h[0]}", entry, h[2], h[3]) for h in hits]
            if len(results) >= limit:
                return results[:limit]
        if results:
            return results
        # No such house number in the data: offer the street itself (below)
    return [_result(e.kind, e.name, e, e.lat, e.lon) for e in found[:limit]]


def nearest(lat: float, lon: float) -> NearestAddress | None:
    """Closest address to (lat, lon), or None if none is within REVERSE_MAX_M."""
    index = _index()
    d = distances_m(index.xy, lat, lon)
    i = int(np.argmin(d))
    if d[i] > REVERSE_MAX_M:
        return None
    a_lon, a_lat = index.lonlat[i]
    return NearestAddress(
        label=index.labels[i], lat=float(a_lat), lon=float(a_lon), distance_m=round(float(d[i]))
    )
