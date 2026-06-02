"""
CarryForge v3.0 — Premium PE Empire Builder
============================================
Mobile-first · Dark finance aesthetic · Deep LBO engine
Narrative events · LP personalities · Rival firms · Prestige system

Tech: Python 3.11+ · Streamlit 1.40+ · SQLite · Plotly
"""

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import random
import json
import sqlite3
import os
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CarryForge",
    page_icon=":briefcase:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM & CSS
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "bg":       "#07080c",
    "surface":  "#0d111e",
    "surface2": "#141928",
    "surface3": "#1c2236",
    "border":   "rgba(255,255,255,.06)",
    "borderl":  "rgba(255,255,255,.14)",
    "lime":     "#4ade80",
    "gold":     "#fbbf24",
    "red":      "#f87171",
    "blue":     "#60a5fa",
    "purple":   "#a78bfa",
    "pink":     "#f472b6",
    "teal":     "#2dd4bf",
    "text":     "#e2e8f0",
    "muted":    "#64748b",
}

SECTOR_COLORS = {
    "SaaS":       ("#60a5fa", "rgba(96,165,250,.10)"),
    "Hardware":   ("#a78bfa", "rgba(167,139,250,.10)"),
    "Healthcare": ("#f472b6", "rgba(244,114,182,.10)"),
    "Fintech":    ("#2dd4bf", "rgba(45,212,191,.10)"),
    "Logistics":  ("#fbbf24", "rgba(251,191,36,.10)"),
    "Media":      ("#fb923c", "rgba(251,146,60,.10)"),
    "Industrial": ("#94a3b8", "rgba(148,163,184,.10)"),
    "Consumer":   ("#f87171", "rgba(248,113,113,.10)"),
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&display=swap');

/* ── Reset & base ──────────────────────────────────────────────────────── */
*, *::before, *::after {
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
  box-sizing: border-box;
}
html, body, .stApp {
  background: #07080c !important;
  color: #e2e8f0;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
  padding: .85rem 1.1rem 5rem;
  max-width: 1000px;
  margin: 0 auto;
}
@media (min-width: 900px) {
  .block-container { padding: 1.5rem 2.5rem 2.5rem !important; max-width: 1360px !important; }
  #_cf_nav { display: none !important; }
}

/* ── Typography ────────────────────────────────────────────────────────── */
h1 { font-size:1.6rem; font-weight:800; margin:0; letter-spacing:-.025em; }
h2 { font-size:1.05rem; font-weight:700; margin:.8rem 0 .4rem; letter-spacing:-.01em; }
h3 { font-size:.9rem; font-weight:700; margin:0; }
hr { border-color: rgba(255,255,255,.06); margin: .7rem 0; }

/* ── Hide widgets we use as state buses ────────────────────────────────── */
div[data-testid="stTextInput"] { display: none !important; }

/* ── Streamlit metrics override ─────────────────────────────────────────── */
div[data-testid="stMetric"] {
  background: #0d111e;
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 16px;
  padding: .85rem 1.1rem !important;
}
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size:.62rem !important;
  font-weight:700 !important; text-transform:uppercase; letter-spacing:.08em; }
div[data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1.5rem !important;
  font-weight: 700 !important;
  color: #e2e8f0 !important;
}
div[data-testid="stMetricDelta"] > div { font-size: .78rem !important; }

