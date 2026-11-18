"""Visual identity: palette, typography and global CSS overrides."""

from __future__ import annotations

import streamlit as st

IVORY = "#F7F5F0"
CHARCOAL = "#25251F"
TERRACOTTA = "#BE6641"
SAGE = "#A8B5A0"
MUSTARD = "#E3A93B"
MUTED = "#6B6A60"
LINE = "rgba(37,37,31,.10)"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');

.stApp, .stMarkdown, input, textarea {{
  font-family: "Inter", system-ui, -apple-system, sans-serif;
}}
.stApp {{ background: {IVORY}; color: {CHARCOAL}; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1240px; }}
h1, h2, h3, .ba-serif {{ font-family: "Fraunces", Georgia, serif !important; color: {CHARCOAL}; letter-spacing: -0.01em; }}
footer, #MainMenu {{ visibility: hidden; }}

/* --- brand header --- */
.ba-brand {{ display:flex; align-items:baseline; gap:.6rem; margin-bottom:.2rem; }}
.ba-wordmark {{ font: 600 1.05rem/1 "Fraunces", Georgia, serif; letter-spacing: .02em; color: {CHARCOAL}; }}
.ba-dot {{ width:8px; height:8px; border-radius:50%; background:{TERRACOTTA}; display:inline-block; transform: translateY(-1px); }}
.ba-eyebrow-lg {{ font-size:.72rem; font-weight:600; letter-spacing:.16em; text-transform:uppercase; color:{TERRACOTTA}; }}
.ba-hero h1 {{ font-size: clamp(2.1rem, 4.4vw, 3.4rem); line-height: 1.04; margin: .35rem 0 .5rem; font-weight: 600; }}
.ba-hero p {{ color: {MUTED}; font-size: 1.02rem; max-width: 40rem; margin: 0; }}
.ba-muted {{ color: {MUTED}; }}
/* marker-pen underline */
.ba-mark {{
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 20' preserveAspectRatio='none'%3E%3Cpath d='M4 13 C48 6 118 17 196 8' stroke='%23E3A93B' stroke-width='10' fill='none' stroke-linecap='round' opacity='.9'/%3E%3C/svg%3E") no-repeat left 92% / 100% .38em;
  padding: 0 .05em;
}}
.ba-small {{ font-size: .8rem; color: {MUTED}; }}
.ba-rule {{ height:1px; background:{LINE}; margin: 1.4rem 0; border:0; }}

/* --- widgets --- */
[data-testid="stPills"] button, [data-testid="stBaseButton-pills"], [data-testid="stBaseButton-pillsActive"] {{
  border-radius: 999px !important;
}}
[data-testid="stBaseButton-pillsActive"] {{
  background: {CHARCOAL} !important; color: {IVORY} !important; border-color: {CHARCOAL} !important;
}}
.stButton > button, .stLinkButton > a, .stDownloadButton > button {{
  border-radius: 10px; font-weight: 500;
}}
.stButton > button[kind="primary"], .stLinkButton > a[kind="primary"] {{
  background: {TERRACOTTA}; border-color: {TERRACOTTA};
}}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color: {LINE} !important; border-radius: 18px !important; background: #FBFAF6; }}
[data-testid="stPopoverButton"] {{ border-radius: 999px; }}

/* --- restaurant card --- */
.ba-card-media {{
  position: relative; aspect-ratio: 4 / 3; border-radius: 14px; overflow: hidden; background: {IVORY}; margin-bottom: .7rem;
  border: 1px solid {LINE};
}}
.ba-card-media img {{ width:100%; height:100%; object-fit:cover; display:block; transition: transform .4s ease; }}
.ba-card-media:hover img {{ transform: scale(1.03); }}
.ba-card-tag {{
  position:absolute; top:10px; left:10px; background: {MUSTARD}; color:{CHARCOAL}; border: 1.5px solid {CHARCOAL};
  font-size:.68rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; padding:5px 9px; border-radius:999px;
}}
.ba-card-title {{ font: 600 1.15rem/1.2 "Fraunces", Georgia, serif; margin: 0 0 .2rem; color:{CHARCOAL}; }}
.ba-card-meta {{ font-size:.82rem; color:{MUTED}; margin-bottom:.45rem; }}
.ba-star {{ color:{TERRACOTTA}; }}
.ba-chiprow {{ display:flex; flex-wrap:wrap; gap:4px; margin-bottom:.5rem; }}
.ba-chip2 {{ font-size:.7rem; padding:3px 9px; border-radius:999px; background: rgba(168,181,160,.28); color:#3f4a39; }}
.ba-note {{ font-size:.84rem; color:{CHARCOAL}; border-left: 2px solid {TERRACOTTA}; padding-left:.6rem; margin:.3rem 0 .4rem; }}
.ba-credit {{ font-size:.68rem; color:#8a897e; margin-top:-.4rem; margin-bottom:.4rem; }}
.ba-credit a {{ color: inherit; }}
.ba-attrib {{ font-size:.75rem; color:{MUTED}; margin-top:.6rem; }}

/* --- details --- */
.ba-gallery {{ display:grid; grid-template-columns: 2fr 1fr; gap:10px; height: clamp(240px, 38vw, 440px); }}
.ba-gallery.is-single {{ grid-template-columns: 1fr; }}
.ba-gallery .ba-g-main, .ba-gallery .ba-g-side {{ min-height:0; height:100%; }}
.ba-gallery .ba-g-side {{ display:grid; grid-auto-rows: 1fr; gap:10px; }}
.ba-gallery figure {{ margin:0; height:100%; border-radius:16px; overflow:hidden; background:#E9E2D5; position:relative; }}
.ba-h4 {{ font: 600 1.15rem/1.3 "Fraunces", Georgia, serif; margin: 1rem 0 .4rem; }}
.ba-gallery img {{ width:100%; height:100%; object-fit:cover; display:block; }}
.ba-gallery figcaption {{ position:absolute; bottom:6px; right:8px; font-size:.65rem; color:#fff; background: rgba(0,0,0,.45); padding:2px 6px; border-radius:6px; }}
.ba-gallery figcaption a {{ color:#fff; }}
.ba-kv {{ display:grid; grid-template-columns: 7.5rem 1fr; gap:.35rem .8rem; font-size:.92rem; }}
.ba-kv dt {{ color:{MUTED}; }}
.ba-kv dd {{ margin:0; }}
@media (max-width: 640px) {{
  .ba-gallery {{ grid-template-columns: 1fr; height:auto; }}
  .ba-gallery .ba-g-main {{ height: 240px; }}
  .ba-gallery .ba-g-side {{ grid-auto-rows: 120px; grid-auto-flow: column; }}
  .block-container {{ padding-top: 3.2rem; }}
}}
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def brand_header() -> None:
    st.markdown(
        '<div class="ba-brand"><span class="ba-dot"></span><span class="ba-wordmark">Burger Atlas</span></div>',
        unsafe_allow_html=True,
    )
