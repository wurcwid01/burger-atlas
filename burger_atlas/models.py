"""Provider-neutral domain models.

Every discovery provider (Google Places, demo data, future providers)
returns these types, so the UI, map and database layers never depend on a
specific API's response shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Source = Literal["google", "demo"]


@dataclass(frozen=True)
class LatLng:
    lat: float
    lng: float


@dataclass(frozen=True)
class Attribution:
    """Credit that must be shown next to the content it belongs to."""

    name: str
    uri: str = ""
    photo_uri: str = ""


@dataclass
class Photo:
    # Provider reference (e.g. a Places photo resource name). Resolved to a
    # displayable URL lazily, only for photos actually shown.
    ref: str
    url: str = ""
    width: int = 0
    height: int = 0
    attributions: list[Attribution] = field(default_factory=list)


@dataclass
class District:
    slug: str
    name: str
    center: LatLng
    radius_m: int
    aliases: list[str] = field(default_factory=list)


@dataclass
class Bounds:
    south: float
    west: float
    north: float
    east: float

    def contains(self, p: LatLng) -> bool:
        return self.south <= p.lat <= self.north and self.west <= p.lng <= self.east


@dataclass
class City:
    slug: str
    name: str
    region: str
    country_code: str
    enabled: bool
    currency_symbol: str
    center: LatLng
    zoom: int
    bounds: Bounds
    districts: list[District]

    def district(self, slug: str | None) -> District | None:
        return next((d for d in self.districts if d.slug == slug), None)


@dataclass
class Category:
    slug: str
    label: str
    blurb: str
    search_terms: list[str]
    keywords: list[str]
    place_types: list[str]
    max_price_level: int | None = None


@dataclass
class Restaurant:
    id: str
    name: str
    source: Source
    location: LatLng
    address: str = ""
    rating: float | None = None
    rating_count: int = 0
    # 0 free, 1 inexpensive, 2 moderate, 3 expensive, 4 very expensive
    price_level: int | None = None
    primary_type: str = ""
    types: list[str] = field(default_factory=list)
    summary: str = ""
    phone: str = ""
    website: str = ""
    maps_uri: str = ""
    open_now: bool | None = None
    hours: list[str] = field(default_factory=list)
    photos: list[Photo] = field(default_factory=list)
    # Third-party data providers credited by the source (Places `attributions`).
    attributions: list[Attribution] = field(default_factory=list)
    # Enrichment added by Burger Atlas (our own data, safe to store):
    district_slug: str | None = None
    categories: set[str] = field(default_factory=set)
    editor_note: str = ""
    featured: bool = False
    distance_m: float | None = None

    @property
    def is_google_content(self) -> bool:
        return self.source == "google"

    @property
    def hero_photo(self) -> Photo | None:
        return self.photos[0] if self.photos else None


@dataclass
class SearchFilters:
    city_slug: str
    districts: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    min_rating: float = 0.0
    # Allowed price levels (empty = any). Restaurants with unknown price are
    # kept unless `strict_price` is on.
    price_levels: list[int] = field(default_factory=list)
    strict_price: bool = False
    open_now: bool = False
    origin: LatLng | None = None
    radius_m: int | None = None
    sort: Literal["recommended", "rating", "distance"] = "recommended"
