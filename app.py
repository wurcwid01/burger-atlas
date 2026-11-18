"""Burger Atlas — Find your next great burger.

Run with:  streamlit run app.py
"""

import streamlit as st

from burger_atlas.ui import state
from burger_atlas.ui.theme import brand_header, inject_theme

st.set_page_config(
    page_title="Burger Atlas — Find your next great burger",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()

# Keep Explore filters when the user visits another page and comes back
# (Streamlit drops state for widgets that weren't rendered on a run).
for _k in [k for k in st.session_state if str(k).startswith("f_")]:
    st.session_state[_k] = st.session_state[_k]

state.sync_favorites()

pages = [
    st.Page("views/explore.py", title="Explore", default=True, url_path="explore"),
    st.Page("views/details.py", title="Restaurant Details", url_path="restaurant"),
    st.Page("views/favorites.py", title="Favorites", url_path="favorites"),
    st.Page("views/about.py", title="About", url_path="about"),
]
nav = st.navigation(pages, position="top")
brand_header()
nav.run()
