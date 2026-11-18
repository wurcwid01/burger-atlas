// Burger Atlas interactive map — Streamlit Components v2 module.
//
// One UI layer (pins, preview card, locate / search-this-area controls)
// on top of two interchangeable engines:
//   * "google"  — Google Maps JavaScript API (required for Google Places content)
//   * "leaflet" — Leaflet + CARTO tiles, ONLY for fictional demo data
// Python enforces which engine may show which content (maps/registry.py);
// this file re-checks it defensively before drawing anything.
//
// All text is inserted with textContent — never innerHTML — because place
// names and addresses are external data.

const GOOGLE_SRC_ID = "ba-google-maps-loader";

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = String(text);
  return n;
}

// ---------------------------------------------------------------- loaders
function loadGoogle(key) {
  if (window.__baGoogle) return window.__baGoogle;
  window.__baGoogle = new Promise((resolve, reject) => {
    if (window.google && window.google.maps && window.google.maps.importLibrary) {
      resolve(window.google.maps);
      return;
    }
    const cb = "__baGoogleReady";
    window[cb] = () => resolve(window.google.maps);
    const s = document.createElement("script");
    s.id = GOOGLE_SRC_ID;
    const p = new URLSearchParams({ key, v: "weekly", loading: "async", callback: cb, libraries: "marker" });
    s.src = "https://maps.googleapis.com/maps/api/js?" + p.toString();
    s.async = true;
    s.onerror = () => { window.__baGoogle = null; reject(new Error("Google Maps failed to load")); };
    document.head.appendChild(s);
  });
  return window.__baGoogle;
}

function loadLeaflet() {
  if (window.__baLeaflet) return window.__baLeaflet;
  window.__baLeaflet = new Promise((resolve, reject) => {
    if (window.L) { resolve(window.L); return; }
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(css);
    const s = document.createElement("script");
    s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    s.onload = () => resolve(window.L);
    s.onerror = () => { window.__baLeaflet = null; reject(new Error("Leaflet failed to load")); };
    document.head.appendChild(s);
  });
  return window.__baLeaflet;
}

// ---------------------------------------------------------------- pins
function pinElement(m, selected) {
  const pin = el("div", "ba-pin");
  if (selected) pin.classList.add("is-selected");
  if (m.featured) pin.classList.add("is-featured");
  pin.appendChild(el("span", "ba-pin-label", m.rating ? Number(m.rating).toFixed(1) : "•"));
  pin.setAttribute("role", "button");
  pin.setAttribute("aria-label", m.name);
  pin.title = m.name;
  return pin;
}

function userDot() {
  const d = el("div", "ba-user-dot");
  d.appendChild(el("span", "ba-user-pulse"));
  return d;
}

// ---------------------------------------------------------------- engines
function googleEngine(gmaps, container, view) {
  const map = new gmaps.Map(container, {
    center: view.center,
    zoom: view.zoom,
    mapId: view.mapId || "DEMO_MAP_ID",
    disableDefaultUI: true,
    zoomControl: true,
    zoomControlOptions: { position: gmaps.ControlPosition.RIGHT_BOTTOM },
    clickableIcons: false,
    gestureHandling: "cooperative",
    colorScheme: "LIGHT",
  });
  const markers = new Map();
  let overlays = [];
  const AM = gmaps.marker.AdvancedMarkerElement;
  return {
    setMarkers(list, selectedId, onClick) {
      markers.forEach((mk) => (mk.map = null));
      markers.clear();
      list.forEach((m) => {
        const mk = new AM({
          map,
          position: { lat: m.lat, lng: m.lng },
          content: pinElement(m, m.id === selectedId),
          title: m.name,
          zIndex: m.id === selectedId ? 1000 : m.featured ? 500 : 1,
          gmpClickable: true,
        });
        mk.addListener("click", () => onClick(m.id));
        markers.set(m.id, mk);
      });
    },
    highlight(selectedId, list) {
      list.forEach((m) => {
        const mk = markers.get(m.id);
        if (!mk) return;
        mk.content = pinElement(m, m.id === selectedId);
        mk.zIndex = m.id === selectedId ? 1000 : m.featured ? 500 : 1;
      });
    },
    setOverlays(user, radius, focus) {
      overlays.forEach((o) => (o.setMap ? o.setMap(null) : (o.map = null)));
      overlays = [];
      if (focus) {
        focus.forEach((f) =>
          overlays.push(new gmaps.Circle({ map, center: f.center, radius: f.radius_m, strokeColor: "#A8B5A0",
            strokeOpacity: 0.9, strokeWeight: 1.5, fillColor: "#A8B5A0", fillOpacity: 0.12, clickable: false }))
        );
      }
      if (user) {
        overlays.push(new AM({ map, position: user, content: userDot(), zIndex: 2000 }));
        if (radius) overlays.push(new gmaps.Circle({ map, center: user, radius, strokeColor: "#BE6641",
          strokeOpacity: 0.6, strokeWeight: 1, fillColor: "#BE6641", fillOpacity: 0.05, clickable: false }));
      }
    },
    fit(points, fallback) {
      if (points.length > 1) {
        const b = new gmaps.LatLngBounds();
        points.forEach((p) => b.extend(p));
        map.fitBounds(b, 48);
      } else if (points.length === 1) { map.setCenter(points[0]); map.setZoom(15); }
      else { map.setCenter(fallback.center); map.setZoom(fallback.zoom); }
    },
    panTo(p) { map.panTo(p); },
    onUserMove(cb) { map.addListener("dragend", cb); },
    centerRadius() {
      const c = map.getCenter(); const b = map.getBounds();
      const ne = b ? b.getNorthEast() : c;
      return { lat: c.lat(), lng: c.lng(), corner: { lat: ne.lat(), lng: ne.lng() } };
    },
  };
}

