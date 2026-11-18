"""Favorites — saved burger spots, kept in the visitor's browser."""

import streamlit as st

from burger_atlas.maps.component import render_map
from burger_atlas.maps.engines import ComplianceError, choose_engine
from burger_atlas.providers import ProviderError
from burger_atlas.settings import get_settings
from burger_atlas.ui import state
from burger_atlas.ui.cards import card_grid, google_attribution

ss = st.session_state
city = state.current_city()

st.markdown(
    """<div class="ba-hero"><div class="ba-eyebrow-lg">Favorites</div>
    <h1>Your burger <span class="ba-mark">shortlist.</span></h1>
    <p>Everything you've saved, in one place. No account needed — your list is kept
    privately in this browser on this device.</p></div>""",
    unsafe_allow_html=True,
)
st.write("")

# ------------------------------------------------------------------ list
favs = state.favorites()
if not favs:
    st.markdown("### Nothing saved yet")
    st.markdown("<p class='ba-muted'>Tap <b>♡ Save</b> on any burger spot and it'll land here.</p>",
                unsafe_allow_html=True)
    if st.button("Start exploring", type="primary"):
        st.switch_page("views/explore.py")
    st.stop()

restaurants, missing = [], 0
providers = {}
with st.spinner("Loading your favorites…"):
    for f in favs:
        if f.city_slug != city.slug:
            continue
        p = providers.setdefault(f.source, state.provider_for_source(f.source))
        if p is None:
            missing += 1
            continue
        try:
            r = p.get_details(f.place_id, city)
        except ProviderError:
            r = None
        if r is None:
            missing += 1
        else:
            restaurants.append(r)

other_city = sum(1 for f in favs if f.city_slug != city.slug)
st.markdown(f"### {len(restaurants)} saved in {city.name}")
if missing:
    st.caption(f"{missing} saved place{'s' if missing != 1 else ''} couldn't be loaded right now.")
if other_city:
    st.caption(f"{other_city} more saved in other cities.")

if restaurants:
    # Pick an engine every source present is allowed on (Google content ⇒ Google map).
    allowed = frozenset.intersection(*[p.allowed_map_engines for p in providers.values() if p])
    try:
        engine = choose_engine(get_settings(), allowed)
        ev = render_map(engine, city, restaurants, height=380, key="fav_map")
        if ev.open_details:
            state.open_details(ev.open_details)
    except ComplianceError as e:
        st.caption(str(e))
    st.write("")
    primary = next(iter(p for p in providers.values() if p))
    card_grid(restaurants, city, primary, key_prefix="fav", removable=True)
    google_attribution(restaurants, primary)
