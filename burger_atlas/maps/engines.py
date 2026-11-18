"""Map engines and the compliance guard that pairs them with providers.

Google Maps Platform terms forbid showing Places API content on a
non-Google map. That rule is enforced here, in one place:

* every provider declares ``allowed_map_engines``
* every restaurant carries its ``source``
* :func:`assert_compliant` refuses to render Google content on any engine
  other than ``google`` — it raises before a single marker is sent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import Restaurant
from ..settings import Settings


class ComplianceError(RuntimeError):
    pass


class MapEngine(Protocol):
    name: str

    def browser_config(self) -> dict: ...


@dataclass(frozen=True)
class GoogleMapEngine:
    browser_key: str
    map_id: str = "DEMO_MAP_ID"
    name: str = "google"

    def browser_config(self) -> dict:
        # The browser key is public by design; restrict it by HTTP referrer
        # and to the Maps JavaScript API only in Google Cloud Console.
        return {"engine": "google", "browser_key": self.browser_key, "map_id": self.map_id}


@dataclass(frozen=True)
class LeafletDemoEngine:
    """Open-source map for FICTIONAL demo data only."""

    name: str = "leaflet"

    def browser_config(self) -> dict:
        return {"engine": "leaflet"}


def choose_engine(settings: Settings, allowed: frozenset[str]) -> MapEngine:
    if "google" in allowed and settings.google_maps_browser_key:
        return GoogleMapEngine(settings.google_maps_browser_key, settings.google_map_id or "DEMO_MAP_ID")
    if "leaflet" in allowed:
        return LeafletDemoEngine()
    raise ComplianceError(
        "This content requires a Google map, but GOOGLE_MAPS_BROWSER_KEY isn't configured."
    )


def assert_compliant(engine: MapEngine, restaurants: list[Restaurant]) -> None:
    if engine.name != "google" and any(r.is_google_content for r in restaurants):
        raise ComplianceError("Google Places content may only be displayed on a Google map.")
