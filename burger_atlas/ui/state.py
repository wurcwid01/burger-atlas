"""Session wiring: provider, city and browser-stored favorites."""

from __future__ import annotations

import streamlit as st

from ..geo import get_city
from ..models import City, Restaurant
from ..providers import DemoProvider, DiscoveryProvider, GooglePlacesProvider, ProviderError, get_provider
from ..settings import get_settings
from ..store import MAX_FAVORITES, Favorite, parse_favorites
from .browser_bridge import favorites_bridge


# ---------------------------------------------------------------- services
@st.cache_resource
def _provider() -> DiscoveryProvider:
    return get_provider()


def provider() -> DiscoveryProvider:
    try:
        return _provider()
    except ProviderError as e:
        st.warning(f"{e} Falling back to sample data.")
        return DemoProvider()


def provider_for_source(source: str) -> DiscoveryProvider | None:
    if source == "demo":
        return DemoProvider()
    p = provider()
    return p if isinstance(p, GooglePlacesProvider) else None


def current_city() -> City:
    s = get_settings()
    return get_city(st.session_state.get("city_slug") or s.default_city or None)


# ---------------------------------------------------------------- favorites
def sync_favorites() -> None:
    """Run once per script run (from app.py) before any page renders."""
    ss = st.session_state
    loaded = ss.get("_favs_loaded", False)
    to_store = [f.to_dict() for f in ss.get("favorites", [])] if loaded else None
    reported = favorites_bridge(to_store)
    if not loaded and reported is not None:
        ss["favorites"] = parse_favorites(reported)
        ss["_favs_loaded"] = True
        st.rerun()  # render pages with the restored list


def favorites() -> list[Favorite]:
    return list(st.session_state.get("favorites", []))


def favorite_ids() -> set[str]:
    return {f.place_id for f in favorites()}


def toggle_favorite(r: Restaurant, city: City) -> None:
    ss = st.session_state
    favs = favorites()
    if r.id in {f.place_id for f in favs}:
        ss["favorites"] = [f for f in favs if f.place_id != r.id]
        st.toast(f"Removed {r.name} from favorites")
    elif len(favs) >= MAX_FAVORITES:
        st.toast("Your favorites list is full — remove one first.")
    else:
        ss["favorites"] = [Favorite(r.id, city.slug, r.source), *favs]
        st.toast(f"Saved {r.name}")
    ss["_favs_loaded"] = True


def open_details(place_id: str) -> None:
    st.session_state["selected_place"] = place_id
    st.switch_page("views/details.py")
