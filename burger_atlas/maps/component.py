"""Streamlit binding for the interactive map (Components v2, bidirectional).

``render_map`` sends markers to the browser and returns the events the user
triggered on this run: ``open_details`` (place id), ``locate`` ({lat, lng})
and ``search_area`` ({lat, lng, radius_m}).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st

from ..geo import category_map, format_distance
from ..models import City, LatLng, Restaurant
from .engines import MapEngine, assert_compliant

_ASSETS = Path(__file__).parent / "assets"

_HTML = """
<div class="ba-map-root">
  <div class="ba-map"></div>
  <div class="ba-controls">
    <span class="ba-badge" hidden></span>
    <div class="ba-right">
      <button class="ba-ctrl ba-search-area" hidden>Search this area</button>
      <button class="ba-ctrl ba-locate" title="Find burgers near me">◎ Near me</button>
    </div>
  </div>
  <div class="ba-preview" hidden></div>
</div>
"""


@st.cache_resource
def _component():
    return st.components.v2.component(
        "burger_atlas_map",
        html=_HTML,
        css=(_ASSETS / "atlas_map.css").read_text(encoding="utf-8"),
        js=(_ASSETS / "atlas_map.js").read_text(encoding="utf-8"),
        isolate_styles=False,  # Google Maps injects global styles
    )


def price_label(level: int | None, symbol: str = "₱") -> str:
    return symbol * level if level else ""


def directions_url(r: Restaurant, origin: LatLng | None = None) -> str:
    """Google Maps URL (no API key, no billing) that opens turn-by-turn directions."""
    q = {"api": "1", "destination": f"{r.location.lat},{r.location.lng}"}
    if r.is_google_content:
        q["destination_place_id"] = r.id
        q["destination"] = r.name
    if origin:
        q["origin"] = f"{origin.lat},{origin.lng}"
    return "https://www.google.com/maps/dir/?" + urlencode(q)


def marker_payload(r: Restaurant, city: City, origin: LatLng | None) -> dict:
    cats = category_map()
    district = city.district(r.district_slug)
    photo = r.hero_photo
    credit = photo.attributions[0] if photo and photo.attributions else None
    return {
        "id": r.id,
        "source": r.source,
        "name": r.name,
        "lat": r.location.lat,
        "lng": r.location.lng,
        "rating": r.rating,
        "rating_count": r.rating_count,
        "price": price_label(r.price_level, city.currency_symbol),
        "district": district.name if district else "",
        "distance": format_distance(r.distance_m),
        "categories": [cats[c].label for c in sorted(r.categories) if c in cats],
        "featured": r.featured,
        # Only photos already resolved for cards are reused — no extra calls.
        "photo": photo.url if photo and photo.url else _illustration(r),
        "photo_credit": credit.name if (credit and photo and photo.url) else "",
        "photo_credit_uri": credit.uri if (credit and photo and photo.url) else "",
        "directions": directions_url(r, origin),
    }


def _illustration(r: Restaurant) -> str:
    from ..ui.cards import illustration_for  # local import avoids a cycle

    return illustration_for(r)


@dataclass
class MapEvents:
    open_details: str | None = None
    locate: dict | None = None
    search_area: dict | None = None


def render_map(
    engine: MapEngine,
    city: City,
    restaurants: list[Restaurant],
    *,
    origin: LatLng | None = None,
    radius_m: int | None = None,
    focus_districts: list[str] | None = None,
    selected_id: str | None = None,
    select_nonce: int = 0,
    height: int = 560,
    badge: str = "",
    key: str = "atlas_map",
    controls: bool = True,
) -> MapEvents:
    assert_compliant(engine, restaurants)  # raises before anything is sent
    focus = [
        {"center": {"lat": d.center.lat, "lng": d.center.lng}, "radius_m": d.radius_m}
        for d in city.districts
        if focus_districts and d.slug in focus_districts
    ]
    data = {
        **engine.browser_config(),
        "center": {"lat": city.center.lat, "lng": city.center.lng},
        "zoom": city.zoom,
        "markers": [marker_payload(r, city, origin) for r in restaurants],
        "user": {"lat": origin.lat, "lng": origin.lng} if origin else None,
        "radius_m": radius_m,
        "focus": focus,
        "selected_id": selected_id,
        "select_nonce": select_nonce,
        "fitKey": f"{city.slug}:{','.join(focus_districts or [])}:{radius_m}",
        "height": height,
        "badge": badge,
        "controls": controls,
    }
    noop = lambda: None  # noqa: E731 — callbacks register the trigger keys
    result = _component()(
        data=data,
        key=key,
        height=height,
        on_open_details_change=noop,
        on_locate_change=noop,
        on_search_area_change=noop,
    )
    return MapEvents(
        open_details=getattr(result, "open_details", None),
        locate=getattr(result, "locate", None),
        search_area=getattr(result, "search_area", None),
    )
