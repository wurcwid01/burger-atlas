"""Restaurant cards and small presentational helpers."""

from __future__ import annotations

from html import escape

import streamlit as st

from ..geo import category_map, format_distance
from ..maps.component import directions_url, price_label
from ..models import City, Photo, Restaurant
from ..providers import DiscoveryProvider
from ..providers.demo import illustration_url
from . import state

PLACEHOLDER = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 3'><rect width='4' height='3' fill='%23E9E2D5'/>"
    "<circle cx='2' cy='1.35' r='.7' fill='%23D99A5B'/><rect x='1.3' y='1.55' width='1.4' height='.32' rx='.16' fill='%235A3A2A'/></svg>"
)


def safe_url(u: str) -> str:
    """Only allow http(s) and our own data: image URIs into HTML attributes."""
    if u.startswith(("https://", "http://", "data:image/", "app/static/")):
        return escape(u, quote=True)
    return ""


# Hand-drawn marker illustrations (tools/gen_illustrations.py), grouped by burger style.
ILLUSTRATIONS = {
    "smash-classic": [1, 2, 3],
    "gourmet-craft": [4, 5],
    "chicken-fish": [6, 7],
    "plant-based": [8, 9],
    "budget-local": [10, 11, 12],
}
_ORDER = ["chicken-fish", "plant-based", "gourmet-craft", "smash-classic", "budget-local"]


def illustration_for(r: Restaurant) -> str:
    """Stable illustration matching the restaurant's burger style (our own art, free to show)."""
    style = next((c for c in _ORDER if c in r.categories), "smash-classic")
    options = ILLUSTRATIONS[style]
    n = options[sum(map(ord, r.id)) % len(options)]
    return illustration_url(f"burger-{n:02d}.svg")


def photo_url(provider: DiscoveryProvider, photo: Photo | None, width: int = 640) -> str:
    if not photo:
        return ""
    try:
        return provider.resolve_photo(photo, width)
    except Exception:
        return ""


def credit_html(photo: Photo | None) -> str:
    if not photo or not photo.attributions or not photo.url:
        return ""
    parts = []
    for a in photo.attributions:
        name = escape(a.name)
        parts.append(f'<a href="{safe_url(a.uri)}" target="_blank" rel="noopener">{name}</a>' if a.uri else name)
    return "Photo: " + ", ".join(parts)


def meta_line(r: Restaurant, city: City) -> str:
    bits = []
    if r.rating:
        cnt = f" ({r.rating_count:,})" if r.rating_count else ""
        bits.append(f'<span class="ba-star">★</span> {r.rating:.1f}{cnt}')
    if r.price_level:
        bits.append(escape(price_label(r.price_level, city.currency_symbol)))
    d = city.district(r.district_slug)
    if d:
        bits.append(escape(d.name))
    if r.distance_m is not None:
        bits.append(escape(format_distance(r.distance_m)))
    if r.open_now is True:
        bits.append('<span style="color:#5d7a52">Open now</span>')
    elif r.open_now is False:
        bits.append("Closed")
    return " &nbsp;·&nbsp; ".join(bits)


def chips_html(r: Restaurant) -> str:
    cats = category_map()
    chips = "".join(
        f'<span class="ba-chip2">{escape(cats[c].label)}</span>' for c in sorted(r.categories) if c in cats
    )
    return f'<div class="ba-chiprow">{chips}</div>' if chips else ""


def restaurant_card(
    r: Restaurant,
    city: City,
    provider: DiscoveryProvider,
    *,
    key_prefix: str,
    fav_ids: set[str],
    on_show_on_map=None,
    removable: bool = False,
) -> None:
    if r.source == "demo":
        img = safe_url(photo_url(state.provider_for_source("demo"), r.hero_photo))
    else:
        # Never fetch Google photos for cards (billed per photo) — reuse one only if
        # it was already loaded on the details page, else show our illustration.
        hero = r.hero_photo
        img = safe_url(hero.url) if hero and hero.url else ""
    img = img or illustration_for(r) or PLACEHOLDER
    tag = '<span class="ba-card-tag">Editor\'s pick</span>' if r.featured else ""
    note = f'<div class="ba-note">{escape(r.editor_note)}</div>' if r.editor_note else ""
    credit = credit_html(r.hero_photo)
    with st.container(border=True):
        # Joined without newlines/indentation: Markdown would turn an indented line into a code block.
        parts = [
            f'<div class="ba-card-media">{tag}<img src="{img}" alt="" loading="lazy" referrerpolicy="no-referrer"></div>',
            f'<div class="ba-credit">{credit}</div>' if credit else "",
            f'<div class="ba-card-title">{escape(r.name)}</div>',
            f'<div class="ba-card-meta">{meta_line(r, city)}</div>',
            chips_html(r),
            note,
        ]
        st.markdown("".join(parts), unsafe_allow_html=True)
        if on_show_on_map:
            st.button("Show on map", key=f"{key_prefix}-m-{r.id}", type="tertiary",
                      icon=":material/location_on:", on_click=on_show_on_map, args=(r.id,))
        cols = st.columns(2, wrap=False, gap="small")
        if cols[0].button("Details", key=f"{key_prefix}-d-{r.id}", width="stretch", type="primary"):
            state.open_details(r.id)
        saved = r.id in fav_ids
        label = ("Remove" if removable else "♥ Saved") if saved else "♡ Save"
        cols[1].button(label, key=f"{key_prefix}-f-{r.id}", width="stretch",
                       help="Remove from favorites" if saved else "Save to favorites",
                       on_click=state.toggle_favorite, args=(r, city))


def card_grid(
    restaurants: list[Restaurant],
    city: City,
    provider: DiscoveryProvider,
    *,
    key_prefix: str,
    columns: int = 3,
    on_show_on_map=None,
    removable: bool = False,
) -> None:
    fav_ids = state.favorite_ids()
    for i in range(0, len(restaurants), columns):
        cols = st.columns(columns, gap="medium")
        for col, r in zip(cols, restaurants[i : i + columns]):
            with col:
                restaurant_card(r, city, provider, key_prefix=key_prefix, fav_ids=fav_ids,
                                on_show_on_map=on_show_on_map, removable=removable)


def google_attribution(restaurants: list[Restaurant], provider: DiscoveryProvider) -> None:
    """Credit Google (and any third parties) wherever Places content appears off-map."""
    if not any(r.is_google_content for r in restaurants):
        if restaurants:
            st.markdown('<div class="ba-attrib">Sample restaurants are fictional and shown for demonstration only.</div>',
                        unsafe_allow_html=True)
        return
    third = sorted({(a.name, a.uri) for r in restaurants for a in r.attributions if a.name})
    extra = ""
    if third:
        extra = " · Additional data: " + ", ".join(
            f'<a href="{safe_url(u)}" target="_blank" rel="noopener">{escape(n)}</a>' if u else escape(n)
            for n, u in third
        )
    st.markdown(
        f'<div class="ba-attrib">Restaurant information from <span translate="no" '
        f'style="font-family:Roboto,Arial,sans-serif;font-weight:500">Google Maps</span>{extra}</div>',
        unsafe_allow_html=True,
    )


__all__ = ["card_grid", "restaurant_card", "google_attribution", "photo_url", "safe_url", "credit_html",
           "meta_line", "chips_html", "directions_url"]
