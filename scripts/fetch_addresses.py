"""Addresses and named places in the City of Zagreb (OpenStreetMap) -> data/addresses.parquet.

Source osm-adrese (see docs/data-sources.md): Overpass, everything with addr:street +
addr:housenumber, plus place=suburb|quarter|neighbourhood|locality|hamlet|village nodes,
inside ISO 3166-2 HR-21. Ways and relations are reduced to their centre point.

Streets: OSM has only street names, and some names exist in several parts of the City
(merged former municipalities). Addresses with the same street name are grouped into one
street when they are within 1 km of each other (single linkage); each group gets the most
common postcode and city of its addresses (only ~36 % of addresses carry a postcode).

Output columns: kind (address|place), name (street or place name), housenumber, postcode,
city, lat, lon (EPSG:4326), street_id (group id, -1 for places), source_id.

Run from the repo root:  uv run --project backend python scripts/fetch_addresses.py
"""

import json
import logging
import time
from collections import Counter
from pathlib import Path

import httpx2 as httpx
import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw" / "osm_addresses.json"
OUT_PATH = ROOT / "data" / "addresses.parquet"

USER_AGENT = "EkoAdresa/0.1 (+https://github.com/Filip-Pogac/EkoAdresa)"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
QUERY = (
    "[out:json][timeout:240];"
    'area["ISO3166-2"="HR-21"]["admin_level"]->.zg;'
    '(nwr["addr:housenumber"]["addr:street"](area.zg);'
    'node["place"~"^(suburb|quarter|neighbourhood|locality|hamlet|village)$"]["name"](area.zg););'
    "out center tags;"
)
SAME_STREET_M = 1000
DEFAULT_CITY = "Zagreb"

to_htrs = Transformer.from_crs("EPSG:4326", "EPSG:3765", always_xy=True)  # metres
log = logging.getLogger("fetch_addresses")


def download() -> dict:
    """Overpass answer, cached in data/raw (delete the file to fetch fresh OSM data)."""
    if RAW_PATH.exists():
        return json.loads(RAW_PATH.read_bytes())
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=300) as client:
        for attempt in range(1, 6):
            for url in OVERPASS_URLS:
                try:
                    resp = client.post(url, data={"data": QUERY})
                    if resp.status_code == 200:
                        RAW_PATH.write_bytes(resp.content)
                        return resp.json()
                    log.warning("%s -> HTTP %s (attempt %d)", url, resp.status_code, attempt)
                except httpx.HTTPError as exc:
                    log.warning("%s -> %s (attempt %d)", url, exc, attempt)
            time.sleep(10 * attempt)
    raise RuntimeError("all Overpass endpoints failed")


def clean(value: str | None) -> str | None:
    text = " ".join(value.split()) if value else ""
    return text or None


def street_groups(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Single-linkage groups of points closer than SAME_STREET_M (union-find)."""
    parent = list(range(len(x)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    d = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
    for i, j in zip(*np.nonzero(np.triu(d < SAME_STREET_M, k=1)), strict=True):
        parent[find(i)] = find(j)
    return np.array([find(i) for i in range(len(x))])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = download()
    osm_timestamp = payload["osm3s"]["timestamp_osm_base"]

    rows = []
    for el in payload["elements"]:
        tags = el.get("tags", {})
        lat = el.get("lat", el.get("center", {}).get("lat"))
        lon = el.get("lon", el.get("center", {}).get("lon"))
        if lat is None:
            continue
        if "addr:housenumber" in tags:
            rows.append(
                {
                    "kind": "address",
                    "name": clean(tags["addr:street"]),
                    "housenumber": clean(tags["addr:housenumber"]),
                    "postcode": clean(tags.get("addr:postcode")),
                    "city": clean(tags.get("addr:city")),
                    "lat": lat,
                    "lon": lon,
                }
            )
        else:
            rows.append({"kind": "place", "name": clean(tags["name"]), "lat": lat, "lon": lon})
    df = pd.DataFrame(rows)
    df = df[df["name"].notna()].reset_index(drop=True)
    x, y = to_htrs.transform(df["lon"].to_numpy(), df["lat"].to_numpy())

    df["street_id"] = -1
    addresses = df["kind"] == "address"
    next_id = 0
    for _, idx in df[addresses].groupby("name").groups.items():
        idx = np.asarray(idx)
        groups = street_groups(x[idx], y[idx])
        for g in np.unique(groups):
            members = idx[groups == g]
            df.loc[members, "street_id"] = next_id
            # dropna, not `if p`: missing values are NaN, and NaN is truthy
            postcodes = Counter(df.loc[members, "postcode"].dropna())
            cities = Counter(df.loc[members, "city"].dropna())
            df.loc[members, "postcode"] = postcodes.most_common(1)[0][0] if postcodes else None
            df.loc[members, "city"] = cities.most_common(1)[0][0] if cities else DEFAULT_CITY
            next_id += 1

    # Places: postcode and city of the nearest address
    addr_xy = np.column_stack([x[addresses], y[addresses]])
    for i in np.nonzero(~addresses.to_numpy())[0]:
        nearest = np.argmin(np.hypot(*(addr_xy - [x[i], y[i]]).T))
        df.loc[i, ["postcode", "city"]] = df[addresses].iloc[nearest][["postcode", "city"]].values

    # A building mapped both as node and as way: keep one row per street and number
    before = len(df)
    df = df.drop_duplicates(subset=["kind", "name", "housenumber", "street_id"], keep="first")
    df["lat"], df["lon"] = df["lat"].round(6), df["lon"].round(6)
    df["source_id"] = "osm-adrese"
    df = df.sort_values(["kind", "name", "street_id", "housenumber"], ignore_index=True)
    df.to_parquet(OUT_PATH, index=False)

    n_addr = int((df["kind"] == "address").sum())
    log.info(
        "wrote %s: %d addresses on %d streets (%d duplicates dropped), %d places; OSM as of %s",
        OUT_PATH.relative_to(ROOT),
        n_addr,
        df.loc[df["kind"] == "address", "street_id"].nunique(),
        before - len(df),
        int((df["kind"] == "place").sum()),
        osm_timestamp,
    )
    (OUT_PATH.with_suffix(".meta.json")).write_text(
        json.dumps({"source_id": "osm-adrese", "osm_data_as_of": osm_timestamp, "query": QUERY})
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
