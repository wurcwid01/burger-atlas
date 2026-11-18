# Burger Atlas

**Find your next great burger.** A simple, map-first burger finder for Iloilo City, built with Streamlit and Google Maps.

- No database and no accounts. Favorites are saved in each visitor's own browser.
- It's built to fit inside Google's free monthly allowances.
- Without keys it runs on fictional sample data, so you can try it straight away.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pages
- **Explore**: map with rating pins and tap-to-preview cards. Filters cover the 7 districts, 5 burger styles, rating, price, open now and distance ("◎ Near me", "Search this area", or a radius around a district).
- **Restaurant Details**: photo, the editor's note, address, phone, website, hours, directions and a save button.
- **Favorites**: your saved spots, kept in this browser.
- **About**: data credits, terms and privacy.

---

## Go live on Streamlit Community Cloud (free)

### 1. Put the code on GitHub
Create a GitHub repository and upload this folder. `.streamlit/secrets.toml` is git-ignored, so your keys won't be uploaded.

### 2. Deploy
On share.streamlit.io, click **Create app**, pick your repo, and set the main file to `app.py`, then **Deploy**. Note your app's address, e.g. `https://burger-atlas.streamlit.app`.

### 3. Get two Google keys
At console.cloud.google.com:
1. Create a project and turn on billing. A card is required, but the limits in step 4 keep you within the free allowances.
2. Under **APIs & Services → Library**, enable **Places API (New)** and **Maps JavaScript API**.
3. Under **Google Maps Platform → Credentials**, create two keys:
   - **Server key**: API restriction **Places API (New)** only.
   - **Browser key**: API restriction **Maps JavaScript API** only. Under application restrictions choose **Websites** and add `https://YOUR-APP.streamlit.app/*` and `http://localhost:8501/*`.

### 4. Cap usage so it stays free (important)
Go to **Google Maps Platform → Quotas**. For each API, set these per-day limits:

| API | Quota | Daily limit | Why |
|---|---|---|---|
| Places API (New) | SearchTextRequest per day | **30** | Each visitor session uses about 2 searches |
| Places API (New) | GetPlaceRequest per day | **30** | One per restaurant details view |
| Places API (New) | GetPhotoMediaRequest per day | **30** | One photo per details view |
| Places API (New) | SearchNearbyRequest / Autocomplete… per day | **1** | Not used by the app |
| Maps JavaScript API | Map loads per day | **300** | One per page view with a map |

Each paid Places feature includes about 1,000 free requests a month (roughly 33 a day). If a limit is reached, the app shows a friendly message until the limit resets the next day, and nothing is charged. You can also add a **budget alert** under Billing → Budgets as a backup.

With these limits the app comfortably serves about 15 visitor sessions a day for free. If it gets popular, raise the limits; the cost beyond the free tier is listed on Google's pricing page.

### 5. Add the keys to Streamlit
In your app, go to **⋮ → Settings → Secrets** and paste:
```toml
GOOGLE_PLACES_API_KEY = "your-server-key"
GOOGLE_MAPS_BROWSER_KEY = "your-browser-key"
```
Save. The app restarts with real Iloilo burger spots on a Google map, and **About → Deployment status** confirms it.

---

## How it keeps costs low
- **One search per visit.** The app makes a single city-wide "burger restaurant in Iloilo City" search (2 pages, up to 40 places) and applies all filters on top of those results. Changing filters costs nothing extra.
- **No photos on cards.** Cards show Burger Atlas burger illustrations. A real Google photo loads only when someone opens a restaurant's details.
- **Short-term reuse.** Results are reused within a visitor's session for 30 minutes and are never stored long-term.

## Look & feel
The palette is **Warm Diner**: Ivory `#F7F5F0`, Charcoal `#25251F`, Terracotta `#BE6641`, Sage `#A8B5A0` and Mustard `#E3A93B`. The illustrations, map pins and headline underline are drawn in a hand-drawn marker style.

There are 12 illustrations in `static/illustrations/`, one set per burger style: double smash, gourmet with tomato, crispy chicken, plant-based with avocado, and budget in a paper wrapper. To regenerate or tweak them, run:
```bash
python tools/gen_illustrations.py static/illustrations
```

## Editor's picks
Add your favourite spots to `config/curated.yaml` with a place ID, an optional note, styles and an "Editor's pick" badge. Commit the change and the app redeploys. You can find place IDs with Google's Place ID Finder.

## Adding a city
Add a block to `config/cities.yaml` (centre, bounds, districts) and set `enabled: true`. A city switcher appears automatically. Bacolod and Cebu are included as disabled examples.

## Google rules this app follows
- Google restaurant data is only ever shown on a Google map. The app refuses to draw it on any other map, and the free demo map is used only for the fictional sample data.
- Nothing from Google is stored long-term. Favorites hold only place IDs, which Google allows to be kept.
- A "Google Maps" credit appears next to listings, and photographer credits appear under every photo.
- The About page links Google's Terms of Service and Privacy Policy.

## Project layout
```
app.py                      entry point
views/                      explore · details · favorites · about
config/                     cities.yaml · categories.yaml · curated.yaml
burger_atlas/
  providers/                Google Places (New) + demo data (swappable)
  services/discovery.py     search once → filter / rank locally
  maps/                     Google map + demo map, compliance guard
  ui/                       theme, cards, browser favorites
  store.py                  editor's picks + favorites validation
tests/                      python -m pytest -q
```
