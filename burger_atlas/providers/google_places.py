"""Google Places API (New) discovery provider.

Endpoints used:
* Text Search (New)   POST https://places.googleapis.com/v1/places:searchText
* Place Details (New) GET  https://places.googleapis.com/v1/places/{id}
* Place Photos (New)  GET  https://places.googleapis.com/v1/{photo}/media

Compliance notes (see README › Google Maps Platform compliance):
* The API key is sent as a header from the server; it never reaches the
  browser. Photos are resolved with ``skipHttpRedirect=true`` so the browser
  only ever sees Google's short-lived ``photoUri``.
* Responses are reused only within one user session (``SessionCache``) and
  never persisted. Only place IDs are stored in the database.
* Photo author attributions and third-party ``attributions`` are carried on
  the models so the UI can display them next to the content.
* Field masks are kept minimal: the fields requested decide the billing SKU.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import requests

from ..models import Attribution, City, LatLng, Photo, Restaurant
from .base import ProviderError, ProviderQuery
from .session_cache import SessionCache

BASE = "https://places.googleapis.com/v1"

SEARCH_FIELDS = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.rating",
        "places.userRatingCount",
        "places.priceLevel",
        "places.primaryType",
        "places.types",
        "places.photos",
        "places.googleMapsUri",
        "places.currentOpeningHours.openNow",
        "places.editorialSummary",
        "places.attributions",
        "nextPageToken",
    ]
)

DETAIL_FIELDS = ",".join(
    [
        "id",
        "displayName",
        "formattedAddress",
        "location",
        "rating",
        "userRatingCount",
        "priceLevel",
        "primaryType",
        "types",
        "photos",
        "googleMapsUri",
        "websiteUri",
        "nationalPhoneNumber",
        "regularOpeningHours.weekdayDescriptions",
        "currentOpeningHours.openNow",
        "editorialSummary",
        "attributions",
    ]
)

PRICE_LEVELS = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


def parse_place(p: dict[str, Any]) -> Restaurant:
    loc = p.get("location") or {}
    photos = []
    for ph in p.get("photos", []) or []:
        photos.append(
            Photo(
                ref=ph.get("name", ""),
                width=int(ph.get("widthPx", 0) or 0),
                height=int(ph.get("heightPx", 0) or 0),
                attributions=[
                    Attribution(
                        name=a.get("displayName", ""),
                        uri=a.get("uri", ""),
                        photo_uri=a.get("photoUri", ""),
                    )
                    for a in ph.get("authorAttributions", []) or []
                ],
            )
        )
    return Restaurant(
        id=p["id"],
        name=(p.get("displayName") or {}).get("text", "Unnamed"),
        source="google",
        location=LatLng(float(loc.get("latitude", 0)), float(loc.get("longitude", 0))),
        address=p.get("formattedAddress", ""),
        rating=p.get("rating"),
        rating_count=int(p.get("userRatingCount", 0) or 0),
        price_level=PRICE_LEVELS.get(p.get("priceLevel", "")),
        primary_type=p.get("primaryType", ""),
        types=list(p.get("types", []) or []),
        summary=(p.get("editorialSummary") or {}).get("text", ""),
        phone=p.get("nationalPhoneNumber", ""),
        website=p.get("websiteUri", ""),
        maps_uri=p.get("googleMapsUri", ""),
        open_now=(p.get("currentOpeningHours") or {}).get("openNow"),
        hours=list((p.get("regularOpeningHours") or {}).get("weekdayDescriptions", []) or []),
        photos=photos,
        attributions=[
            Attribution(name=a.get("provider", ""), uri=a.get("providerUri", ""))
            for a in p.get("attributions", []) or []
            if a.get("provider")
        ],
    )


def build_search_body(query: ProviderQuery, page_token: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "textQuery": query.text,
        "pageSize": 20,
        "languageCode": query.language,
        "regionCode": query.region,
    }
    if query.restrict_to is not None:
        b = query.restrict_to
        body["locationRestriction"] = {
            "rectangle": {
                "low": {"latitude": b.south, "longitude": b.west},
                "high": {"latitude": b.north, "longitude": b.east},
            }
        }
    elif query.bias_center is not None:
        body["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": query.bias_center.lat,
                    "longitude": query.bias_center.lng,
                },
                "radius": float(min(query.bias_radius_m or 3000, 50_000)),
            }
        }
    if query.min_rating:
        # API accepts 0.0–5.0 in 0.5 steps.
        body["minRating"] = round(query.min_rating * 2) / 2
    if query.open_now:
        body["openNow"] = True
    if page_token:
        body["pageToken"] = page_token
    return body


class GooglePlacesProvider:
    name = "google"
    content_source = "google"
    attribution_label = "Google Maps"
    allowed_map_engines = frozenset({"google"})

    def __init__(self, api_key: str, session_ttl_s: int = 900, timeout_s: float = 10.0):
        if not api_key:
            raise ProviderError("Google Places API key is not configured.")
        self._key = api_key
        self._timeout = timeout_s
        self._http = requests.Session()
        self._search_cache = SessionCache("places_search", ttl_s=session_ttl_s)
        self._detail_cache = SessionCache("places_details", ttl_s=session_ttl_s)
        self._photo_cache = SessionCache("places_photos", ttl_s=min(session_ttl_s, 3000), max_items=400)

    # -- HTTP ------------------------------------------------------------
    def _headers(self, field_mask: str | None = None) -> dict[str, str]:
        h = {"X-Goog-Api-Key": self._key, "Content-Type": "application/json"}
        if field_mask:
            h["X-Goog-FieldMask"] = field_mask
        return h

    def _call(self, method: str, url: str, **kw) -> dict[str, Any]:
        try:
            r = self._http.request(method, url, timeout=self._timeout, **kw)
        except requests.RequestException as e:
            raise ProviderError(f"Couldn't reach Google Places: {e}") from e
        if r.status_code == 429:
            raise ProviderError(
                "Burger Atlas has reached today's free lookup limit — please check back tomorrow."
            )
        if r.status_code != 200:
            try:
                msg = r.json().get("error", {}).get("message", r.text[:200])
            except ValueError:
                msg = r.text[:200]
            raise ProviderError(f"Google Places error {r.status_code}: {msg}")
        return r.json()

    # -- Provider API ----------------------------------------------------
    def search(self, city: City, query: ProviderQuery) -> list[Restaurant]:
        key = hashlib.sha1(
            json.dumps([city.slug, build_search_body(query), query.max_pages], sort_keys=True).encode()
        ).hexdigest()
        return self._search_cache.get_or_set(key, lambda: self._search_uncached(query))

    def _search_uncached(self, query: ProviderQuery) -> list[Restaurant]:
        out: list[Restaurant] = []
        token: str | None = None
        for _ in range(max(1, query.max_pages)):
            data = self._call(
                "POST",
                f"{BASE}/places:searchText",
                headers=self._headers(SEARCH_FIELDS),
                json=build_search_body(query, token),
            )
            out.extend(parse_place(p) for p in data.get("places", []) or [])
            token = data.get("nextPageToken")
            if not token:
                break
        return out

    def get_details(self, place_id: str, city: City) -> Restaurant | None:
        if not place_id or "/" in place_id:
            return None

        def fetch():
            data = self._call(
                "GET",
                f"{BASE}/places/{place_id}",
                headers=self._headers(DETAIL_FIELDS),
                params={"languageCode": "en", "regionCode": city.country_code},
            )
            return parse_place(data)

        return self._detail_cache.get_or_set(place_id, fetch)

    def resolve_photo(self, photo: Photo, max_width: int = 800) -> str:
        if photo.url:
            return photo.url
        if not photo.ref.startswith("places/"):
            return ""

        def fetch():
            data = self._call(
                "GET",
                f"{BASE}/{photo.ref}/media",
                headers=self._headers(),
                params={"maxWidthPx": max_width, "skipHttpRedirect": "true"},
            )
            return data.get("photoUri", "")

        try:
            photo.url = self._photo_cache.get_or_set(f"{photo.ref}@{max_width}", fetch)
        except ProviderError:
            photo.url = ""
        return photo.url
