"""Geographic helpers: config loading, distance, district assignment."""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import yaml

from .models import Bounds, Category, City, District, LatLng
from .settings import CONFIG_DIR

EARTH_RADIUS_M = 6_371_000


def haversine_m(a: LatLng, b: LatLng) -> float:
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp = p2 - p1
    dl = math.radians(b.lng - a.lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def format_distance(m: float | None) -> str:
    if m is None:
        return ""
    return f"{m:.0f} m" if m < 1000 else f"{m / 1000:.1f} km"


def bounds_around(points: list[tuple[LatLng, int]]) -> Bounds:
    """Bounding rectangle covering a set of (centre, radius) circles."""
    south = west = math.inf
    north = east = -math.inf
    for c, r in points:
        dlat = r / 111_320
        dlng = r / (111_320 * max(math.cos(math.radians(c.lat)), 1e-6))
        south, north = min(south, c.lat - dlat), max(north, c.lat + dlat)
        west, east = min(west, c.lng - dlng), max(east, c.lng + dlng)
    return Bounds(south, west, north, east)


def assign_district(city: City, address: str, location: LatLng) -> str | None:
    """Pick a district by address alias first, then by nearest centre.

    Returns None when the place is far outside every district (e.g. a
    result that leaked in from a neighbouring municipality).
    """
    addr = (address or "").lower()
    # Longest alias first so "Iloilo City Proper" beats "City Proper", etc.
    aliases = sorted(
        ((alias.lower(), d.slug) for d in city.districts for alias in d.aliases),
        key=lambda x: -len(x[0]),
    )
    for alias, slug in aliases:
        if alias and alias in addr:
            return slug

    best, best_ratio = None, math.inf
    for d in city.districts:
        ratio = haversine_m(location, d.center) / max(d.radius_m, 1)
        if ratio < best_ratio:
            best, best_ratio = d.slug, ratio
    return best if best_ratio <= 2.5 else None


def _latlng(d: dict) -> LatLng:
    return LatLng(float(d["lat"]), float(d["lng"]))


@lru_cache(maxsize=4)
def load_cities(path: Path | None = None) -> tuple[str, dict[str, City]]:
    raw = yaml.safe_load((path or CONFIG_DIR / "cities.yaml").read_text(encoding="utf-8"))
    cities: dict[str, City] = {}
    for slug, c in raw["cities"].items():
        b = c["bounds"]
        cities[slug] = City(
            slug=slug,
            name=c["name"],
            region=c.get("region", ""),
            country_code=c.get("country_code", "PH"),
            enabled=bool(c.get("enabled", False)),
            currency_symbol=c.get("currency_symbol", "₱"),
            center=_latlng(c["center"]),
            zoom=int(c.get("zoom", 13)),
            bounds=Bounds(b["south"], b["west"], b["north"], b["east"]),
            districts=[
                District(
                    slug=d["slug"],
                    name=d["name"],
                    center=_latlng(d["center"]),
                    radius_m=int(d.get("radius_m", 1500)),
                    aliases=list(d.get("aliases", [d["name"]])),
                )
                for d in c.get("districts", [])
            ],
        )
    return raw.get("default_city", next(iter(cities))), cities


def enabled_cities() -> list[City]:
    return [c for c in load_cities()[1].values() if c.enabled]


def get_city(slug: str | None) -> City:
    default, cities = load_cities()
    city = cities.get(slug or "") or cities[default]
    return city


@lru_cache(maxsize=1)
def load_categories(path: Path | None = None) -> list[Category]:
    raw = yaml.safe_load((path or CONFIG_DIR / "categories.yaml").read_text(encoding="utf-8"))
    return [
        Category(
            slug=c["slug"],
            label=c["label"],
            blurb=c.get("blurb", ""),
            search_terms=list(c.get("search_terms", [])),
            keywords=[k.lower() for k in c.get("keywords", [])],
            place_types=list(c.get("place_types", [])),
            max_price_level=c.get("max_price_level"),
        )
        for c in raw["categories"]
    ]


def category_map() -> dict[str, Category]:
    return {c.slug: c for c in load_categories()}
