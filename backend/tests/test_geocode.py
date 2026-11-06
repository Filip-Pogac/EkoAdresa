"""GET /api/geocode against the committed address snapshot (data/addresses.parquet).

The addresses used here are well-mapped landmarks; if a fresh OSM fetch ever drops one,
pick another rather than loosening the assertion.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.geocode import normalise

api = TestClient(app)


def search(q: str, **params: object) -> list[tuple[str, str]]:
    resp = api.get("/api/geocode", params={"q": q, **params})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_id"] == "osm-adrese"
    return [(r["label"], r["kind"]) for r in body["results"]]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Đorđićeva ulica", "dordiceva ulica"),
        ("Trg bana Jelačića", "trg bana jelacica"),
        ("ŠKOLSKA, Žitnjak", "skolska zitnjak"),
        ("Ilica 10/1", "ilica 10/1"),
        ("Savica I.", "savica i"),
    ],
)
def test_normalise(text: str, expected: str) -> None:
    assert normalise(text) == expected


def test_full_address() -> None:
    assert search("Radnička cesta 80")[0] == ("Radnička cesta 80, 10000 Zagreb", "address")


def test_accent_insensitive_and_partial_words() -> None:
    assert search("radnicka 80")[0] == ("Radnička cesta 80, 10000 Zagreb", "address")
    assert search("Dordiceva")[0][0].startswith("Đorđićeva ulica")


def test_words_in_any_order_and_partial() -> None:
    label, kind = search("Trg bana Jel")[0]
    assert label.startswith("Trg bana Josipa Jelačića,")
    assert kind == "street"


def test_house_numbers_in_natural_order() -> None:
    numbers = [label.split(",")[0].removeprefix("Ilica ") for label, _ in search("Ilica 1")]
    assert numbers[0] == "1"  # exact number first
    assert all(n.startswith("1") for n in numbers)
    assert "10" in numbers and numbers.index("1A") < numbers.index("10")


def test_unknown_house_number_falls_back_to_street() -> None:
    assert search("Ilica 99999")[0] == ("Ilica, 10000 Zagreb", "street")


def test_same_street_name_in_two_parts_of_the_city() -> None:
    labels = [label for label, _ in search("Bistrička")]
    assert "Bistrička ulica, 10000 Zagreb" in labels
    assert "Bistrička ulica, 10360 Sesvete" in labels


def test_named_place_first_on_exact_match() -> None:
    assert search("Savica")[0] == ("Savica, 10000 Zagreb", "place")


def test_outside_the_pilot_area() -> None:
    assert search("Split") == []


def test_limit() -> None:
    assert len(search("Ilica 1", limit=2)) == 2


@pytest.mark.parametrize("q", ["Il", "x" * 101])
def test_query_length_validated(q: str) -> None:
    assert api.get("/api/geocode", params={"q": q}).status_code == 422


def reverse(lat: float, lon: float) -> dict:
    resp = api.get("/api/reverse", params={"lat": lat, "lon": lon})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_id"] == "osm-adrese"
    return body["result"]


def test_reverse_nearest_address() -> None:
    # A click 35 m from Trg bana Josipa Jelačića 6 (example address)
    result = reverse(45.8131, 15.9772)
    assert result["label"] == "Trg bana Josipa Jelačića 6, 10000 Zagreb"
    assert result["distance_m"] == 35


def test_reverse_exact_point_is_0_m() -> None:
    result = reverse(45.790284, 15.994318)
    assert result["label"] == "Ulica Vladimira Ruždjaka 20, 10000 Zagreb"
    assert result["distance_m"] == 0


def test_reverse_nothing_within_150_m() -> None:
    assert reverse(45.8305, 16.0217) is None  # middle of Park-šuma Maksimir
    assert reverse(45.7850, 15.9900) is None  # the Sava


def test_reverse_validates_coordinates() -> None:
    assert api.get("/api/reverse", params={"lat": 91, "lon": 16}).status_code == 422
