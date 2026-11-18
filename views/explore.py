"""Explore — the map-first discovery page."""

from html import escape

import streamlit as st

from burger_atlas.geo import enabled_cities, format_distance, load_categories
from burger_atlas.maps.component import render_map
from burger_atlas.maps.engines import ComplianceError, choose_engine
from burger_atlas.models import LatLng, SearchFilters
from burger_atlas.services.discovery import discover
from burger_atlas.settings import get_settings
from burger_atlas.ui import state
from burger_atlas.ui.cards import card_grid, google_attribution, photo_url

PAGE_SIZE = 9
RATING_OPTIONS = {"Any": 0.0, "4.0+": 4.0, "4.3+": 4.3, "4.5+": 4.5}
SORTS = {"Recommended": "recommended", "Top rated": "rating", "Nearest": "distance"}

ss = st.session_state
settings = get_settings()

# Apply changes requested by map events on the previous run, before the
# widgets that own these keys are created.
for k, v in (ss.pop("_pending", None) or {}).items():
    ss[k] = v
for k, v in {"f_radius": 3.0, "f_rating": "Any", "f_sort": "Recommended", "f_near": "anywhere"}.items():
    ss.setdefault(k, v)

# ------------------------------------------------------------------ city
cities = enabled_cities()
if len(cities) > 1:
    ss.setdefault("city_slug", (settings.default_city or cities[0].slug))
    st.selectbox("City", [c.slug for c in cities], key="city_slug",
                 format_func=lambda s: next(c.name for c in cities if c.slug == s))
city = state.current_city()
provider = state.provider()
categories = load_categories()

st.markdown(
    f"""<div class="ba-hero">
      <div class="ba-eyebrow-lg">{escape(city.name)} · {escape(city.region)}</div>
      <h1>Find your next <span class="ba-mark">great burger.</span></h1>
      <p>A curated map of the city's best patties — from heritage-street smash counters
      to craft kitchens. Tap a pin to preview, then dig into the details.</p>
    </div>""",
    unsafe_allow_html=True,
)
st.write("")

# ------------------------------------------------------------------ filters
district_names = {d.slug: d.name for d in city.districts}
st.pills("Neighbourhood", list(district_names), selection_mode="multi", key="f_districts",
         format_func=district_names.get, label_visibility="collapsed")

c_style, c_near, c_refine = st.columns([7, 1.4, 1.2], vertical_alignment="center")
with c_style:
    cat_labels = {c.slug: c.label for c in categories}
    st.pills("Style", list(cat_labels), selection_mode="multi", key="f_categories",
             format_func=cat_labels.get, label_visibility="collapsed")

near_options = {"anywhere": "Anywhere in the city"}
if ss.get("user_loc"):
    near_options["me"] = "My location"
if ss.get("area_loc"):
    near_options["area"] = "Map area"
near_options.update({f"d:{d.slug}": f"Centre of {d.name}" for d in city.districts})
if ss.get("f_near") not in near_options:
    ss["f_near"] = "anywhere"

with c_near:
    near_label = "Distance" if ss.get("f_near", "anywhere") == "anywhere" else f"Within {ss.get('f_radius', 3.0):g} km"
    with st.popover(near_label, width="stretch", icon=":material/near_me:"):
        st.selectbox("Distance from", list(near_options), key="f_near", format_func=near_options.get)
        st.slider("Radius (km)", 0.5, 8.0, step=0.5, key="f_radius",
                  disabled=ss.get("f_near", "anywhere") == "anywhere")
        st.caption("Tip: tap **◎ Near me** on the map to use your location.")

with c_refine:
    with st.popover("Refine", width="stretch", icon=":material/tune:"):
        st.segmented_control("Minimum rating", list(RATING_OPTIONS), key="f_rating")
        st.pills("Price", [1, 2, 3, 4], selection_mode="multi", key="f_price",
                 format_func=lambda n: city.currency_symbol * n)
        st.toggle("Hide places with no price info", key="f_strict_price")
        st.toggle("Open now", key="f_open")
        st.selectbox("Sort by", list(SORTS), key="f_sort")

# ------------------------------------------------------------------ query
near = ss.get("f_near", "anywhere")
origin: LatLng | None = None
if near == "me":
    origin = ss.get("user_loc")
elif near == "area":
    origin = ss.get("area_loc")
elif near.startswith("d:") and city.district(near[2:]):
    origin = city.district(near[2:]).center