function leafletEngine(L, container, view) {
  const map = L.map(container, { zoomControl: false, attributionControl: true, scrollWheelZoom: false })
    .setView([view.center.lat, view.center.lng], view.zoom);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 19, subdomains: "abcd",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  }).addTo(map);
  const markers = new Map();
  let overlays = [];
  const icon = (m, sel) => L.divIcon({ className: "ba-leaflet-icon", html: pinElement(m, sel).outerHTML, iconSize: [40, 40], iconAnchor: [20, 40] });
  return {
    setMarkers(list, selectedId, onClick) {
      markers.forEach((mk) => mk.remove());
      markers.clear();
      list.forEach((m) => {
        const mk = L.marker([m.lat, m.lng], { icon: icon(m, m.id === selectedId), title: m.name, riseOnHover: true,
          zIndexOffset: m.id === selectedId ? 1000 : m.featured ? 500 : 0 }).addTo(map);
        mk.on("click", () => onClick(m.id));
        markers.set(m.id, mk);
      });
    },
    highlight(selectedId, list) {
      list.forEach((m) => {
        const mk = markers.get(m.id);
        if (!mk) return;
        mk.setIcon(icon(m, m.id === selectedId));
        mk.setZIndexOffset(m.id === selectedId ? 1000 : m.featured ? 500 : 0);
      });
    },
    setOverlays(user, radius, focus) {
      overlays.forEach((o) => o.remove());
      overlays = [];
      (focus || []).forEach((f) => overlays.push(L.circle([f.center.lat, f.center.lng], { radius: f.radius_m,
        color: "#A8B5A0", weight: 1.5, fillColor: "#A8B5A0", fillOpacity: 0.12, interactive: false }).addTo(map)));
      if (user) {
        overlays.push(L.marker([user.lat, user.lng], { icon: L.divIcon({ className: "ba-leaflet-icon", html: userDot().outerHTML, iconSize: [18, 18] }), interactive: false }).addTo(map));
        if (radius) overlays.push(L.circle([user.lat, user.lng], { radius, color: "#BE6641", weight: 1, opacity: 0.6, fillOpacity: 0.05, interactive: false }).addTo(map));
      }
    },
    fit(points, fallback) {
      if (points.length > 1) map.fitBounds(points.map((p) => [p.lat, p.lng]), { padding: [48, 48] });
      else if (points.length === 1) map.setView([points[0].lat, points[0].lng], 15);
      else map.setView([fallback.center.lat, fallback.center.lng], fallback.zoom);
    },
    panTo(p) { map.panTo([p.lat, p.lng]); },
    onUserMove(cb) { map.on("dragend", cb); },
    centerRadius() {
      const c = map.getCenter(); const ne = map.getBounds().getNorthEast();
      return { lat: c.lat, lng: c.lng, corner: { lat: ne.lat, lng: ne.lng } };
    },
    invalidate() { setTimeout(() => map.invalidateSize(), 50); },
  };
}

