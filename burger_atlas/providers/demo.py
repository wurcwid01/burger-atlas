"""Demo provider: fictional sample restaurants for running without API keys.

This data is invented (see ``data/demo_restaurants.json``) and is *not*
Google Maps content, so it may be shown on the open-source Leaflet/CARTO
demo map. Real Google Places results can never use that map — see
``burger_atlas.maps.registry``.
"""

from __future__ import annotations

import json
from functools import lru_cache

from ..geo import haversine_m
from ..models import City, LatLng, Photo, Restaurant
from ..settings import DATA_DIR, ILLUSTRATIONS_DIR, ILLUSTRATIONS_URL
from .base import ProviderQuery


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads((DATA_DIR / "demo_restaurants.json").read_text(encoding="utf-8"))


def illustration_url(filename: str) -> str:
    """URL of one of our hand-drawn illustrations, or "" if it doesn't exist."""
    if "/" in filename or not (ILLUSTRATIONS_DIR / filename).is_file():
        return ""
    return f"{ILLUSTRATIONS_URL}/{filename}"


def _to_restaurant(d: dict) -> Restaurant:
    return Restaurant(
        id=d["id"],
        name=d["name"],
        source="demo",
        location=LatLng(d["lat"], d["lng"]),
        address=d.get("address", ""),
        rating=d.get("rating"),
        rating_count=d.get("rating_count", 0),
        price_level=d.get("price_level"),
        primary_type="hamburger_restaurant",
        types=["hamburger_restaurant", "restaurant"],
        summary=d.get("summary", ""),
        maps_uri="",
        open_now=d.get("open_now"),
        hours=d.get("hours", []),
        photos=[
            Photo(ref=f)  # our own illustrations: no credit line needed
            for f in d.get("photos", [])
        ],
        district_slug=d.get("district"),
        categories=set(d.get("categories", [])),
        editor_note=d.get("editor_note", ""),
        featured=bool(d.get("featured")),
    )


class DemoProvider:
    name = "demo"
    content_source = "demo"
    attribution_label = "Sample data"
    allowed_map_engines = frozenset({"google", "leaflet"})

    def _all(self, city: City) -> list[Restaurant]:
        data = _load()
        if data.get("city") != city.slug:
            return []
        return [_to_restaurant(d) for d in data["restaurants"]]

    def search(self, city: City, query: ProviderQuery) -> list[Restaurant]:
        out = []
        for r in self._all(city):
            if query.restrict_to and not query.restrict_to.contains(r.location):
                continue
            if query.bias_center and query.bias_radius_m:
                # Bias, not restrict: allow some slack like the real API.
                if haversine_m(query.bias_center, r.location) > query.bias_radius_m * 1.5:
                    continue
            if query.min_rating and (r.rating or 0) < query.min_rating:
                continue
            if query.open_now and r.open_now is False:
                continue
            out.append(r)
        return out

    def get_details(self, place_id: str, city: City) -> Restaurant | None:
        return next((r for r in self._all(city) if r.id == place_id), None)

    def resolve_photo(self, photo: Photo, max_width: int = 800) -> str:
        if not photo.url:
            photo.url = illustration_url(photo.ref)
        return photo.url
