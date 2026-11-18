"""Unit tests: run with `python -m pytest -q`."""

import pytest

from burger_atlas.store import CuratedPlace, Favorite, parse_favorites
from burger_atlas.geo import assign_district, get_city, haversine_m, load_categories
from burger_atlas.maps.component import directions_url
from burger_atlas.maps.engines import ComplianceError, GoogleMapEngine, LeafletDemoEngine, assert_compliant
from burger_atlas.models import LatLng, Restaurant, SearchFilters
from burger_atlas.providers import DemoProvider, ProviderQuery
from burger_atlas.providers.google_places import build_search_body, parse_place
from burger_atlas.services.discovery import build_query, discover, weighted_score

CITY = get_city("iloilo-city")


def test_city_config_has_seven_districts():
    assert len(CITY.districts) == 7
    assert {d.slug for d in CITY.districts} == {
        "city-proper", "jaro", "la-paz", "lapuz", "mandurriao", "molo", "arevalo"}


def test_categories_load():
    assert {c.slug for c in load_categories()} >= {"smash-classic", "plant-based"}


def test_haversine_reasonable():
    d = haversine_m(LatLng(10.6960, 122.5690), LatLng(10.7280, 122.5590))
    assert 3000 < d < 4500


def test_district_alias_beats_distance():
    # Located near Molo's centre but the address says La Paz.
    assert assign_district(CITY, "Some St, La Paz, Iloilo City", LatLng(10.6970, 122.5450)) == "la-paz"
    assert assign_district(CITY, "", LatLng(10.6970, 122.5450)) == "molo"
    assert assign_district(CITY, "", LatLng(11.5, 123.5)) is None


def test_compliance_guard_blocks_google_content_on_leaflet():
    g = Restaurant(id="ChIJabc", name="X", source="google", location=LatLng(10.7, 122.56))
    with pytest.raises(ComplianceError):
        assert_compliant(LeafletDemoEngine(), [g])
    assert_compliant(GoogleMapEngine("k"), [g])  # fine


def test_parse_place_and_attributions():
    r = parse_place({
        "id": "ChIJ123", "displayName": {"text": "Test Burgers"},
        "location": {"latitude": 10.7, "longitude": 122.56}, "rating": 4.5, "userRatingCount": 10,
        "priceLevel": "PRICE_LEVEL_MODERATE",
        "photos": [{"name": "places/ChIJ123/photos/abc", "authorAttributions": [{"displayName": "Ana", "uri": "https://x"}]}],
    })
    assert r.price_level == 2 and r.source == "google"
    assert r.photos[0].attributions[0].name == "Ana"


def test_search_body_restricts_to_rectangle():
    body = build_search_body(ProviderQuery(text="burger", restrict_to=CITY.bounds, min_rating=4.3))
    assert "rectangle" in body["locationRestriction"]
    assert body["minRating"] == 4.5  # rounded to API's 0.5 steps


def test_single_city_wide_query_regardless_of_filters():
    q = build_query(CITY, 2)
    assert q.restrict_to == CITY.bounds and q.max_pages == 2 and not q.min_rating


def test_discover_demo_filters_and_distance():
    p = DemoProvider()
    assert len(discover(p, CITY, SearchFilters(CITY.slug)).restaurants) == 16
    jaro = discover(p, CITY, SearchFilters(CITY.slug, districts=["jaro"])).restaurants
    assert jaro and all(r.district_slug == "jaro" for r in jaro)
    near = discover(p, CITY, SearchFilters(CITY.slug, origin=LatLng(10.7246, 122.5583),
                                                radius_m=1000, sort="distance")).restaurants
    assert near and all(r.distance_m <= 1000 for r in near)
    assert near == sorted(near, key=lambda r: r.distance_m)