/* ── Primary button ─────────────────────────────────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, #4ade80, #22c55e) !important;
  color: #052e16 !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 800 !important;
  font-size: .85rem !important;
  letter-spacing: .01em !important;
  padding: .65rem 1.4rem !important;
  width: 100%;
  transition: transform .12s, box-shadow .12s !important;
  box-shadow: 0 4px 14px rgba(74,222,128,.18) !important;
  overflow: hidden !important;
  position: relative !important;
}
.stButton > button::after {
  content: ''; position: absolute; top: 0; left: -75%;
  width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.25), transparent);
  transition: left .5s ease;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(74,222,128,.32) !important;
}
.stButton > button:hover::after { left: 140%; }
.stButton > button:disabled {
  background: #1c2236 !important;
  color: #64748b !important;
  box-shadow: none !important;
  transform: none !important;
}

/* ── Choice / secondary buttons ────────────────────────────────────────── */
.choice-btn button {
  background: #141928 !important;
  color: #e2e8f0 !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
  font-weight: 600 !important;
}
.choice-btn button:hover {
  border-color: #4ade80 !important;
  color: #4ade80 !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
div[data-testid="stTabs"] > div:first-child {
  background: #0d111e;
  border-radius: 14px;
  padding: 3px;
  border: 1px solid rgba(255,255,255,.06);
  gap: 2px;
}
div[data-testid="stTabs"] button {
  border-radius: 11px !important;
  font-weight: 600 !important;
  font-size: .82rem !important;
  color: #64748b !important;
  border: none !important;
  padding: .45rem .85rem !important;
  transition: all .15s !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
  background: #141928 !important;
  color: #4ade80 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,.35) !important;
}
div[data-testid="stTabs"] > div:last-child {
  border-top: 1px solid rgba(255,255,255,.06);
  padding-top: .75rem;
}

/* ── Cards ───────────────────────────────────────────────────────────────── */
.card {
  background: #0d111e;
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 18px;
  padding: 1rem 1.15rem;
  margin-bottom: .5rem;
  transition: border-color .2s;
}
.card:hover { border-color: rgba(255,255,255,.14); }
.card-saas     { background: linear-gradient(135deg, rgba(96,165,250,.08), #0d111e 75%); }
.card-hw       { background: linear-gradient(135deg, rgba(167,139,250,.08), #0d111e 75%); }
.card-health   { background: linear-gradient(135deg, rgba(244,114,182,.08), #0d111e 75%); }
.card-fin      { background: linear-gradient(135deg, rgba(45,212,191,.08),  #0d111e 75%); }
.card-log      { background: linear-gradient(135deg, rgba(251,191,36,.08),  #0d111e 75%); }
.card-media    { background: linear-gradient(135deg, rgba(251,146,60,.08),  #0d111e 75%); }
.card-ind      { background: linear-gradient(135deg, rgba(148,163,184,.08), #0d111e 75%); }
.card-con      { background: linear-gradient(135deg, rgba(248,113,113,.08), #0d111e 75%); }

/* ── Number display ─────────────────────────────────────────────────────── */
.num {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1.7rem; font-weight: 700;
  line-height: 1.1; letter-spacing: -.03em;
  font-feature-settings: "tnum";
}
.num-md {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1.15rem; font-weight: 700;
  font-feature-settings: "tnum";
}
.num-sm {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: .92rem; font-weight: 700;
  font-feature-settings: "tnum";
}
.lbl {
  font-size: .6rem; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: .09em;
  margin-top: .18rem;
}

/* ── Chips ───────────────────────────────────────────────────────────────── */
.chip {
  display: inline-block;
  background: #141928;
  border: 1px solid rgba(255,255,255,.07);
  border-radius: 999px;
  padding: .18rem .6rem; font-size: .68rem;
  font-weight: 600; color: #64748b; margin: 2px;
}
.chip b { color: #e2e8f0; font-weight: 700; }
.chip-hot   { border-color: #fbbf24; color: #fbbf24; background: rgba(251,191,36,.08); }
.chip-risk  { border-color: #f87171; color: #f87171; background: rgba(248,113,113,.08); }

/* ── Section headers ────────────────────────────────────────────────────── */
.sec {
  display: flex; align-items: center; gap: .6rem;
  margin: 1.1rem 0 .55rem;
}
.sec span { font-size: .7rem; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: .09em; white-space: nowrap; }
.sec hr { flex: 1; margin: 0;
  background: linear-gradient(90deg, rgba(255,255,255,.07), transparent);
  height: 1px; border: none; }

/* ── LP bar ─────────────────────────────────────────────────────────────── */
.lp-row { display: flex; align-items: center; gap: .55rem; margin: .35rem 0; }
.lp-track {
  flex: 1; height: 10px;
  background: linear-gradient(90deg,
    rgba(74,222,128,.12) 0%,
    rgba(251,191,36,.12) 50%,
    rgba(248,113,113,.12) 100%);
  border-radius: 999px; overflow: hidden;
}
.lp-fill { height: 10px; border-radius: 999px; transition: width .5s ease; }

/* ── Path pills ─────────────────────────────────────────────────────────── */
.pp { display: inline-flex; align-items: center; gap: .3rem;
  border-radius: 999px; padding: .28rem .7rem;
  font-size: .7rem; font-weight: 700; border: 1px solid; margin: 2px; }
.pp-hit    { background: rgba(74,222,128,.12); border-color: #4ade80; color: #4ade80; }
.pp-ahead  { background: rgba(74,222,128,.07); border-color: rgba(74,222,128,.35); color: #86efac; }
.pp-behind { background: rgba(248,113,113,.07); border-color: rgba(248,113,113,.3); color: #fca5a5; }
.pp-miss   { background: #141928; border-color: rgba(255,255,255,.07); color: #64748b; }

/* ── Event cards ────────────────────────────────────────────────────────── */
.ev { border-radius: 20px; padding: 1.2rem 1.35rem; margin: .45rem 0; border: 1px solid; }
.ev-crisis      { background: rgba(248,113,113,.07); border-color: rgba(248,113,113,.28); }
.ev-opportunity { background: rgba(74,222,128,.07);  border-color: rgba(74,222,128,.28); }
.ev-rival       { background: rgba(167,139,250,.07); border-color: rgba(167,139,250,.28); }
.ev-lp          { background: rgba(251,191,36,.07);  border-color: rgba(251,191,36,.28); }
.ev-season      { background: rgba(96,165,250,.07);  border-color: rgba(96,165,250,.28); }

/* ── Score/unlock cards ─────────────────────────────────────────────────── */
.score-card {
  background: linear-gradient(135deg, #141928, #0d111e);
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 24px;
  padding: 2rem 1.75rem;
  text-align: center;
  max-width: 520px;
  margin: .75rem auto;
}
.unlock-card {
  background: linear-gradient(135deg, rgba(251,191,36,.07), #0d111e);
  border: 1px solid rgba(251,191,36,.22);
  border-radius: 18px;
  padding: 1.1rem; margin: .5rem 0; text-align: center;
}

/* ── Hint / log ─────────────────────────────────────────────────────────── */
.hint {
  background: rgba(96,165,250,.07);
  border: 1px solid rgba(96,165,250,.2);
  border-radius: 14px;
  padding: .65rem 1rem; font-size: .83rem; color: #93c5fd; margin: .5rem 0;
}
.log { padding: .38rem .8rem; background: #141928; border-radius: 10px;
  font-size: .79rem; color: #64748b; margin: .2rem 0; }

/* ── Color helpers ──────────────────────────────────────────────────────── */
.g { color: #4ade80 !important; font-weight: 700; }
.go { color: #fbbf24 !important; font-weight: 700; }
.r { color: #f87171 !important; font-weight: 700; }
.mu { color: #64748b !important; }
.b7 { font-weight: 700; }

/* ── Sector dot ─────────────────────────────────────────────────────────── */
.dot { display: inline-block; width: 9px; height: 9px;
  border-radius: 50%; margin-right: 5px; vertical-align: middle; }

/* ── Season colors ──────────────────────────────────────────────────────── */
.s1c { color: #4ade80; font-weight: 700; }
.s2c { color: #fbbf24; font-weight: 700; }
.s3c { color: #f87171; font-weight: 700; }

/* ── Mobile section hide/show ────────────────────────────────────────────── */
@media (max-width: 899px) {
  .desktop-section { display: none !important; }
  .desktop-section.cf-active { display: block !important; }
}

/* ── Value Creation Levers ────────────────────────────────────────────── */
  .lever-grid { display:flex; gap:.3rem; flex-wrap:wrap; margin-top:.4rem; }
  .lever-btn {
    background:#141928; border:1px solid rgba(255,255,255,.1); border-radius:7px;
    padding:.24rem .58rem; font-size:.68rem; font-weight:700; color:#94a3b8;
    cursor:pointer; font-family:'Space Grotesk',sans-serif; transition:all .15s;
  }
  .lever-btn:hover { border-color:#4ade80; color:#4ade80; }
  .lever-btn.active { background:rgba(74,222,128,.12); border-color:#4ade80; color:#4ade80; }
  .lever-btn.cooldown { opacity:.32; cursor:not-allowed; }
  .lever-btn.expensive { opacity:.38; cursor:not-allowed; }
  .lever-outcome { font-size:.7rem; font-weight:600; margin-top:.28rem; }
  .lever-outcome.win  { color:#4ade80; }
  .lever-outcome.loss { color:#f87171; }

/* ── Mobile ─────────────────────────────────────────────────────────────── */
@media (max-width: 640px) {
  .block-container { padding: .65rem .65rem 5.5rem !important; }
  .num { font-size: 1.35rem; }
  h1 { font-size: 1.3rem; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

from game_engine import (
    MAX_PORTFOLIO, DB_PATH, SEASONS, SECTORS, SECTOR_DOT_COLOR,
    CEO_NAMES, COMPANY_NAMES, RIVAL_FIRMS, LP_CHARACTERS, FIRM_DEFAULTS,
    DIFFICULTY, UNLOCKS, NARRATIVE_EVENTS, EFFECTS, LEVERS,
    Company, GameState,
    init_db, save_game, load_game, list_saves,
    mc, cf, lpc,
    make_deal_pitch, make_deals, calc, proj3,
    blended_moic, check_paths, sell_company, apply_effect,
    pick_event, advance_quarter,
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE  (Streamlit-specific — stays here)
# ─────────────────────────────────────────────────────────────────────────────
def G() -> GameState:
    if "gs" not in st.session_state:
        st.session_state.gs = GameState()
    gs = st.session_state.gs
    for field_name, default in [("sound_queue",[]),("season_shown",0),
                                  ("forced_exit_id",""),("total_realized",0.0),
                                  ("achievements",[]),("event_log",[])]:
        if not hasattr(gs, field_name): setattr(gs, field_name, default)
    return gs

def get_tab() -> str:
    return st.session_state.get("tab", "overview")

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# UI HELPERS  (return HTML strings for st.markdown — stays here)
# ─────────────────────────────────────────────────────────────────────────────
def hdot(m):
    c = "#4ade80" if m >= 1.10 else ("#f87171" if m <= 0.85 else "#fbbf24")
    return f'<span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:{c};vertical-align:middle;margin-right:4px"></span>'

def sdot(sector):
    c = SECTOR_DOT_COLOR.get(sector, "#64748b")
    return f'<span class="dot" style="background:{c}"></span>'

def sector_tag(sector: str) -> str:
    abbr  = SECTORS.get(sector, {}).get("abbr", sector[:2].upper())
    color = SECTOR_DOT_COLOR.get(sector, "#64748b")
    return (f'<span style="display:inline-block;background:{color}18;color:{color};'
            f'border:1px solid {color}44;border-radius:4px;padding:1px 6px;'
            f'font-size:.62rem;font-weight:800;letter-spacing:.06em">{abbr}</span>')

def type_badge(ev_type: str) -> str:
    styles = {"crisis":"#f87171","opportunity":"#4ade80","rival":"#a78bfa","lp":"#fbbf24","season":"#60a5fa"}
    labels = {"crisis":"CRISIS","opportunity":"OPP","rival":"RIVAL","lp":"LP","season":"MARKET"}
    c = styles.get(ev_type, "#64748b")
    l = labels.get(ev_type, ev_type.upper())
    return (f'<span style="display:inline-block;background:{c}18;color:{c};'
            f'border:1px solid {c}44;border-radius:4px;padding:2px 8px;'
            f'font-size:.62rem;font-weight:800;letter-spacing:.08em">{l}</span>')

def sec_head(label: str):
    st.markdown(f'<div class="sec"><span>{label}</span><hr></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SOUND ENGINE

# ─────────────────────────────────────────────────────────────────────────────

_AUDIO_JS = r"""
window._cfPlay = function(snd) {
  try {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    var ctx = new AC();
    if (ctx.state === 'suspended') ctx.resume();
    var t = ctx.currentTime;
    function tone(f, type, t0, dur, vol, dt) {
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type = type || 'sine'; o.frequency.value = f;
      if (dt) o.detune.value = dt;
      g.gain.setValueAtTime(0, t0);
      g.gain.linearRampToValueAtTime(vol || 0.2, t0 + 0.012);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      o.start(t0); o.stop(t0 + dur + 0.05);
    }
    var s = snd;
    if (s==='BUY')        { tone(880,'sine',t,.18,.22); tone(1320,'sine',t+.09,.18,.18); tone(1760,'sine',t+.17,.14,.12); }
    else if (s==='SELL_WIN')   { [523,659,784,1047].forEach((f,i)=>tone(f,'sine',t+i*.1,.26,.22)); tone(1047,'sine',t+.45,.35,.16); }
    else if (s==='SELL_OK')    { tone(660,'sine',t,.18,.22); tone(880,'sine',t+.1,.2,.18); }
    else if (s==='SELL_BAD')   { [400,330,260].forEach((f,i)=>tone(f,'triangle',t+i*.12,.22,.16)); }
    else if (s==='TICK')       { tone(700,'sine',t,.06,.1); tone(1000,'sine',t+.04,.05,.07); }
    else if (s==='CRISIS')     { tone(220,'sawtooth',t,.14,.16); tone(196,'sawtooth',t+.12,.18,.13,-10); }
    else if (s==='OPPORTUNITY'){ tone(1100,'sine',t,.1,.18); tone(1320,'sine',t+.07,.13,.14); }
    else if (s==='SEASON')     { [130,164,196,246].forEach((f,i)=>tone(f,'sine',t+i*.08,.55,.13)); }
    else if (s==='RIVAL')      { [500,400,320].forEach((f,i)=>tone(f,'sawtooth',t+i*.09,.18,.11)); }
    else if (s==='LP')         { tone(740,'square',t,.1,.09); tone(740,'square',t+.18,.1,.09); }
    else if (s==='VICTORY')    { [523,659,784,1047,784,1047,1319].forEach((f,i)=>tone(f,'sine',t+i*.09,.28,.2)); }
    else if (s==='DEFEAT')     { [350,300,250,230].forEach((f,i)=>tone(f,'sawtooth',t+i*.14,.25,.13)); }
    setTimeout(()=>{ try{ctx.close();}catch(e){} }, 2800);
  } catch(e) {}
};
"""

def flush_sounds(gs: GameState):
    snds = list(getattr(gs, "sound_queue", []))
    gs.sound_queue = []
    if not snds: return
    calls = "".join(f"window.parent._cfPlay('{s}');" for s in snds)
    import random as _r
    components.html(f"""
    <script>
    (function(){{
      if(!window.parent._cfPlay){{
        var s=window.parent.document.createElement('script');
        s.textContent={repr(_AUDIO_JS)};
        window.parent.document.head.appendChild(s);
      }}
      {calls}
    }})();
    </script>
    <div style="width:1px;height:1px;opacity:0"><!-- {_r.random()} --></div>
    """, height=1)

# ─────────────────────────────────────────────────────────────────────────────
# MOBILE BOTTOM NAV
# ─────────────────────────────────────────────────────────────────────────────

def inject_bottom_nav(active: str, badge: bool = False):
    # Clean text-only tabs — no emoji
    TABS = [("overview","Home"),("deals","Deals"),
            ("portfolio","Port."),("market","Market"),("fund","Fund")]
    import random as _r
    tabs_js = str([(k, l) for k, l in TABS])
    components.html(f"""
    <script>
    (function(){{
      var TABS={tabs_js};
      var active="{active}", badge={"true" if badge else "false"};
      if(window.parent.innerWidth>=900){{
        var old=window.parent.document.getElementById('_cf_nav');
        if(old)old.remove(); return;
      }}
      function setInput(v){{
        var inp=window.parent.document.querySelector('input[data-testid="stTextInput-Input"]')
                ||window.parent.document.querySelector('input[type="text"]');
        if(!inp)return;
        var setter=Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
        setter.call(inp,v);
        inp.dispatchEvent(new window.parent.Event('input',{{bubbles:true}}));
      }}
      function scrollTo(key){{
        var el=window.parent.document.querySelector('[data-cf-section="'+key+'"]');
        if(el)el.scrollIntoView({{behavior:'smooth',block:'start'}});
      }}
      var ex=window.parent.document.getElementById('_cf_nav');
      if(ex){{ if(ex.getAttribute('data-active')===active)return; ex.remove(); }}
      var nav=window.parent.document.createElement('div');
      nav.id='_cf_nav'; nav.setAttribute('data-active',active);
      nav.style.cssText='position:fixed;bottom:0;left:0;right:0;background:#07080c;'
        +'border-top:1px solid rgba(255,255,255,.08);display:flex;z-index:99999;'
        +'padding:8px 0 max(10px,env(safe-area-inset-bottom));'
        +'font-family:"Space Grotesk",-apple-system,sans-serif;'
        +'backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);';
      TABS.forEach(function(tab){{
        var key=tab[0],lbl=tab[1],isAct=(key===active);
        var item=window.parent.document.createElement('button');
        /* Badge dot for market events — CSS only, no emoji */
        var bdot = (key==='market'&&badge)
          ? '<span style="display:inline-block;width:5px;height:5px;border-radius:50%;'
            +'background:#f87171;vertical-align:super;margin-left:2px"></span>' : '';
        item.innerHTML='<span style="font-size:.7rem;display:block;font-weight:'
          +(isAct?'700':'500')+';">' + lbl + bdot + '</span>';
        item.style.cssText='flex:1;background:none;border:none;cursor:pointer;padding:10px 2px 6px;'
          +'color:'+(isAct?'#4ade80':'#64748b')+';outline:none;'
          +'-webkit-tap-highlight-color:transparent;transition:color .18s;'
          +'border-top:2px solid '+(isAct?'#4ade80':'transparent')+';';
        item.addEventListener('click',function(){{
          scrollTo(key); setInput(key);
        }});
        nav.appendChild(item);
      }});
      window.parent.document.body.appendChild(nav);
    }})();
    </script>
    <div style="width:1px;height:1px;opacity:0"><!-- {_r.random()} --></div>
    """, height=1)

# ─────────────────────────────────────────────────────────────────────────────
# SHARED HEADER
# ─────────────────────────────────────────────────────────────────────────────

def render_header(gs: GameState):
    si  = gs.season_info
    bm  = blended_moic(gs)
    fn  = gs.fund_number
    fl  = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    qtl = gs.total_quarters - gs.quarter_num
    sc  = si["css"]

    c1, c2, c3, c4 = st.columns([3, 1.1, 1.2, 1.5])
    with c1:
        st.markdown(
            f"<h1 style='letter-spacing:-.025em'>{gs.firm_name}"
            f"<span style='font-size:.78rem;color:#64748b;font-weight:500;margin-left:.5rem'>· {fl}</span></h1>",
            unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style="text-align:center;padding:.2rem 0">
          <div class="num-md">{cf(gs.cash)}</div>
          <div class="lbl">Dry Powder</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="text-align:center;padding:.2rem 0">
          <div class="num-md"><span class="{sc}">{si['dot']}</span> {gs.year} Q{gs.quarter}</div>
          <div class="lbl">{si['name']}</div></div>""", unsafe_allow_html=True)
    with c4:
        if st.button(f"⏭  Next Quarter  ({qtl})", key="nq"):
            advance_quarter(gs); st.rerun()

    # LP bar
    lp_c = lpc(gs.lp_satisfaction)
    lp_em = "Good" if gs.lp_satisfaction >= 70 else ("Neutral" if gs.lp_satisfaction >= 45 else "Low")
    st.markdown(f"""
    <div class="lp-row">
      <span style="font-size:.68rem;color:#64748b;white-space:nowrap">"LPs — " + lp_em</span>
      <div class="lp-track">
        <div class="lp-fill" style="width:{gs.lp_satisfaction}%;background:{lp_c};
             box-shadow:0 0 8px {lp_c}55"></div>
      </div>
      <span style="font-size:.7rem;color:{lp_c};font-weight:700">{gs.lp_satisfaction}/100</span>
    </div>""", unsafe_allow_html=True)

    if gs.lp_satisfaction < 35:   st.error("LPs threatening to pull. Exit something now.")
    elif gs.lp_satisfaction < 50: st.warning("LPs getting restless. They want returns.")

    # Path pills
    paths = check_paths(gs)
    pills = []
    for p in paths.values():
        if p["hit"]: css = "pp-hit"
        elif p["pace"] == "ahead": css = "pp-ahead"
        elif p["pace"] == "behind": css = "pp-behind"
        else: css = "pp-miss"
        icon = "✓" if p["hit"] else ("↑" if p["pace"]=="ahead" else "↓")
        pills.append(f'<span class="pp {css}">{icon} {p["label"]} {p["actual"]}/{p["target"]}</span>')
    st.markdown("<div style='margin:.3rem 0'>" + " ".join(pills) + "</div>", unsafe_allow_html=True)

    if gs.event_log:
        st.markdown(f'<div class="log">{gs.event_log[0]}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: OVERVIEW (J-Curve + Key Metrics)
# ─────────────────────────────────────────────────────────────────────────────

def tab_overview(gs: GameState):
    bm     = blended_moic(gs)
    paths  = check_paths(gs)
    n_hit  = sum(1 for p in paths.values() if p["hit"])
    realized = gs.total_realized

    # Big 4 metrics
    cols = st.columns(4)
    metrics = [
        (f"{bm:.2f}×",          "Portfolio MOIC",   mc(bm) == "g"),
        (cf(gs.cash),           "Dry Powder",        False),
        (str(len(gs.exited)),   "Exits Closed",      len(gs.exited) > 0),
        (f"{n_hit}/3",          "Win Paths Hit",     n_hit > 0),
    ]
    for col, (val, lbl, hi) in zip(cols, metrics):
        with col:
            clr = "#4ade80" if hi else "#e2e8f0"
            st.markdown(f"""<div style="background:#0d111e;border:1px solid rgba(255,255,255,.06);
                 border-radius:16px;padding:.9rem 1.1rem;text-align:center">
              <div class="num" style="color:{clr}">{val}</div>
              <div class="lbl">{lbl}</div></div>""", unsafe_allow_html=True)

    # J-Curve chart
    if gs.quarter_num > 0 or gs.companies or gs.exited:
        sec_head("FUND PERFORMANCE")
        quarters = list(range(gs.quarter_num + 1))
        # Simulate historical MOIC (we just show current + trend)
        moic_history = []
        for q in range(gs.quarter_num + 1):
            if q == 0: moic_history.append(1.0)
            else:
                trend = 1.0 + (bm - 1.0) * (q / max(gs.quarter_num, 1)) ** 1.2
                noise = np.random.normal(0, 0.04)
                moic_history.append(max(0.5, trend + noise))
        moic_history[-1] = bm  # last point is real

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[f"Q{q+1}" for q in quarters], y=moic_history,
            mode='lines+markers',
            line=dict(color='#4ade80', width=2.5, shape='spline'),
            marker=dict(size=6, color='#4ade80'),
            fill='tozeroy', fillcolor='rgba(74,222,128,.06)',
            hovertemplate='%{x}: %{y:.2f}×<extra></extra>',
            name='Portfolio MOIC',
        ))
        fig.add_hline(y=1.0, line_dash="dot", line_color="rgba(255,255,255,.15)")
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=200, margin=dict(l=0, r=0, t=10, b=0),
            font=dict(color='#64748b', size=11),
            xaxis=dict(showgrid=False, color='#64748b'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,.04)', color='#64748b',
                       tickformat='.1f', ticksuffix='×'),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Portfolio summary
    if gs.companies:
        sec_head("PORTFOLIO")
        for c in gs.companies:
            m   = calc(c, gs)
            dot = SECTOR_DOT_COLOR.get(c.sector, "#64748b")
            yh  = m["yh"]; age = f"{yh:.1f}y" if yh >= 1 else f"{int(round(yh*4))}q"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.6rem 1rem;background:#0d111e;border:1px solid rgba(255,255,255,.06);
                 border-radius:14px;margin-bottom:.32rem">
              <span>
                <span class="dot" style="background:{dot}"></span>
                <strong>{c.name}</strong>
                <span class="mu" style="font-size:.72rem"> · {c.sector} · {age}</span>
              </span>
              <div style="display:flex;gap:1.1rem;align-items:center">
                <span class="num-sm {mc(m['moic'])}">{m['moic']:.2f}×</span>
                <span class="mu" style="font-size:.78rem">{m['irr']*100:.0f}% IRR</span>
              </div>
            </div>""", unsafe_allow_html=True)

    if not gs.companies and gs.quarter_num == 0:
        st.markdown("""<div class="hint" style="margin-top:.75rem">
          <strong>Welcome to CarryForge.</strong> Head to <strong>Deals</strong>
          to source your first investment. Hit <strong>Next Quarter</strong> to grow it.
          Sell when the return looks good. Build your empire.</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: DEAL FLOW
# ─────────────────────────────────────────────────────────────────────────────

def tab_deals(gs: GameState):
    full = len(gs.companies) >= MAX_PORTFOLIO
    sec_head(f"DEAL FLOW {'· Portfolio Full — sell first to buy' if full else ''}")
    buy_idx = None

    for i, d in enumerate(gs.deals):
        sec  = SECTORS[d.sector]
        p3   = proj3(d, gs)
        can  = d.entry_equity <= gs.cash and not full
        lev  = d.entry_debt / max(d.ebitda, 1)
        dot  = SECTOR_DOT_COLOR[d.sector]
        tier_chip = (f'<span class="chip chip-hot">HOT</span>' if d.tier == "hot"
                     else f'<span class="chip chip-risk">RISK</span>' if d.tier == "risky" else "")

        ca, cb, cc = st.columns([3.2, 1.9, 1])
        with ca:
            st.markdown(f"""<div class="card {sec['css']}">
              <div style="display:flex;align-items:center;gap:.45rem;margin-bottom:.35rem">
                <span class="dot" style="background:{dot};width:10px;height:10px"></span>
                <h3>{d.name}</h3> {tier_chip}
              </div>
              <div style="font-size:.75rem;color:#64748b;margin-bottom:.4rem;font-style:italic">
                "{d.pitch}"</div>
              <div style="font-size:.73rem;color:#64748b;margin-bottom:.4rem">CEO: {d.ceo}</div>
              <span class="chip">{d.sector}</span>
              <span class="chip">Entry <b>{d.entry_multiple:.1f}×</b></span>
              <span class="chip">Growth <b>{d.growth*100:.0f}%</b></span>
              <span class="chip">Margin <b>{d.margin*100:.0f}%</b></span>
              <span class="chip">Lev <b>{lev:.1f}×</b></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div style="display:flex;gap:.6rem;align-items:center;height:100%;padding:.4rem 0">
              <div style="text-align:center">
                <div class="num-md">{cf(d.entry_equity)}</div>
                <div class="lbl">Equity</div>
              </div>
              <div style="width:1px;height:32px;background:rgba(255,255,255,.07)"></div>
              <div style="text-align:center">
                <div class="num-md {mc(p3)}">{p3:.1f}×</div>
                <div class="lbl">Est 3yr</div>
              </div>
            </div>""", unsafe_allow_html=True)
        with cc:
            lbl = "Buy" if can else ("Full" if full else "--")
            if st.button(lbl, key=f"buy_{i}_{gs.quarter_num}", disabled=not can):
                buy_idx = i

    if buy_idx is not None:
        d = gs.deals[buy_idx]
        gs.cash -= d.entry_equity
        d.entry_quarter = gs.quarter_num
        gs.companies.append(d)
        gs.deals.pop(buy_idx)
        gs.event_log.insert(0, f"Closed {d.name}. {d.ceo} is 'excited about the partnership.'")
        gs.event_log = gs.event_log[:8]
        gs.sound_queue.append("BUY")
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB: PORTFOLIO
# ─────────────────────────────────────────────────────────────────────────────

def tab_portfolio(gs: GameState):
    sec_head(f"PORTFOLIO ({len(gs.companies)}/{MAX_PORTFOLIO})")
    if not gs.companies:
        st.markdown('<div class="hint">No holdings yet — source deals to invest.</div>', unsafe_allow_html=True)
        return

    sell_idx = None
    for i, c in enumerate(gs.companies):
        m    = calc(c, gs)
        sec  = SECTORS[c.sector]
        dot  = SECTOR_DOT_COLOR[c.sector]
        yh   = m["yh"]; age = f"{yh:.1f}y" if yh >= 1 else f"{int(round(yh*4))}q"
        status = (' <span style="color:#f87171;font-size:.7rem">damaged</span>' if c.moic_modifier < 0.85
                  else (' <span style="color:#4ade80;font-size:.7rem">boosted</span>' if c.moic_modifier > 1.15 else ""))
        cov_warn = " !" if m["leverage"] > 3.5 or m["interest_cov"] < 1.5 else ""

        ca, cb, cc = st.columns([3.2, 1.9, 1])
        with ca:
            st.markdown(f"""<div class="card {sec['css']}">
              <div style="display:flex;align-items:center;gap:.45rem;margin-bottom:.3rem">
                <span class="dot" style="background:{dot};width:10px;height:10px"></span>
                <span class="b7">{c.name}</span>
                <span class="mu" style="font-size:.72rem">{c.sector} · {c.ceo} · {age}{cov_warn}</span>
                {status}
              </div>
              <span class="chip">{cf(m['revenue'])} rev</span>
              <span class="chip">Lev <b>{m['leverage']:.1f}×</b></span>
              <span class="chip">ICR <b>{m['interest_cov']:.1f}×</b></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div style="display:flex;gap:.6rem;align-items:center;height:100%;padding:.4rem 0">
              <div style="text-align:center">
                <div class="num-md {mc(m['moic'])}">{m['moic']:.2f}×</div>
                <div class="lbl">MOIC</div>
              </div>
              <div style="width:1px;height:32px;background:rgba(255,255,255,.07)"></div>
              <div style="text-align:center">
                <div class="num-md">{m['irr']*100:.0f}%</div>
                <div class="lbl">IRR</div>
              </div>
            </div>""", unsafe_allow_html=True)
        with cc:
            good_exit = m['moic'] >= 1.4
            btn_lbl = "Sell" + (" ←" if good_exit else "")
            if st.button(btn_lbl, key=f"sell_{i}_{gs.quarter_num}", type="primary" if good_exit else "secondary"):
                sell_idx = i

        # ── Value Creation Levers ────────────────────────────────────────
        lever_html = '<div class="lever-grid">'
        active = c.pending_lever
        for lid, lev in LEVERS.items():
            on_cd = (c.lever_cooldowns.get(lid, -99) > gs.quarter_num - lev["cooldown"])
            too_expensive = lev["cost"] > 0 and lev["cost"] > gs.cash
            css_cls = ("active" if lid == active
                       else "cooldown" if on_cd
                       else "expensive" if too_expensive
                       else "")
            cost_str = f" +{cf(lev['cost'])}" if lev["cost"] > 0 else ""
            sr = int(lev['success_rate']*100)
            title = f"title=\"{lev['desc']}  |  {sr}% success  |  +{lev['win_moic']*100:.0f}% win / {lev['loss_moic']*100:.0f}% loss\""
            lever_html += f'<button class="lever-btn {css_cls}" {title}>{lev["short"]}{cost_str}</button>'
        lever_html += '</div>'
        # Last lever outcome
        if c.lever_history:
            last = c.lever_history[-1]
            ok = last["outcome"] == "WIN"
            cls = "lever-outcome-win" if ok else "lever-outcome-loss"
            lever_html += f'<div class="{cls}" style="margin-top:.3rem;font-size:.7rem">Last: {last["lever"]} — {last["msg"][:60]}</div>'
        st.markdown(lever_html, unsafe_allow_html=True)

        # Lever click detection via radio (hidden label = lever id)
        lever_pick = st.radio("", ["—"] + list(LEVERS.keys()),
                              key=f"lev_{c.id}_{gs.quarter_num}",
                              horizontal=True, label_visibility="collapsed",
                              index=0 if not active else list(LEVERS.keys()).index(active)+1)
        if lever_pick != "—" and lever_pick != active:
            lev = LEVERS[lever_pick]
            on_cd = (c.lever_cooldowns.get(lever_pick,-99) > gs.quarter_num - lev["cooldown"])
            if not on_cd and (lev["cost"] == 0 or lev["cost"] <= gs.cash):
                if lev["cost"] > 0: gs.cash -= lev["cost"]
                c.pending_lever = lever_pick
                gs.event_log.insert(0, f"{c.name}: {lev['label']} queued for next quarter.")
                gs.event_log = gs.event_log[:8]
                st.rerun()
        elif lever_pick == "—" and active:
            # Cancel a pending lever (refund cash cost)
            lev = LEVERS[active]
            if lev["cost"] > 0: gs.cash += lev["cost"]
            c.pending_lever = ""
            st.rerun()

    if sell_idx is not None:
        m     = calc(gs.companies[sell_idx], gs)
        cname = gs.companies[sell_idx].name
        sell_company(gs, sell_idx)
        gs.sound_queue.append("SELL_WIN" if m["moic"] >= 2.0 else ("SELL_OK" if m["moic"] >= 1.3 else "SELL_BAD"))
        em = "[WIN]" if m["moic"] >= 2.0 else "[OK]" if m["moic"] >= 1.4 else "[LOSS]"
        st.success(f"{em} Sold **{cname}** — {m['moic']:.2f}× · {cf(m['equity'])}")
        st.rerun()

    if gs.exited:
        sec_head("EXITS")
        for e in reversed(gs.exited):
            dot = SECTOR_DOT_COLOR.get(e["sector"], "#64748b")
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.55rem 1rem;background:#0d111e;border:1px solid rgba(255,255,255,.06);
                 border-radius:14px;margin-bottom:.3rem">
              <span><span class="dot" style="background:{dot}"></span><strong>{e['name']}</strong>
                <span class="mu" style="font-size:.72rem"> · {e['yh']:.1f}yr</span></span>
              <span class="num-sm {mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="mu" style="font-size:.78rem">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: MARKET & GLOBE
# ─────────────────────────────────────────────────────────────────────────────

def tab_market(gs: GameState):
    si = gs.season_info

    sec_head("MARKET CONDITIONS")
    c1, c2, c3 = st.columns(3)
    c1.metric("Season", f"{si['dot']} {si['name']}", si.get("text","")[:40])
    c2.metric("Exit Mult Modifier", f"{gs.exit_mult_mod:.2f}×",
              f"{(gs.exit_mult_mod-1)*100:+.0f}%")
    c3.metric("Growth Modifier", f"{gs.growth_mod:.2f}×",
              f"{(gs.growth_mod-1)*100:+.0f}%")

    # Market sentiment mini-chart
    quarters = list(range(1, gs.quarter_num + 2))
    mult_trend = [8.5 * SEASONS[1 if q <= 4 else (2 if q <= 8 else 3)]["exit_mod"]
                  for q in quarters]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[f"Q{q}" for q in quarters], y=mult_trend,
        mode='lines', line=dict(color='#fbbf24', width=2),
        hovertemplate='%{x}: %{y:.1f}×<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text="Exit Multiple Trend", font=dict(color='#64748b', size=11)),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=160, margin=dict(l=0, r=0, t=30, b=0),
        font=dict(color='#64748b', size=11),
        xaxis=dict(showgrid=False, color='#64748b'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,.04)', color='#64748b',
                   tickformat='.1f', ticksuffix='×'),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Portfolio globe (simplified scatter map)
    if gs.companies or gs.exited:
        sec_head("PORTFOLIO COMPANIES — GLOBAL VIEW")

        # Assign pseudo-random locations to companies
        locations = {
            "SaaS":       [(37.8, -122.4, "San Francisco"), (40.7, -74.0, "New York"), (51.5, -0.1, "London")],
            "Hardware":   [(47.6, -122.3, "Seattle"), (52.5, 13.4, "Berlin"), (35.7, 139.7, "Tokyo")],
            "Healthcare": [(42.4, -71.1, "Boston"), (48.9, 2.3, "Paris"), (19.1, 72.9, "Mumbai")],
            "Fintech":    [(51.5, -0.1, "London"), (1.3, 103.8, "Singapore"), (40.7, -74.0, "New York")],
            "Logistics":  [(41.9, 12.5, "Rome"), (39.9, 116.4, "Beijing"), (33.7, -84.4, "Atlanta")],
            "Media":      [(34.1, -118.2, "Los Angeles"), (52.4, -1.9, "Birmingham"), (55.8, 37.6, "Moscow")],
            "Industrial": [(52.2, 21.0, "Warsaw"), (43.8, -79.4, "Toronto"), (50.1, 8.7, "Frankfurt")],
            "Consumer":   [(40.4, -3.7, "Madrid"), (31.2, 121.5, "Shanghai"), (28.6, 77.2, "Delhi")],
        }

        lats, lons, texts, colors, sizes = [], [], [], [], []
        for c in gs.companies:
            m = calc(c, gs)
            locs = locations.get(c.sector, [(40.7, -74.0, "New York")])
            lat, lon, city = random.choice(locs)
            lat += random.uniform(-3, 3); lon += random.uniform(-3, 3)
            lats.append(lat); lons.append(lon)
            moic_c = "#4ade80" if m["moic"] >= 1.5 else ("#fbbf24" if m["moic"] >= 1.1 else "#f87171")
            texts.append(f"{c.name}<br>{city}<br>{m['moic']:.2f}× MOIC")
            colors.append(moic_c); sizes.append(12 + m["moic"] * 6)

        for e in gs.exited:
            locs = locations.get(e["sector"], [(40.7, -74.0, "New York")])
            lat, lon, city = random.choice(locs)
            lat += random.uniform(-3, 3); lon += random.uniform(-3, 3)
            lats.append(lat); lons.append(lon)
            texts.append(f"{e['name']} (Exited)<br>{city}<br>{e['moic']:.2f}× MOIC")
            colors.append("#64748b"); sizes.append(8)

        fig_map = go.Figure(go.Scattergeo(
            lat=lats, lon=lons, text=texts,
            mode='markers',
            marker=dict(size=sizes, color=colors, opacity=0.9,
                        symbol='circle',
                        line=dict(color='rgba(0,0,0,.3)', width=1)),
            hoverinfo='text',
        ))
        fig_map.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True, coastlinecolor='rgba(255,255,255,.08)',
                showland=True,      landcolor='#141928',
                showocean=True,     oceancolor='#0d111e',
                showlakes=False,
                projection_type='natural earth',
                # bgcolor / showgrid are not valid geo keys in Plotly 6.x
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            height=280, margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

    # Event history
    if gs.event_log:
        sec_head("RECENT INTEL")
        for msg in gs.event_log[:5]:
            st.markdown(f'<div class="log">• {msg}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: FUND & LPs
# ─────────────────────────────────────────────────────────────────────────────

def tab_fund(gs: GameState):
    cfg    = DIFFICULTY[gs.difficulty]
    paths  = check_paths(gs)
    fn     = gs.fund_number
    fl     = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    unlock = UNLOCKS[sum(1 for p in paths.values() if p["hit"])]
    raised = cfg["cash"] * gs.fund_cash_mult
    next_cash = raised * unlock["mult"]
    realized  = gs.total_realized

    sec_head(f"{fl} · {gs.firm_name}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Capital Raised", cf(raised))
    c2.metric("Deployed",       cf(raised - gs.cash))
    c3.metric("Realized",       cf(realized))

    # Win paths progress
    sec_head("WIN PATHS")
    for p in paths.values():
        pct   = min(p["actual"] / max(p["target"], 1), 1.0)
        bar_w = int(pct * 100)
        col   = "#4ade80" if p["hit"] else ("#fbbf24" if pct > 0.55 else "#374151")
        tick  = "✓ " if p["hit"] else ""
        st.markdown(f"""
        <div style="margin:.4rem 0">
          <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:.28rem">
            <span>{tick}<strong>{p['label']}</strong></span>
            <span style="color:{col};font-weight:700">{p['actual']} / {p['target']}</span>
          </div>
          <div style="background:#1c2236;border-radius:999px;height:6px;overflow:hidden">
            <div style="width:{bar_w}%;height:6px;background:{col};border-radius:999px;
                 box-shadow:0 0 6px {col}77;transition:width .4s"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Unlock card
    st.markdown(f"""<div class="unlock-card" style="margin-top:.9rem">
      <div style="font-size:.65rem;color:#fbbf24;font-weight:700;text-transform:uppercase;
           letter-spacing:.1em;margin-bottom:.35rem">On Track For</div>
      <div style="font-size:1.1rem;font-weight:800;color:#fbbf24">{unlock['fund']} — {cf(next_cash)}</div>
      <div style="font-size:.82rem;color:#64748b;margin:.35rem 0 0">{unlock['msg']}</div>
    </div>""", unsafe_allow_html=True)

    # LP characters
    sec_head("LIMITED PARTNERS")
    for lp in LP_CHARACTERS:
        ok    = gs.lp_satisfaction >= 60
        col   = "#4ade80" if ok else "#fbbf24"
        msg   = random.choice(lp["happy_msg"] if ok else lp["angry_msg"])
        lp_col = lp.get("color","#64748b")
        st.markdown(f"""
        <div class="card" style="margin-bottom:.4rem">
          <div style="display:flex;align-items:flex-start;gap:.75rem">
            <div style="flex-shrink:0;width:38px;height:38px;border-radius:10px;
              background:{lp_col}18;border:1px solid {lp_col}44;
              display:flex;align-items:center;justify-content:center;
              font-size:.78rem;font-weight:800;color:{lp_col};letter-spacing:.02em">
              {lp['initials']}</div>
            <div style="flex:1">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <span class="b7">{lp['name']}</span>
                  <span class="mu" style="font-size:.72rem"> · {lp['type']}</span>
                </div>
                <span style="color:{col};font-size:.78rem;font-weight:700">
                  {'Satisfied' if ok else 'Restless'}</span>
              </div>
              <div style="font-size:.78rem;color:#64748b;margin:.2rem 0">
                <em>"{msg}"</em>
              </div>
              <div style="font-size:.72rem;color:#374151">{lp['trait']}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Rival intel
    if gs.rival:
        sec_head("RIVAL FIRM")
        rc = gs.rival.get("color","#a78bfa")
        ri = gs.rival.get("initials","?")
        st.markdown(f"""
        <div class="ev ev-rival" style="display:flex;align-items:flex-start;gap:.75rem">
          <div style="flex-shrink:0;width:38px;height:38px;border-radius:10px;
            background:{rc}18;border:1px solid {rc}44;
            display:flex;align-items:center;justify-content:center;
            font-size:.78rem;font-weight:800;color:{rc}">{ri}</div>
          <div>
            <strong>{gs.rival.get('name','')}</strong>
            <span class="mu" style="font-size:.78rem"> — {gs.rival.get('style','').capitalize()}</span>
            <div style="font-size:.82rem;color:{rc};margin-top:.35rem;font-style:italic">
              "{gs.rival.get('motto','')}"</div>
          </div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# EVENT SCREEN
# ─────────────────────────────────────────────────────────────────────────────

def screen_event(gs: GameState):
    ev  = gs.pending_event
    css = {"crisis":"ev-crisis","opportunity":"ev-opportunity",
           "rival":"ev-rival","lp":"ev-lp","season":"ev-season"}.get(ev.get("type",""),"ev-season")

    badge_html = type_badge(ev.get("type",""))
    st.markdown(f"""
    <div class="ev {css}">
      <div style="margin-bottom:.6rem">{badge_html}</div>
      <h2 style="margin:0 0 .55rem;font-size:1.15rem">{ev.get('title','')}</h2>
      <p style="font-size:.9rem;color:#e2e8f0;line-height:1.65">{ev.get('text','')}</p>
    </div>""", unsafe_allow_html=True)

    choices = ev.get("choices", [])
    if ev.get("type") != "season":
        st.markdown("<p style='font-size:.75rem;color:#64748b;margin:.55rem 0 .3rem;"
                    "font-weight:700;text-transform:uppercase;letter-spacing:.07em'>What do you do?</p>",
                    unsafe_allow_html=True)

    cols = st.columns(max(len(choices), 1))
    for i, ch in enumerate(choices):
        with cols[i]:
            st.markdown('<div class="choice-btn">', unsafe_allow_html=True)
            if st.button(ch["label"], key=f"ch_{i}_{gs.quarter_num}"):
                apply_effect(gs, ch.get("effect", "nothing"), ev.get("cid"))
                if gs.forced_exit_id:
                    idx = next((j for j, c in enumerate(gs.companies) if c.id == gs.forced_exit_id), None)
                    if idx is not None: sell_company(gs, idx)
                    gs.forced_exit_id = ""
                gs.pending_event = {}
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: START
# ─────────────────────────────────────────────────────────────────────────────

def screen_start():
    st.markdown("""
    <div style="text-align:center;padding:2.75rem 0 1.75rem">
      <div style="font-size:3.5rem;margin-bottom:.75rem;
           filter:drop-shadow(0 0 28px rgba(74,222,128,.45))"></div>
      <h1 style="font-size:3.2rem;font-weight:800;letter-spacing:-.045em;
          background:linear-gradient(135deg,#4ade80 0%,#a78bfa 50%,#fbbf24 100%);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        CarryForge
      </h1>
      <p style="color:#64748b;font-size:.95rem;margin:.55rem 0 0;font-weight:500">
        Launch your fund · Build your portfolio · Become a legend
      </p>
    </div>""", unsafe_allow_html=True)

    # Load saves
    saves = list_saves()
    if saves:
        sec_head("CONTINUE")
        cols = st.columns(min(len(saves), 3))
        for i, (slot, label, ts) in enumerate(saves[:3]):
            with cols[i]:
                date_str = ts[:10] if ts else ""
                if st.button(f"Load: {label} ({date_str})", key=f"load_{slot}"):
                    gs = load_game(slot)
                    if gs:
                        st.session_state.gs = gs
                        st.session_state.tab = "overview"
                        st.rerun()

    sec_head("NEW GAME")
    with st.form("setup"):
        c1, c2 = st.columns(2)
        with c1: firm    = st.text_input("Firm name",  placeholder=random.choice(FIRM_DEFAULTS))
        with c2: partner = st.text_input("Your name",  placeholder="e.g. Alex Chen")
        diff = st.radio("Difficulty", ["Casual","Balanced","Hardcore"], horizontal=True, index=1,
                        captions=["Forgiving · $70M","Recommended · $50M","Full risk · $35M"])
        p = DIFFICULTY[diff]["paths"]
        st.markdown(f"""
        <div style="background:#0d111e;border:1px solid rgba(255,255,255,.1);border-radius:16px;
             padding:1rem 1.2rem;margin:.7rem 0">
          <div style="font-size:.65rem;color:#64748b;margin-bottom:.5rem;font-weight:700;
               text-transform:uppercase;letter-spacing:.1em">Three ways to win — hit any one</div>
          <div style="display:flex;gap:1.2rem;flex-wrap:wrap;font-size:.86rem;font-weight:600">
            <span style="color:#4ade80">{p['moic']}× MOIC</span>
            <span style="color:#2dd4bf">LPs ≥{p['lp']}</span>
            <span style="color:#fbbf24">{p['exits']} exits</span>
          </div>
        </div>""", unsafe_allow_html=True)
        if st.form_submit_button("Launch Fund I  →"):
            ph  = random.choice(FIRM_DEFAULTS); cfg = DIFFICULTY[diff]
            gs  = GameState(screen="game", difficulty=diff, cash=cfg["cash"],
                lp_satisfaction=cfg["lp_start"],
                firm_name=firm.strip() or ph,
                partner_name=partner.strip() or "Alex",
                rival=random.choice(RIVAL_FIRMS))
            gs.deals = make_deals(gs, 5)
            st.session_state.gs  = gs
            st.session_state.tab = "overview"
            st.session_state["score_sound"] = False
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: GAME (main loop)
# ─────────────────────────────────────────────────────────────────────────────

def screen_game():
    gs = G()

    # Tab bus (hidden input — JS nav writes here)
    raw = st.text_input("_tab", value=get_tab(), key="tab_input", label_visibility="collapsed")
    if raw != get_tab():
        st.session_state["tab"] = raw; st.rerun()
    active_tab = get_tab()

    flush_sounds(gs)
    render_header(gs)

    if gs.pending_event:
        screen_event(gs)
        inject_bottom_nav(active_tab, badge=bool(gs.pending_event))
        return

    # Desktop: Streamlit native tabs
    st.markdown("<hr>", unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["Overview", "Deals", "Portfolio", "Market", "Fund"])
    with t1: tab_overview(gs)
    with t2: tab_deals(gs)
    with t3: tab_portfolio(gs)
    with t4: tab_market(gs)
    with t5: tab_fund(gs)

    # Auto-save every quarter
    if gs.quarter_num > 0 and gs.quarter_num % 4 == 0:
        save_game(99, gs, "auto")

    inject_bottom_nav(active_tab)

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: SCORE
# ─────────────────────────────────────────────────────────────────────────────

def screen_score():
    gs    = G()
    if not st.session_state.get("score_sound"):
        st.session_state["score_sound"] = True
        n = sum(1 for p in check_paths(gs).values() if p["hit"])
        gs.sound_queue.append("VICTORY" if n >= 1 else "DEFEAT")
    flush_sounds(gs)

    paths  = check_paths(gs)
    n_hit  = sum(1 for p in paths.values() if p["hit"])
    unlock = UNLOCKS[n_hit]
    fn     = gs.fund_number
    bm     = blended_moic(gs)
    realized = gs.total_realized
    grade, gc = {3:("S","#fbbf24"),2:("A","#4ade80"),1:("B","#60a5fa"),0:("C","#f87171")}[n_hit]
    lp_quotes = {
        range(70,101): "LPs asking about Fund II before you've even closed this one.",
        range(45,70):  "LPs satisfied. One asked if you're 'considering expanding the strategy.'",
        range(25,45):  "LPs polite but distant. Hartley CC'd their attorney on the last email.",
        range(0,25):   "Westfield wants a meeting. On a Saturday.",
    }
    lp_quote = next((v for r,v in lp_quotes.items() if gs.lp_satisfaction in r), "")
    fl = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    next_cash = DIFFICULTY[gs.difficulty]["cash"] * unlock["mult"] * gs.fund_cash_mult

    st.markdown(f"""
    <div class="score-card">
      <div style="font-size:.7rem;color:#64748b;margin-bottom:.25rem;font-weight:700;
           text-transform:uppercase;letter-spacing:.09em">{gs.firm_name} · {fl}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:5.5rem;font-weight:900;
           color:{gc};line-height:1;text-shadow:0 0 50px {gc}55">{grade}</div>
      <div style="font-size:1.15rem;font-weight:700;margin:.4rem 0 .2rem">{n_hit}/3 paths hit</div>
      <p style="font-size:.88rem;color:#64748b;margin-bottom:1.5rem;max-width:380px;
         margin-left:auto;margin-right:auto">{lp_quote}</p>
      <div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:.5rem">
        <div><div class="num" style="color:{gc}">{bm:.2f}×</div><div class="lbl">MOIC</div></div>
        <div><div class="num">{len(gs.exited)}</div><div class="lbl">Exits</div></div>
        <div><div class="num">{cf(realized)}</div><div class="lbl">Realized</div></div>
        <div><div class="num" style="color:{lpc(gs.lp_satisfaction)}">{gs.lp_satisfaction}</div>
          <div class="lbl">LP Score</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # CTA buttons
    _, c2, c3 = st.columns([1,1,1])
    with c2:
        nl = f"Start {unlock['fund']} →" if fn < 3 else "New Fund"
        if st.button(nl, key="fund_next"):
            st.session_state["score_sound"] = False
            if fn < 3:
                ng = GameState(
                    screen="game", difficulty=gs.difficulty, cash=next_cash,
                    lp_satisfaction=min(100, DIFFICULTY[gs.difficulty]["lp_start"] + unlock["lp_bonus"]),
                    firm_name=gs.firm_name, partner_name=gs.partner_name,
                    fund_number=fn + 1,
                    fund_cash_mult=unlock["mult"] * gs.fund_cash_mult,
                    fund_lp_bonus=gs.fund_lp_bonus + unlock["lp_bonus"],
                    rival=gs.rival,
                )
                ng.deals = make_deals(ng, 5)
                st.session_state.gs = ng
            else:
                del st.session_state["gs"]
            st.session_state.tab = "overview"
            st.rerun()
    with c3:
        if st.button("New Game", key="new_game"):
            st.session_state["score_sound"] = False
            del st.session_state["gs"]; st.rerun()

    # Path breakdown
    st.markdown("<h2 style='text-align:center;margin-top:1.1rem;font-size:.88rem;"
                "color:#64748b;text-transform:uppercase;letter-spacing:.09em'>Win Paths</h2>",
                unsafe_allow_html=True)
    for p in paths.values():
        css = ("background:rgba(74,222,128,.09);border:1px solid rgba(74,222,128,.3)"
               if p["hit"] else "background:#141928;border:1px solid rgba(255,255,255,.07);opacity:.55")
        col = "#4ade80" if p["hit"] else "#64748b"
        st.markdown(f"""<div style="{css};border-radius:12px;padding:.55rem .95rem;margin:.25rem 0">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-weight:700">{'✓ ' if p['hit'] else ''}{p['label']}</span>
            <span style="color:{col};font-weight:700;font-family:'JetBrains Mono',monospace">
              {p['actual']} {'✓' if p['hit'] else f'/ {p["target"]}'}</span>
          </div></div>""", unsafe_allow_html=True)

    # Unlock
    st.markdown(f"""<div class="unlock-card" style="margin-top:.9rem">
      <div style="font-size:.65rem;color:#fbbf24;font-weight:700;text-transform:uppercase;
           letter-spacing:.1em;margin-bottom:.4rem">('Unlocked' if fn<3 else 'Endgame')</div>
      <div style="font-size:1.15rem;font-weight:800;color:#fbbf24">{unlock['fund']} · {cf(next_cash)}</div>
      <div style="font-size:.82rem;color:#64748b;margin:.4rem 0 0">{unlock['msg']}</div>
    </div>""", unsafe_allow_html=True)

    # Deal recap
    if gs.exited:
        st.markdown("<h2 style='text-align:center;margin-top:1.1rem;font-size:.88rem;"
                    "color:#64748b;text-transform:uppercase;letter-spacing:.09em'>Deal Recap</h2>",
                    unsafe_allow_html=True)
        for e in sorted(gs.exited, key=lambda x: -x["moic"]):
            dot = SECTOR_DOT_COLOR.get(e["sector"], "#64748b")
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.55rem 1rem;background:#0d111e;border:1px solid rgba(255,255,255,.06);
                 border-radius:14px;margin-bottom:.3rem">
              <span><span class="dot" style="background:{dot}"></span><strong>{e['name']}</strong></span>
              <span class="num-sm {mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="mu" style="font-size:.78rem">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

    save_game(98, gs, "last_score")

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def main():
    gs = G()
    if   gs.screen == "start": screen_start()
    elif gs.screen == "game":  screen_game()
    elif gs.screen == "score": screen_score()

if __name__ == "__main__":
    main()