radius_m = int(ss.get("f_radius", 3.0) * 1000) if origin else None

filters = SearchFilters(
    city_slug=city.slug,
    districts=list(ss.get("f_districts") or []),
    categories=list(ss.get("f_categories") or []),
    min_rating=RATING_OPTIONS.get(ss.get("f_rating") or "Any", 0.0),
    price_levels=list(ss.get("f_price") or []),
    strict_price=bool(ss.get("f_strict_price")),
    open_now=bool(ss.get("f_open")),
    origin=origin,
    radius_m=radius_m,
    sort=SORTS.get(ss.get("f_sort") or "Recommended", "recommended"),
)
if filters.sort == "distance" and not origin:
    filters.sort = "recommended"

with st.spinner("Finding burgers…"):
    result = discover(provider, city, filters, max_pages=settings.places_max_pages)
restaurants = result.restaurants

# Google photos are billed per request, so cards use Burger Atlas illustrations
# and real photos load only on the details page. (Demo photos are local and free.)
limit = ss.get("cards_limit", PAGE_SIZE)
if provider.name == "demo":
    for r in restaurants[:limit]:
        photo_url(provider, r.hero_photo)

# ------------------------------------------------------------------ map
try:
    engine = choose_engine(settings, provider.allowed_map_engines)
    badge = "Sample data · fictional restaurants" if provider.name == "demo" else ""
    events = render_map(
        engine, city, restaurants,
        origin=origin, radius_m=radius_m,
        focus_districts=filters.districts,
        selected_id=ss.get("map_selected"), select_nonce=ss.get("map_nonce", 0),
        height=560, badge=badge,
    )
except ComplianceError as e:
    st.error(str(e))
    events = None

if events:
    if events.open_details:
        state.open_details(events.open_details)
    if events.locate:
        ss["user_loc"] = LatLng(float(events.locate["lat"]), float(events.locate["lng"]))
        ss["_pending"] = {"f_near": "me", "f_sort": "Nearest", "cards_limit": PAGE_SIZE}
        st.rerun()
    if events.search_area:
        a = events.search_area
        ss["area_loc"] = LatLng(float(a["lat"]), float(a["lng"]))
        km = min(max(round(float(a["radius_m"]) / 500) / 2, 0.5), 8.0)
        ss["_pending"] = {"f_near": "area", "f_radius": km, "cards_limit": PAGE_SIZE}
        st.rerun()

for w in result.warnings:
    st.caption(f"⚠️ {w}")

# ------------------------------------------------------------------ results
def show_on_map(place_id: str) -> None:
    ss["map_selected"] = place_id
    ss["map_nonce"] = ss.get("map_nonce", 0) + 1


def clear_filters() -> None:
    for k in ("f_districts", "f_categories", "f_price", "f_strict_price", "f_open"):
        ss.pop(k, None)
    ss["f_rating"] = "Any"
    ss["f_sort"] = "Recommended"
    ss["f_near"] = "anywhere"
    ss["cards_limit"] = PAGE_SIZE


scope = []
if filters.districts:
    scope.append(", ".join(district_names[d] for d in filters.districts))
if origin:
    scope.append(f"within {format_distance(radius_m)} of {near_options.get(near, 'here').replace('Centre of ', '')}")
head, clear = st.columns([5, 1], vertical_alignment="bottom")
head.markdown(
    f"### {len(restaurants)} burger spot{'s' if len(restaurants) != 1 else ''}"
    + (f"<span class='ba-small'> &nbsp;{escape(' · '.join(scope))}</span>" if scope else ""),
    unsafe_allow_html=True,
)
active = any(ss.get(k) for k in ("f_districts", "f_categories", "f_price", "f_open")) or near != "anywhere" \
    or (ss.get("f_rating") or "Any") != "Any"
if active:
    clear.button("Clear filters", on_click=clear_filters, type="tertiary", width="stretch")

if not restaurants:
    st.markdown(
        "<p class='ba-muted'>No burgers match that combination yet. Try widening the radius, "
        "removing a style, or exploring another neighbourhood.</p>",
        unsafe_allow_html=True,
    )
else:
    card_grid(restaurants[:limit], city, provider, key_prefix="ex", on_show_on_map=show_on_map)
    if len(restaurants) > limit:
        st.button(f"Show more ({len(restaurants) - limit} more)",
                  on_click=lambda: ss.update(cards_limit=limit + PAGE_SIZE))
    google_attribution(restaurants[:limit], provider)
