"""Invisible component that keeps favorites in the visitor's browser.

Favorites are stored in localStorage under ``ba_favorites`` as a small list
of ``{place_id, city_slug, source}`` — place IDs only, no Google content.

Flow:
* first run of a session: the browser reports what it has stored
* after that, Python is the source of truth and sends the list down
  whenever it changes; the browser writes it to localStorage
"""

from __future__ import annotations

import uuid

import streamlit as st

_JS = """
export default function ({ data, setStateValue }) {
  const K = "ba_favorites";
  let stored = [];
  try {
    if (data && Array.isArray(data.favorites)) {
      localStorage.setItem(K, JSON.stringify(data.favorites));
    }
    stored = JSON.parse(localStorage.getItem(K) || "[]");
    if (!Array.isArray(stored)) stored = [];
  } catch (e) {
    stored = (data && data.favorites) || [];   // storage blocked (private mode)
  }
  const report = JSON.stringify({ s: data && data.session, f: stored });
  if (window.__baFavReport !== report) {
    window.__baFavReport = report;
    setStateValue("favorites", stored);
  }
}
"""


@st.cache_resource
def _component():
    return st.components.v2.component("burger_atlas_favorites", js=_JS)


def favorites_bridge(favorites_to_store: list[dict] | None) -> list | None:
    """Sync favorites with localStorage. Returns what the browser reported (or None yet)."""
    if "_ba_session_nonce" not in st.session_state:
        st.session_state["_ba_session_nonce"] = uuid.uuid4().hex
    data: dict = {"session": st.session_state["_ba_session_nonce"]}
    if favorites_to_store is not None:
        data["favorites"] = favorites_to_store
    result = _component()(data=data, key="ba_favorites", on_favorites_change=lambda: None)
    return getattr(result, "favorites", None)
