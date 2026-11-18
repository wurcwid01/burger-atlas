"""Per-session, in-memory reuse of provider responses.

Streamlit reruns the whole script on every interaction. Without a small
cache, every click would re-bill the same Places request. This cache:

* lives only in the current user's ``st.session_state`` (never shared
  between users, never written to disk or to the database);
* expires entries after ``ttl_s`` seconds (default 15 minutes);
* is size-capped.

Only Google place IDs are stored persistently anywhere in Burger Atlas
(they are exempt from the Places caching restrictions). Review your own
Google Maps Platform agreement before changing this behaviour.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Callable

_FALLBACK: dict[str, OrderedDict] = {}


def _store(namespace: str) -> OrderedDict:
    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is not None:
            key = f"__ba_cache_{namespace}"
            if key not in st.session_state:
                st.session_state[key] = OrderedDict()
            return st.session_state[key]
    except Exception:
        pass
    return _FALLBACK.setdefault(namespace, OrderedDict())


class SessionCache:
    def __init__(self, namespace: str, ttl_s: int = 900, max_items: int = 200):
        self.namespace = namespace
        self.ttl_s = ttl_s
        self.max_items = max_items

    def get_or_set(self, key: str, fn: Callable[[], Any]) -> Any:
        store = _store(self.namespace)
        now = time.time()
        hit = store.get(key)
        if hit is not None and now - hit[0] < self.ttl_s:
            store.move_to_end(key)
            return hit[1]
        value = fn()
        store[key] = (now, value)
        while len(store) > self.max_items:
            store.popitem(last=False)
        return value

    def clear(self) -> None:
        _store(self.namespace).clear()