function haversine(a, b) {
  const R = 6371000, r = Math.PI / 180;
  const dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// ---------------------------------------------------------------- preview card
function renderPreview(box, m, data, setTriggerValue, onClose) {
  box.replaceChildren();
  if (!m) { box.hidden = true; return; }
  box.hidden = false;

  const close = el("button", "ba-preview-close", "×");
  close.setAttribute("aria-label", "Close preview");
  close.onclick = onClose;

  const media = el("div", "ba-preview-media");
  if (m.photo) {
    const img = el("img");
    img.src = m.photo; img.alt = ""; img.loading = "lazy"; img.referrerPolicy = "no-referrer";
    media.appendChild(img);
  } else {
    media.classList.add("is-empty");
  }

  const body = el("div", "ba-preview-body");
  if (m.featured) body.appendChild(el("div", "ba-eyebrow", "Editor's pick"));
  body.appendChild(el("div", "ba-preview-title", m.name));
  const meta = [];
  if (m.rating) meta.push("★ " + Number(m.rating).toFixed(1) + (m.rating_count ? " (" + m.rating_count + ")" : ""));
  if (m.price) meta.push(m.price);
  if (m.district) meta.push(m.district);
  if (m.distance) meta.push(m.distance);
  body.appendChild(el("div", "ba-preview-meta", meta.join("  ·  ")));
  if (m.categories && m.categories.length) {
    const chips = el("div", "ba-chips");
    m.categories.slice(0, 3).forEach((c) => chips.appendChild(el("span", "ba-chip", c)));
    body.appendChild(chips);
  }
  const actions = el("div", "ba-preview-actions");
  const details = el("button", "ba-btn ba-btn-primary", "View details");
  details.onclick = () => setTriggerValue("open_details", m.id);
  const dir = el("a", "ba-btn ba-btn-ghost", "Directions");
  dir.href = m.directions; dir.target = "_blank"; dir.rel = "noopener";
  actions.append(details, dir);
  body.appendChild(actions);
  if (m.photo_credit) {
    const credit = el("div", "ba-photo-credit");
    credit.appendChild(document.createTextNode("Photo: "));
    if (m.photo_credit_uri) {
      const a = el("a", null, m.photo_credit); a.href = m.photo_credit_uri; a.target = "_blank"; a.rel = "noopener";
      credit.appendChild(a);
    } else credit.appendChild(document.createTextNode(m.photo_credit));
    body.appendChild(credit);
  }
  box.append(close, media, body);
}

// ---------------------------------------------------------------- main
export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  if (!data) return;
  const root = parentElement.querySelector(".ba-map-root");
  if (!root) return;
  root.style.height = (data.height || 560) + "px";

  const S = root.__ba || (root.__ba = { engine: null, engineName: null, idsKey: null, selected: null, data: null, loading: null });
  const hash = JSON.stringify(data);
  if (S.lastHash === hash) return;
  S.lastHash = hash;
  S.data = data;

  // Defensive compliance check (Python is the primary guard).
  if (data.engine !== "google" && data.markers.some((m) => m.source === "google")) {
    root.querySelector(".ba-map").textContent = "Google Places content can only be shown on a Google map.";
    return;
  }

  const mapEl = root.querySelector(".ba-map");
  const preview = root.querySelector(".ba-preview");
  const locateBtn = root.querySelector(".ba-locate");
  const areaBtn = root.querySelector(".ba-search-area");
  const badge = root.querySelector(".ba-badge");
  root.querySelector(".ba-right").style.display = data.controls === false ? "none" : "";
  badge.hidden = !data.badge;
  badge.textContent = data.badge || "";

  const byId = () => new Map(S.data.markers.map((m) => [m.id, m]));
  const select = (id) => {
    S.selected = id;
    S.engine.highlight(id, S.data.markers);
    const m = byId().get(id);
    renderPreview(preview, m, S.data, setTriggerValue, () => select(null));
    if (m) S.engine.panTo({ lat: m.lat, lng: m.lng });
  };

  locateBtn.onclick = () => {
    if (!navigator.geolocation) { locateBtn.textContent = "Location unavailable"; return; }
    locateBtn.classList.add("is-busy");
    navigator.geolocation.getCurrentPosition(
      (pos) => { locateBtn.classList.remove("is-busy");
        setTriggerValue("locate", { lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy }); },
      () => { locateBtn.classList.remove("is-busy"); locateBtn.title = "Location permission denied"; locateBtn.classList.add("is-denied"); },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  };
  areaBtn.onclick = () => {
    const cr = S.engine.centerRadius();
    const radius = Math.min(Math.max(haversine(cr, cr.corner) * 0.8, 600), 8000);
    areaBtn.hidden = true;
    setTriggerValue("search_area", { lat: cr.lat, lng: cr.lng, radius_m: Math.round(radius) });
  };

  const draw = () => {
    const d = S.data;
    const idsKey = d.markers.map((m) => m.id).join("|") + "@" + (d.fitKey || "");
    const markersChanged = idsKey !== S.idsKey;
    if (markersChanged) {
      S.engine.setMarkers(d.markers, d.selected_id || null, (id) => select(id));
      S.idsKey = idsKey;
      if (d.fit !== false) S.engine.fit(d.markers.map((m) => ({ lat: m.lat, lng: m.lng })), { center: d.center, zoom: d.zoom });
    }
    S.engine.setOverlays(d.user || null, d.radius_m || null, d.focus || null);
    if (d.selected_id && (d.selected_id !== S.selected || d.select_nonce !== S.nonce)) {
      S.nonce = d.select_nonce;
      select(d.selected_id);
    }
    else if (markersChanged) { S.selected = null; renderPreview(preview, null); }
  };

  if (S.engine && S.engineName === data.engine) { draw(); return; }

  const view = { center: data.center, zoom: data.zoom, mapId: data.map_id };
  const boot = data.engine === "google"
    ? loadGoogle(data.browser_key).then((g) => googleEngine(g, mapEl, view))
    : loadLeaflet().then((L) => leafletEngine(L, mapEl, view));
  boot.then((engine) => {
    S.engine = engine; S.engineName = data.engine;
    engine.onUserMove(() => { areaBtn.hidden = false; });
    if (engine.invalidate) engine.invalidate();
    draw();
  }).catch((e) => {
    mapEl.replaceChildren(el("div", "ba-map-error", e.message + " — check your connection or API key."));
  });
}