def test_curation_overrides():
    cur = {"demo-molo-kiosk": CuratedPlace("demo-molo-kiosk", CITY.slug, None, ["plant-based"], "Try it", True)}
    rs = discover(DemoProvider(), CITY, SearchFilters(CITY.slug, categories=["budget-local"]), curated=cur).restaurants
    kiosk = next(r for r in rs if r.id == "demo-molo-kiosk")
    assert kiosk.featured and "plant-based" in kiosk.categories and kiosk.editor_note == "Try it"


def test_weighted_score_prefers_volume():
    few = Restaurant(id="a", name="a", source="demo", location=LatLng(0, 0), rating=4.9, rating_count=5)
    many = Restaurant(id="b", name="b", source="demo", location=LatLng(0, 0), rating=4.6, rating_count=900)
    assert weighted_score(many) > weighted_score(few)


def test_parse_favorites_rejects_bad_browser_data():
    raw = [
        {"place_id": "ChIJok1", "city_slug": "iloilo-city", "source": "google"},
        {"place_id": "ChIJok1", "city_slug": "iloilo-city"},          # duplicate
        {"place_id": "../etc", "city_slug": "iloilo-city"},           # bad id
        {"place_id": "ChIJok2", "city_slug": "<script>"},             # bad slug
        {"place_id": "ChIJok3", "city_slug": "iloilo-city", "source": "evil"},
        "nonsense",
    ]
    assert parse_favorites(raw) == [Favorite("ChIJok1", "iloilo-city", "google")]
    assert parse_favorites({"not": "a list"}) == []


def test_directions_url_uses_place_id_for_google():
    g = Restaurant(id="ChIJabc", name="Ember", source="google", location=LatLng(10.7, 122.56))
    assert "destination_place_id=ChIJabc" in directions_url(g)
    d = Restaurant(id="demo-x", name="Demo", source="demo", location=LatLng(10.7, 122.56))
    assert "destination_place_id" not in directions_url(d)


def test_google_provider_pipeline_with_stubbed_http(monkeypatch):
    from burger_atlas.providers.google_places import GooglePlacesProvider

    calls = []

    def fake_call(self, method, url, **kw):
        calls.append((method, url, kw.get("headers", {}).get("X-Goog-FieldMask")))
        if url.endswith(":searchText"):
            return {"places": [
                {"id": "ChIJjaro1", "displayName": {"text": "Jaro Smash"}, "formattedAddress": "E Lopez St, Jaro, Iloilo City",
                 "location": {"latitude": 10.725, "longitude": 122.558}, "rating": 4.6, "userRatingCount": 300},
                {"id": "ChIJfar", "displayName": {"text": "Far Away"}, "formattedAddress": "Roxas City",
                 "location": {"latitude": 11.58, "longitude": 122.75}},
            ]}
        return {"photoUri": "https://lh3.googleusercontent.com/x"}

    monkeypatch.setattr(GooglePlacesProvider, "_call", fake_call)
    p = GooglePlacesProvider("server-key")
    rs = discover(p, CITY, SearchFilters(CITY.slug, categories=["smash-classic"])).restaurants
    assert [r.id for r in rs] == ["ChIJjaro1"]  # out-of-city result dropped
    assert rs[0].district_slug == "jaro" and "smash-classic" in rs[0].categories
    assert calls[0][2].startswith("places.id")  # field mask always sent
    # changing filters never triggers another billed search
    discover(p, CITY, SearchFilters(CITY.slug, districts=["molo"], min_rating=4.5, open_now=True))
    discover(p, CITY, SearchFilters(CITY.slug, origin=LatLng(10.72, 122.55), radius_m=2000))
    assert len(calls) == 1


def test_quota_exhausted_gives_friendly_message(monkeypatch):
    from burger_atlas.providers.google_places import GooglePlacesProvider

    class R:
        status_code = 429

    p = GooglePlacesProvider("k")
    p._search_cache.clear()  # earlier test cached a result in the shared fallback store
    monkeypatch.setattr(p._http, "request", lambda *a, **k: R())
    res = discover(p, CITY, SearchFilters(CITY.slug))
    assert res.restaurants == [] and "check back tomorrow" in res.warnings[0]
