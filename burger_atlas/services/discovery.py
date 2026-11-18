"""Discovery service: provider search → enrichment → filtering → ranking.

Cost-saving design: Burger Atlas makes ONE city-wide search per visitor
session (``PLACES_MAX_PAGES`` pages of 20). Every filter — district, style,
rating, price, open now, distance — is applied locally to those results, so
changing filters never triggers another billed Google request.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from ..geo import assign_district, category_map, haversine_m
from ..models import Category, City, Restaurant, SearchFilters
from ..providers import DiscoveryProvider, ProviderError, ProviderQuery
from ..store import CuratedPlace, curated_for

# Bayesian rating prior: a 4.9 with 8 reviews shouldn't outrank a 4.6 with 900.
PRIOR_MEAN = 4.0
PRIOR_WEIGHT = 40


@dataclass
class DiscoveryResult:
    restaurants: list[Restaurant]
    total_before_filters: int = 0
    warnings: list[str] = field(default_factory=list)
    queries: int = 0


def weighted_score(r: Restaurant) -> float:
    if r.rating is None:
        return PRIOR_MEAN - 0.5
    n = max(r.rating_count, 0)
    return (PRIOR_WEIGHT * PRIOR_MEAN + n * r.rating) / (PRIOR_WEIGHT + n)


def infer_categories(r: Restaurant, cats: list[Category]) -> set[str]:
    text = f"{r.name} {r.summary}".lower()
    found: set[str] = set()
    for c in cats:
        if any(k in text for k in c.keywords):
            found.add(c.slug)
        elif c.place_types and set(c.place_types) & set(r.types):
            found.add(c.slug)
        elif c.max_price_level is not None and r.price_level is not None and r.price_level <= c.max_price_level:
            found.add(c.slug)
    return found


def build_query(city: City, max_pages: int) -> ProviderQuery:
    """The single, filter-independent search used for a whole session."""
    return ProviderQuery(text=f"burger restaurant in {city.name}", restrict_to=city.bounds, max_pages=max_pages)


def enrich(r: Restaurant, city: City, curated: dict[str, CuratedPlace], cats: list[Category]) -> None:
    c = curated.get(r.id)
    if c:
        r.district_slug = c.district_slug or r.district_slug
        r.categories |= set(c.categories)
        r.editor_note = c.editor_note or r.editor_note
        r.featured = r.featured or c.featured
    if not r.district_slug:
        r.district_slug = assign_district(city, r.address, r.location)
    r.categories |= infer_categories(r, cats)


def passes(r: Restaurant, f: SearchFilters) -> bool:
    if f.districts and r.district_slug not in f.districts:
        return False
    if f.categories and not (r.categories & set(f.categories)):
        return False
    if f.min_rating and (r.rating or 0) < f.min_rating:
        return False
    if f.price_levels:
        if r.price_level is None:
            if f.strict_price:
                return False
        elif r.price_level not in f.price_levels:
            return False
    if f.open_now and r.open_now is False:
        return False
    if f.origin and f.radius_m and (r.distance_m is None or r.distance_m > f.radius_m):
        return False
    return True


def sort_restaurants(rs: list[Restaurant], sort: str) -> list[Restaurant]:
    if sort == "distance" and all(r.distance_m is not None for r in rs):
        return sorted(rs, key=lambda r: r.distance_m)
    if sort == "rating":
        return sorted(rs, key=lambda r: (-(r.rating or 0), -r.rating_count))
    return sorted(rs, key=lambda r: (not r.featured, -weighted_score(r)))


def discover(
    provider: DiscoveryProvider,
    city: City,
    f: SearchFilters,
    max_pages: int = 2,
    curated: dict[str, CuratedPlace] | None = None,
) -> DiscoveryResult:
    cats = list(category_map().values())
    curated = curated_for(city.slug) if curated is None else curated
    warnings: list[str] = []
    try:
        found = provider.search(city, build_query(city, max_pages))
    except ProviderError as e:
        warnings.append(str(e))
        found = []

    rs = []
    for r in found:
        # Copy so enrichment never mutates provider-cached objects.
        r = replace(r, categories=set(r.categories))
        enrich(r, city, curated, cats)
        if r.district_slug is None and not city.bounds.contains(r.location):
            continue  # leaked in from outside the city
        r.distance_m = haversine_m(f.origin, r.location) if f.origin else None
        rs.append(r)

    total = len(rs)
    rs = sort_restaurants([r for r in rs if passes(r, f)], f.sort)
    return DiscoveryResult(restaurants=rs, total_before_filters=total, warnings=warnings, queries=1)
