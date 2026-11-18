"""Burger Atlas's own data: editorial picks (a YAML file) and favorites.

There is no database. Editor's picks live in ``config/curated.yaml`` (edit it
and redeploy). Favorites live in each visitor's browser (localStorage) — see
``ui/browser_bridge.py``. Only Google place IDs are ever stored, which Google
allows indefinitely; no Places content is persisted anywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

import yaml

from .settings import CONFIG_DIR

_PLACE_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{3,256}$")
_SLUG_RE = re.compile(r"^[a-z0-9\-]{1,64}$")
MAX_FAVORITES = 200


def is_valid_place_id(value: object) -> bool:
    return isinstance(value, str) and bool(_PLACE_ID_RE.match(value))


@dataclass(frozen=True)
class Favorite:
    place_id: str
    city_slug: str
    source: str = "google"

    def to_dict(self) -> dict:
        return {"place_id": self.place_id, "city_slug": self.city_slug, "source": self.source}


def parse_favorites(raw: object) -> list[Favorite]:
    """Validate favorites coming back from the browser (untrusted input)."""
    out: list[Favorite] = []
    seen: set[str] = set()
    if not isinstance(raw, list):
        return out
    for item in raw[:MAX_FAVORITES]:
        if not isinstance(item, dict):
            continue
        pid, city, src = item.get("place_id"), item.get("city_slug"), item.get("source", "google")
        if (is_valid_place_id(pid) and isinstance(city, str) and _SLUG_RE.match(city)
                and src in ("google", "demo") and pid not in seen):
            seen.add(pid)
            out.append(Favorite(pid, city, src))
    return out


@dataclass
class CuratedPlace:
    place_id: str
    city_slug: str
    district_slug: str | None = None
    categories: list[str] = field(default_factory=list)
    editor_note: str = ""
    featured: bool = False


@lru_cache(maxsize=1)
def _load_curated() -> dict[str, CuratedPlace]:
    path = CONFIG_DIR / "curated.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, CuratedPlace] = {}
    for city_slug, places in (raw.get("cities") or {}).items():
        for p in places or []:
            pid = p.get("place_id")
            if not is_valid_place_id(pid):
                continue
            out[pid] = CuratedPlace(
                place_id=pid,
                city_slug=city_slug,
                district_slug=p.get("district"),
                categories=list(p.get("categories") or []),
                editor_note=str(p.get("note") or ""),
                featured=bool(p.get("featured")),
            )
    return out


def curated_for(city_slug: str) -> dict[str, CuratedPlace]:
    return {k: v for k, v in _load_curated().items() if v.city_slug == city_slug}
