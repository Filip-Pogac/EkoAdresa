"""Every source_id the app emits is registered in app.sources and in docs/data-sources.md."""

import json
import re

from fastapi.testclient import TestClient

from app.main import app
from app.paths import DATA_DIR
from app.services import air, dhmz, flood, geocode, mobility, noise
from app.sources import SOURCES

ROOT = DATA_DIR.parent


def emitted_source_ids() -> set[str]:
    ids = {flood.SOURCE_ID, noise.SOURCE_ID, air.SOURCE_ID, air.STATIONS_SOURCE_ID,
           air.LIVE_SOURCE_ID, mobility.SOURCE_ID, geocode.SOURCE_ID,
           dhmz.SOURCE_ID}  # fmt: skip
    for path in DATA_DIR.glob("*.geojson"):
        data = json.loads(path.read_text(encoding="utf-8"))
        ids.update(data.get("metadata", {}).get("sources", []))
        for feature in data["features"]:
            ids.update(v for k, v in feature["properties"].items() if k.endswith("source_id"))
    return ids


def test_every_emitted_source_is_registered() -> None:
    assert emitted_source_ids() - SOURCES.keys() == set()


def test_registry_has_no_unused_sources() -> None:
    assert SOURCES.keys() - emitted_source_ids() == set()


def test_every_source_is_in_the_docs() -> None:
    summary = (ROOT / "docs" / "data-sources.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"^\| `([a-z0-9-]+)`", summary, flags=re.MULTILINE))
    assert SOURCES.keys() - documented == set()


def test_entries_are_complete() -> None:
    for source in SOURCES.values():
        assert source.urls and all(u.startswith("https://") for u in source.urls), source.id
        assert "TODO" not in source.model_dump_json(), source.id  # shown to users as is


def test_api_lists_sources() -> None:
    body = TestClient(app).get("/api/sources").json()
    assert [s["id"] for s in body] == list(SOURCES)
    by_id = {s["id"]: s for s in body}
    assert by_id["hv-poplave"]["licence"] is None  # none stated: never claim one
    assert by_id["zg-zet"]["licence"] == "Otvorena dozvola (OD)"
