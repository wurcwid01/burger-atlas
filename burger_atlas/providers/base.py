"""Discovery provider interface.

A provider turns a :class:`ProviderQuery` into provider-neutral
:class:`~burger_atlas.models.Restaurant` objects. Swapping Google Places for
another source (or adding one per country) means implementing this
protocol — nothing in the UI changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..models import Bounds, City, LatLng, Photo, Restaurant, Source


class ProviderError(RuntimeError):
    """A provider call failed in a way the UI should explain to the user."""


@dataclass(frozen=True)
class ProviderQuery:
    text: str
    restrict_to: Bounds | None = None
    bias_center: LatLng | None = None
    bias_radius_m: int | None = None
    min_rating: float = 0.0
    open_now: bool = False
    max_pages: int = 1
    language: str = "en"
    region: str = "PH"
    extra: dict = field(default_factory=dict, hash=False, compare=False)


@runtime_checkable
class DiscoveryProvider(Protocol):
    name: str
    content_source: Source
    # Text shown wherever this provider's content appears off-map.
    attribution_label: str
    # Which map engines may legally display this provider's content.
    allowed_map_engines: frozenset[str]

    def search(self, city: City, query: ProviderQuery) -> list[Restaurant]: ...

    def get_details(self, place_id: str, city: City) -> Restaurant | None: ...

    def resolve_photo(self, photo: Photo, max_width: int = 800) -> str: ...
