"""About — philosophy, data sources, terms and privacy."""

import streamlit as st

from burger_atlas.geo import enabled_cities
from burger_atlas.settings import get_settings

s = get_settings()

st.markdown(
    """<div class="ba-hero"><div class="ba-eyebrow-lg">About</div>
    <h1>A local burger guide, drawn as a map.</h1>
    <p>Burger Atlas is a curated way to find great burgers — the map comes first, the
    photography and notes help you choose, and the directions get you there.</p></div>""",
    unsafe_allow_html=True,
)
st.write("")

a, b = st.columns(2, gap="large")
with a:
    st.markdown("#### How it works")
    st.markdown(
        "- **Explore on the map.** Every pin is a burger spot; tap one for a quick preview.\n"
        "- **Narrow it down** by neighbourhood, burger style, rating, price, or distance.\n"
        "- **Read the Atlas take.** Editor's picks and notes come from our own curation.\n"
        "- **Save favorites** with one tap — no account needed."
    )
    st.markdown("#### Where we are")
    st.markdown(", ".join(f"**{c.name}**" for c in enabled_cities()) + " — with more Philippine cities on the way.")
with b:
    st.markdown("#### Data & attribution")
    st.markdown(
        "Restaurant listings, ratings, hours and photos are provided by **Google Maps** and are shown "
        "only on Google maps. Photo credits appear next to each photo. Editorial picks, notes and "
        "burger-style tags are Burger Atlas's own."
    )
    st.markdown("#### Terms & privacy")
    st.markdown(
        "By using Burger Atlas you also agree to the "
        "[Google Maps/Google Earth Additional Terms of Service](https://maps.google.com/help/terms_maps/) "
        "and acknowledge the [Google Privacy Policy](https://policies.google.com/privacy).\n\n"
        "**What we store:** nothing on our servers. Your favorites are kept only in your own browser "
        "(as a list of place IDs). There are no accounts, and we don't track you across sites.\n\n"
        "**Location:** only used when you tap *Near me*, only to sort nearby burgers, and never stored."
    )

with st.expander("Deployment status"):
    st.markdown(
        f"- Discovery provider: `{s.provider_name}`\n"
        f"- Google map: `{'configured' if s.google_maps_browser_key else 'not configured — demo map in use'}`\n"
        f"- Favorites: `stored in each visitor's browser`"
    )

st.markdown("<hr class='ba-rule'><p class='ba-small'>Burger Atlas · Find your next great burger.</p>",
            unsafe_allow_html=True)
