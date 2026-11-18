"""Runtime settings.

Values are read from Streamlit secrets first (``.streamlit/secrets.toml`` or
the Streamlit Cloud secrets UI), then from environment variables. Nothing
secret is ever sent to the browser except ``google_maps_browser_key``, which
must be an HTTP-referrer-restricted key that only allows the Maps JavaScript
API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
ILLUSTRATIONS_DIR = ROOT_DIR / "static" / "illustrations"
# URL Streamlit serves ./static at (server.enableStaticServing).
ILLUSTRATIONS_URL = "app/static/illustrations"


def _secret(name: str, default: str = "") -> str:
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # secrets file missing, or running outside Streamlit
        pass
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    # Discovery provider: "auto" | "google" | "demo"
    data_provider: str
    # Server-side key: Places API (New) only. Never rendered into HTML.
    google_places_api_key: str
    # Browser key: Maps JavaScript API only, referrer-restricted.
    google_maps_browser_key: str
    # Map ID for Advanced Markers + cloud-based minimalist styling.
    google_map_id: str
    # In-session reuse window for Places responses (seconds). Places content
    # is never written to a database or shared between users.
    places_session_ttl_s: int
    places_max_pages: int
    # Google photos shown on the details page (each one is a billed request).
    detail_photos: int
    default_city: str

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_places_api_key and self.google_maps_browser_key)

    @property
    def provider_name(self) -> str:
        if self.data_provider == "demo":
            return "demo"
        if self.data_provider == "google":
            return "google"
        return "google" if self.google_enabled else "demo"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        data_provider=_secret("DATA_PROVIDER", "auto").strip().lower(),
        google_places_api_key=_secret("GOOGLE_PLACES_API_KEY"),
        google_maps_browser_key=_secret("GOOGLE_MAPS_BROWSER_KEY"),
        google_map_id=_secret("GOOGLE_MAP_ID", "DEMO_MAP_ID"),
        places_session_ttl_s=int(_secret("PLACES_SESSION_TTL_S", "1800")),
        places_max_pages=int(_secret("PLACES_MAX_PAGES", "2")),
        detail_photos=int(_secret("DETAIL_PHOTOS", "1")),
        default_city=_secret("DEFAULT_CITY", ""),
    )
