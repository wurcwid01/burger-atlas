"""Restaurant Details."""

from html import escape

import streamlit as st

from burger_atlas.store import curated_for, is_valid_place_id
from burger_atlas.geo import category_map, haversine_m
from burger_atlas.maps.component import directions_url, render_map
from burger_atlas.maps.engines import ComplianceError, choose_engine
from burger_atlas.providers import ProviderError
from burger_atlas.services.discovery import enrich
from burger_atlas.settings import get_settings
from burger_atlas.ui import state
from burger_atlas.ui.cards import chips_html, credit_html, google_attribution, meta_line, photo_url, safe_url

ss = st.session_state
city = state.current_city()

place_id = st.query_params.get("place") or ss.get("selected_place")
if not is_valid_place_id(place_id):
    st.markdown("## Pick a burger spot first")
    st.markdown("<p class='ba-muted'>Choose a restaurant on the map or from the list to see its details.</p>",
                unsafe_allow_html=True)
    if st.button("Go to Explore", type="primary"):
        st.switch_page("views/explore.py")
    st.stop()

st.query_params["place"] = place_id  # shareable URL
ss["selected_place"] = place_id

source = "demo" if place_id.startswith("demo-") else "google"
provider = state.provider_for_source(source)
if provider is None:
    st.warning("This restaurant comes from Google Places, which isn't configured in this deployment.")
    st.stop()

try:
    with st.spinner("Loading details…"):
        r = provider.get_details(place_id, city)
except ProviderError as e:
    st.error(str(e))
    st.stop()
if r is None:
    st.warning("We couldn't find that restaurant. It may have closed or moved.")
    st.stop()

enrich(r, city, curated_for(city.slug), list(category_map().values()))
origin = ss.get("user_loc")
if origin:
    r.distance_m = haversine_m(origin, r.location)

if st.button("← Back to the map", type="tertiary"):
    st.query_params.clear()
    st.switch_page("views/explore.py")

# ------------------------------------------------------------------ gallery
n_photos = 3 if provider.name == "demo" else max(0, min(get_settings().detail_photos, 3))
photos = r.photos[:n_photos]
urls = [photo_url(provider, p, 1200 if i == 0 else 600) for i, p in enumerate(photos)]


def figure(i: int) -> str:
    if i >= len(photos) or not urls[i]:
        return '<figure></figure>'
    cap = credit_html(photos[i])
    return (f'<figure><img src="{safe_url(urls[i])}" alt="" referrerpolicy="no-referrer">'
            + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>")


shown = [i for i, u in enumerate(urls) if u]
if shown:
    side = "".join(figure(i) for i in shown[1:3])
    st.markdown(
        f'<div class="ba-gallery{"" if side else " is-single"}"><div class="ba-g-main">{figure(shown[0])}</div>'
        + (f'<div class="ba-g-side">{side}</div>' if side else "") + "</div>",
        unsafe_allow_html=True,
    )
    st.write("")

# ------------------------------------------------------------------ body
left, right = st.columns([1.55, 1], gap="large")
with left:
    district = city.district(r.district_slug)
    eyebrow = " · ".join(x for x in ["Editor's pick" if r.featured else "", district.name if district else "", city.name] if x)
    st.markdown(
        f"""<div class="ba-eyebrow-lg">{escape(eyebrow)}</div>
        <h1 style="margin:.2rem 0 .3rem;font-size:clamp(2rem,4vw,2.9rem);line-height:1.05">{escape(r.name)}</h1>
        <div class="ba-card-meta" style="font-size:.95rem">{meta_line(r, city)}</div>
        {chips_html(r)}""",
        unsafe_allow_html=True,
    )
    if r.editor_note:
        st.markdown(f"<div class='ba-h4'>The Atlas take</div><div class='ba-note' style='font-size:1rem'>{escape(r.editor_note)}</div>",
                    unsafe_allow_html=True)
    if r.summary:
        st.markdown(f"<p style='font-size:1.02rem'>{escape(r.summary)}</p>", unsafe_allow_html=True)

    rows = []
    if r.address:
        rows.append(("Address", escape(r.address)))
    if r.phone:
        rows.append(("Phone", f'<a href="tel:{escape(r.phone.replace(" ", ""))}">{escape(r.phone)}</a>'))
    if r.website and safe_url(r.website):
        rows.append(("Website", f'<a href="{safe_url(r.website)}" target="_blank" rel="noopener">{escape(r.website.split("//")[-1].rstrip("/"))}</a>'))
    if rows:
        st.markdown('<dl class="ba-kv">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>",
                    unsafe_allow_html=True)
    if r.hours:
        with st.expander("Opening hours"):
            st.markdown("\n".join(f"- {escape(h)}" for h in r.hours))

with right:
    with st.container(border=True):
        st.link_button("Get directions", directions_url(r, origin), type="primary", width="stretch",
                       icon=":material/directions:")
        saved = r.id in state.favorite_ids()
        st.button("♥ Saved to favorites" if saved else "♡ Save to favorites", width="stretch",
                  on_click=state.toggle_favorite, args=(r, city))
        if r.maps_uri:
            st.link_button("Open in Google Maps", r.maps_uri, width="stretch")
        try:
            engine = choose_engine(get_settings(), provider.allowed_map_engines)
            render_map(engine, city, [r], height=300, key="detail_map", controls=False)
        except ComplianceError as e:
            st.caption(str(e))

google_attribution([r], provider)
