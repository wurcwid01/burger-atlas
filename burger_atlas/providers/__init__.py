"""Discovery providers and the factory that picks one from settings."""

from __future__ import annotations

from ..settings import Settings, get_settings
from .base import DiscoveryProvider, ProviderError, ProviderQuery
from .demo import DemoProvider
from .google_places import GooglePlacesProvider

__all__ = [
    "DiscoveryProvider",
    "ProviderError",
    "ProviderQuery",
    "DemoProvider",
    "GooglePlacesProvider",
    "get_provider",
]


def get_provider(settings: Settings | None = None) -> DiscoveryProvider:
    s = settings or get_settings()
    if s.provider_name == "google":
        return GooglePlacesProvider(s.google_places_api_key, session_ttl_s=s.places_session_ttl_s)
    return DemoProvider()
