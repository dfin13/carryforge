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
    page_icon="💼",
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

MAX_PORTFOLIO = 4
DB_PATH = ".claude/carryforge.db"
os.makedirs(".claude", exist_ok=True)

SEASONS = {
    1: {"name":"Bull Run","emoji":"🟢","css":"s1c","exit_mod":1.15,"growth_mod":1.10,
        "title":"The Bull Is Running",
        "text":"Rates near zero. Every growth equity fund in NYC has more capital than ideas. "
               "Sellers know it. Price accordingly."},
    2: {"name":"The Turn","emoji":"🟡","css":"s2c","exit_mod":1.00,"growth_mod":0.95,
        "title":"The Market Has Turned",
        "text":"Easy money is gone. Buyers are more selective. Your LPs have started "
               "CC'ing their advisors on emails."},
    3: {"name":"The Reckoning","emoji":"🔴","css":"s3c","exit_mod":0.85,"growth_mod":0.88,
        "title":"Batten Down the Hatches",
        "text":"Rates up 300bps. Debt markets nearly closed. Companies that haven't "
               "exited are sitting a while longer."},
}

SECTORS = {
    "SaaS":       {"emoji":"💻","css":"card-saas","rev":(40,180),"margin":(.28,.50),"growth":(.12,.38)},
    "Hardware":   {"emoji":"🔧","css":"card-hw",  "rev":(90,320),"margin":(.08,.20),"growth":(.04,.16)},
    "Healthcare": {"emoji":"🏥","css":"card-health","rev":(70,260),"margin":(.14,.30),"growth":(.08,.24)},
    "Fintech":    {"emoji":"💰","css":"card-fin",  "rev":(35,130),"margin":(.22,.45),"growth":(.22,.50)},
    "Logistics":  {"emoji":"📦","css":"card-log",  "rev":(100,400),"margin":(.06,.14),"growth":(.05,.14)},
    "Media":      {"emoji":"📱","css":"card-media","rev":(30,110),"margin":(.15,.32),"growth":(.10,.30)},
    "Industrial": {"emoji":"⚙️","css":"card-ind", "rev":(120,380),"margin":(.08,.16),"growth":(.04,.12)},
    "Consumer":   {"emoji":"🛍","css":"card-con", "rev":(60,220),"margin":(.10,.22),"growth":(.06,.18)},
}

SECTOR_DOT_COLOR = {
    "SaaS":"#60a5fa","Hardware":"#a78bfa","Healthcare":"#f472b6","Fintech":"#2dd4bf",
    "Logistics":"#fbbf24","Media":"#fb923c","Industrial":"#94a3b8","Consumer":"#f87171",
}

CEO_NAMES = [
    "Marcus Webb","Priya Sharma","Derek Lund","Sophie Chen","Raj Patel","Chloe Kim",
    "Jake Torres","Nadia Okafor","Ben Holt","Mei Lin","Aaron Voss","Tara Flynn",
    "Luis Reyes","Iris Park","Owen Grant","Valentina Cruz","Sam Adeyemi","Petra Novak",
    "Cal Morrison","Zoe Tanaka","Finn O'Brien","Leila Hassan","Derek Storm","Ana Costa",
]

COMPANY_NAMES = {
    "SaaS":      ["CloudVault","DataFlow","SyncHub","AutoScale","SnapMetrics","PipelineAI","GridLogic","NovaDash","ClearLayer","VaultSync","OmniTrack","Apexio"],
    "Hardware":  ["TechWorks","PrecisionCo","SmartBuild","CoreForge","IronStack","PeakSystems","NexHardware","OrbDrive","PulseCore","Nexigen"],
    "Healthcare":["HealthPlus","CareFlow","MedTech","PulseCare","BioServe","ClearMed","VitalPath","RxBridge","GenoPlex","NeuroScan"],
    "Fintech":   ["PayHub","TradeFlow","VaultSecure","ClearPay","LedgerX","SwiftBridge","CapitalOps","NovaMoney","CryptoEdge","FusionPay"],
    "Logistics": ["ShipNow","FreightHub","LastMile","FastTrack","CargoFlow","PivotLog","NexiRoute","GridMove"],
    "Media":     ["ContentFlow","StreamVault","MediaLab","NovaStudio","BrightCast","PulseFeed","TalentGrid","Scrollr"],
    "Industrial":["PrecisionWorks","IronPath","NexaFab","BuildCore","ForgePoint","MetalFlow","GridMech","ArcWeld"],
    "Consumer":  ["BrandFlow","ShelfPop","TrendCo","NovaBrand","GoodBasket","CartEdge","PrimeSelect","VenusCo"],
}

RIVAL_FIRMS = [
    {"name":"Apex Capital","emoji":"🦅","style":"aggressive","motto":"We don't pass. We outbid."},
    {"name":"Redwood PE","emoji":"🌲","style":"conservative","motto":"Boring is beautiful."},
    {"name":"Meridian Partners","emoji":"🐍","style":"sleazy","motto":"Relationships. Always."},
    {"name":"Pinnacle Fund","emoji":"🏔","style":"arrogant","motto":"Second place is first loser."},
]

LP_CHARACTERS = [
    {"name":"Dr. Eleanor Voss","type":"Westfield Endowment","emoji":"🎓","personality":"conservative",
     "trait":"Demands quarterly ESG updates. Loves 10-year IRR charts.",
     "happy_msg":["Impressed with your discipline.", "The board was pleased this quarter.", "Exactly what we expected from you."],
     "angry_msg":["We're concerned about the leverage.", "Expected better DPI by now.", "My investment committee is asking questions."]},
    {"name":"Mike Carbone","type":"CalPERS West","emoji":"🏛","personality":"aggressive",
     "trait":"Wants top-quartile returns. 'Don't bore me with process.'",
     "happy_msg":["Now we're talking. Keep pushing.", "That's what I like to see.", "The committee is smiling. Good work."],
     "angry_msg":["These returns are embarrassing.", "My buddy at Apex is killing it.", "Give me a reason not to pull out."]},
    {"name":"Hartley & Hartley","type":"Family Office","emoji":"👔","personality":"relationship",
     "trait":"Three generations of investing. Values honesty and quarterly calls.",
     "happy_msg":["Pleasure doing business, as always.", "The family is happy. That matters.", "Worth every dollar of carry."],
     "angry_msg":["Father wouldn't have tolerated this.", "We expected a call, not a deck.", "Trust is everything."]},
    {"name":"Atlas Foundation","type":"Nonprofit Endowment","emoji":"🌍","personality":"esg",
     "trait":"ESG-focused. Refuses to back extractive industries or high-polluters.",
     "happy_msg":["This aligns with our mission beautifully.", "Great returns. Great impact.", "The board gave a standing ovation."],
     "angry_msg":["This company's carbon footprint is unacceptable.", "Returns don't justify the harm.", "We need to discuss compliance."]},
]

FIRM_DEFAULTS = ["Genesis Capital","Ironwood Partners","Crestview Equity","Summit PE","Clarendon Fund","Northstar PE"]

DIFFICULTY = {
    "Casual":   {"cash":70e6,"exit_mult":10.0,"quarters":12,"lp_start":82,"paths":{"moic":1.4,"lp":65,"exits":2}},
    "Balanced": {"cash":50e6,"exit_mult":8.5, "quarters":12,"lp_start":65,"paths":{"moic":1.75,"lp":65,"exits":4}},
    "Hardcore": {"cash":35e6,"exit_mult":7.0, "quarters":12,"lp_start":50,"paths":{"moic":2.2,"lp":58,"exits":5}},
}

UNLOCKS = {
    0: {"fund":"Fund II","mult":1.0,"lp_bonus":0,"msg":"LPs give you one more shot."},
    1: {"fund":"Fund II","mult":1.3,"lp_bonus":8,"msg":"Modest step up. LPs are cautiously optimistic."},
    2: {"fund":"Fund II","mult":1.65,"lp_bonus":15,"msg":"Strong showing. Real upgrade incoming."},
    3: {"fund":"Fund II","mult":2.1,"lp_bonus":25,"msg":"All three. LPs are fighting over allocation. Fund III is next."},
}

# ─────────────────────────────────────────────────────────────────────────────
# NARRATIVE EVENTS (30+ entries)
# ─────────────────────────────────────────────────────────────────────────────

NARRATIVE_EVENTS = [
    {"id":"ceo_poached","type":"crisis","title":"Your CEO Got Poached","icon":"😬",
     "template":"**{ceo}** — CEO of {co} — just got a $2.8M offer from {rival}. "
                "They called from the school parking lot.",
     "choices":[
        {"label":"Counter with 2% equity stake (+$300K)","effect":"ceo_stays"},
        {"label":"Match salary only","effect":"ceo_slows"},
        {"label":"Wish them luck. Start a search.","effect":"ceo_gone"},
     ]},
    {"id":"ceo_arrested","type":"crisis","title":"Legal Situation","icon":"🚔",
     "template":"CEO of {co}, **{ceo}**, was arrested. 'Unrelated to business.' SEC says otherwise.",
     "choices":[
        {"label":"Terminate immediately. PR blackout.","effect":"ceo_fired_clean"},
        {"label":"Hire crisis lawyer, ride it out","effect":"crisis_lawyer"},
        {"label":"Back them publicly","effect":"disaster"},
     ]},
    {"id":"big_contract","type":"opportunity","title":"Enterprise Contract","icon":"🤝",
     "template":"{co} got an LOI from a Fortune 50 — $14M ARR adding ~32% to revenue overnight.",
     "choices":[
        {"label":"Staff up fast — hire 45 people","effect":"big_growth"},
        {"label":"Sign it, figure out delivery later","effect":"medium_growth"},
        {"label":"Pass — too much execution risk","effect":"nothing"},
     ]},
    {"id":"customer_churn","type":"crisis","title":"Client Just Walked","icon":"💨",
     "template":"{co}'s largest customer — 19% of ARR — terminated. Their CFO: 'a nice experiment.'",
     "choices":[
        {"label":"Fly out, offer discount to stay","effect":"partial_save"},
        {"label":"Accept it and focus on pipeline","effect":"slight_miss"},
        {"label":"Sue for breach","effect":"litigation"},
     ]},
    {"id":"rival_bid","type":"rival","title":"Competing Bid","icon":"😤",
     "template":"**{rival}** just bid $9M over your offer for {co}. 'Using leverage we'd never touch.'",
     "choices":[
        {"label":"Walk away — discipline first","effect":"deal_lost"},
        {"label":"Match, tighten terms elsewhere","effect":"deal_expensive"},
        {"label":"Go lower, pitch operational value","effect":"deal_clever"},
     ]},
    {"id":"rival_email","type":"rival","title":"Interesting Email","icon":"📧",
     "template":"Email from **{rival}**: *'Heard you picked up {co}. Brave given the cap table. "
                "Let us know when you're ready to recap at a fair price.'*",
     "choices":[
        {"label":"Reply with a screenshot of your DPI","effect":"rival_rivalry"},
        {"label":"Ignore it","effect":"nothing"},
        {"label":"Forward to LP for a laugh","effect":"lp_amused"},
     ]},
    {"id":"lp_call","type":"lp","title":"LP on Line 1","icon":"📞",
     "template":"**{lp}** calling. DPI still 0x. 'Have you considered your exit timeline?' "
                "Call in 15 minutes.",
     "choices":[
        {"label":"Take it — promise Q3 exit","effect":"pressure_exit"},
        {"label":"Send deck — 'pipeline is strong'","effect":"bought_time"},
        {"label":"Have associate take it","effect":"lp_annoyed"},
     ]},
    {"id":"lp_pullout","type":"lp","title":"LP Threatening Withdrawal","icon":"🚨",
     "template":"**{lp}** needs liquidity. Threatening to sell their stake at 30% discount.",
     "choices":[
        {"label":"Dividend recap on one company","effect":"recap_lp"},
        {"label":"Help find secondary buyer","effect":"lp_secondary"},
        {"label":"Call the bluff","effect":"lp_furious"},
     ]},
    {"id":"unsolicited_bid","type":"opportunity","title":"Someone Wants to Buy","icon":"💸",
     "template":"Strategic buyer: unsolicited offer for {co} at 38% premium. Answer by Friday.",
     "choices":[
        {"label":"Sell — take the money","effect":"force_exit"},
        {"label":"Run a full process","effect":"auction_process"},
        {"label":"Decline — just getting started","effect":"nothing"},
     ]},
    {"id":"add_on_deal","type":"opportunity","title":"Bolt-On Opportunity","icon":"🧩",
     "template":"{co} found a smaller competitor for $9M. Adds 18% revenue and a great customer list.",
     "choices":[
        {"label":"Fund it","effect":"addon_success"},
        {"label":"Pass — keep management focused","effect":"nothing"},
        {"label":"Negotiate 20% lower first","effect":"addon_negotiate"},
     ]},
    {"id":"rate_shock","type":"crisis","title":"Fed Rate Shock","icon":"📉",
     "template":"Fed raised 75bps. Debt cost up $2.3M annually. "
                "Blackstone sent 'Navigating the New Normal.' You deleted it.",
     "choices":[
        {"label":"Refinance early on strongest company","effect":"rate_hedge"},
        {"label":"Accelerate exits","effect":"pressure_exit"},
        {"label":"Weather it","effect":"slight_miss"},
     ]},
    {"id":"sector_hot","type":"opportunity","title":"Your Sector Is Hot","icon":"🔥",
     "template":"{co}'s sector on Fortune cover. Exit multiples doubled from a year ago.",
     "choices":[
        {"label":"Exit now at peak multiples","effect":"force_exit"},
        {"label":"Hold — ride the wave","effect":"risky_hold"},
        {"label":"Hire tier-1 CEO to prep for sale","effect":"ceo_upgrade"},
     ]},
    {"id":"mgmt_fight","type":"crisis","title":"Board Meeting Gone Wrong","icon":"🥊",
     "template":"**{ceo}** and your operating partner aren't speaking after last board meeting. "
                "CFO: 'That was not great.'",
     "choices":[
        {"label":"Back the CEO","effect":"mgmt_stable"},
        {"label":"Side with the OP — shake up management","effect":"ceo_gone"},
        {"label":"Bring in a mediator","effect":"slow_resolution"},
     ]},
    {"id":"ipo_buzz","type":"opportunity","title":"Bankers Calling","icon":"🏦",
     "template":"Goldman and Morgan both pitching IPO for {co}. Analyst: 'Exactly what the market wants.'",
     "choices":[
        {"label":"Set up a bake-off","effect":"ipo_process"},
        {"label":"Too early — wait another year","effect":"nothing"},
        {"label":"Take lunch but say no","effect":"nothing"},
     ]},
    {"id":"key_departure","type":"crisis","title":"Key Person Risk","icon":"👤",
     "template":"{co}'s CTO — author of 60% of the codebase — just handed in their notice.",
     "choices":[
        {"label":"Aggressive retention package","effect":"key_retained"},
        {"label":"Restructure team, promote from within","effect":"mgmt_stable"},
        {"label":"External search immediately","effect":"slight_miss"},
     ]},
    {"id":"partnership","type":"opportunity","title":"Strategic Partnership","icon":"🤝",
     "template":"{co} offered an exclusive distribution deal with a 500-store retail chain.",
     "choices":[
        {"label":"Sign the exclusive","effect":"big_growth"},
        {"label":"Negotiate non-exclusive terms","effect":"medium_growth"},
        {"label":"Pass — don't like the counterparty","effect":"nothing"},
     ]},
]

# Effect definitions
EFFECTS = {
    "ceo_stays":       {"moic_d":+.22,"msg":"CEO stayed. Equity updated. They seem pleased."},
    "ceo_slows":       {"moic_d":-.08,"msg":"They took it. You have 90 days."},
    "ceo_gone":        {"moic_d":-.28,"msg":"CEO out. Search firm on retainer."},
    "ceo_fired_clean": {"moic_d":-.18,"msg":"Terminated. Legal risk contained. Business wobbling."},
    "crisis_lawyer":   {"moic_d":-.09,"msg":"Charges reduced. Optics still your problem."},
    "disaster":        {"moic_d":-.42,"msg":"SEC subpoenas arrived Friday afternoon."},
    "big_growth":      {"moic_d":+.32,"msg":"Bold bet paid. Revenue +30%. CEO insufferable."},
    "medium_growth":   {"moic_d":+.15,"msg":"Bumpy delivery. Contract held. Client renewed."},
    "nothing":         {"moic_d":.00,"msg":"Status quo. Deck identical to last quarter."},
    "partial_save":    {"moic_d":-.07,"msg":"12-month extension. Still going to leave."},
    "slight_miss":     {"moic_d":-.11,"msg":"Revenue down 16%. Pipeline 'robust.'"},
    "litigation":      {"moic_d":-.28,"msg":"Litigation expensive. Distraction worse."},
    "deal_lost":       {"moic_d":.00,"msg":"Deal lost. You walk out saying 'discipline.'"},
    "deal_expensive":  {"moic_d":-.04,"msg":"Won it. Paid over market. Model needs a hero exit."},
    "deal_clever":     {"moic_d":+.09,"msg":"Seller picked you over higher bid. Reputation matters."},
    "rival_rivalry":   {"moic_d":.00,"lp_d":+3,"msg":"They didn't reply. Probably furious."},
    "lp_amused":       {"moic_d":.00,"lp_d":+6,"msg":"LP laughed. 'These guys.' Good relationship."},
    "pressure_exit":   {"force_exit":True,"msg":"You committed to an exit. Now deliver."},
    "bought_time":     {"lp_d":-3,"msg":"Accepted the deck. Called again 3 weeks later."},
    "lp_annoyed":      {"lp_d":-11,"msg":"Associate took it. LP is 65 and has been in PE forever."},
    "recap_lp":        {"moic_d":-.04,"lp_d":+11,"msg":"LP placated. Small leverage hit."},
    "lp_secondary":    {"lp_d":-18,"msg":"LP sold at 32% discount. New holder emails weekly."},
    "lp_furious":      {"lp_d":-26,"msg":"Called the bluff. You're calling every LP this Friday."},
    "force_exit":      {"force_exit":True,"msg":"Company going to market. Time to find your IRR."},
    "auction_process": {"moic_d":+.14,"msg":"Four bidders. Extracted another 20% on price."},
    "addon_success":   {"moic_d":+.16,"msg":"Tuck-in closed. Customer cross-sell working."},
    "addon_negotiate": {"moic_d":+.06,"msg":"Came back 20% lower. Counter-signed same afternoon."},
    "rate_hedge":      {"moic_d":+.05,"msg":"Locked 6.2% for 5 years. Feels smart already."},
    "risky_hold":      {"moic_d":+.12,"msg":"Wave didn't materialize. Multiple contracted 12%."},
    "ceo_upgrade":     {"moic_d":+.16,"msg":"Hired ex-Stripe COO. Restructured sales week one."},
    "mgmt_stable":     {"moic_d":+.05,"msg":"OP annoyed but professional. Board quieter."},
    "slow_resolution": {"moic_d":-.04,"msg":"Mediation took 6 weeks. Everyone technically aligned."},
    "ipo_process":     {"moic_d":+.09,"msg":"12-month process begins. Analyst calls next quarter."},
    "key_retained":    {"moic_d":+.08,"msg":"Retained with RSUs. Code commit rate up 40%."},
    "ceo_gone_fired":  {"moic_d":-.22,"msg":"CEO out. Interim named. Search begins Monday."},
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Company:
    id: str; name: str; sector: str; ceo: str
    revenue: float; ebitda: float; margin: float; growth: float
    entry_multiple: float; entry_ev: float; entry_debt: float; entry_equity: float
    entry_quarter: int = 0; moic_modifier: float = 1.0; tier: str = "standard"
    pitch: str = ""

@dataclass
class GameState:
    screen: str = "start"
    difficulty: str = "Balanced"
    quarter_num: int = 0
    cash: float = 50e6
    firm_name: str = ""
    partner_name: str = ""
    fund_number: int = 1
    fund_cash_mult: float = 1.0
    fund_lp_bonus: int = 0
    companies: list = field(default_factory=list)
    exited: list = field(default_factory=list)
    deals: list = field(default_factory=list)
    pending_event: dict = field(default_factory=dict)
    event_log: list = field(default_factory=list)
    lp_satisfaction: int = 65
    rival: dict = field(default_factory=dict)
    exit_mult_mod: float = 1.0
    growth_mod: float = 1.0
    sector_mods: dict = field(default_factory=dict)
    forced_exit_id: str = ""
    season_shown: int = 0
    sound_queue: list = field(default_factory=list)
    total_realized: float = 0.0
    achievements: list = field(default_factory=list)

    @property
    def year(self): return 2024 + self.quarter_num // 4
    @property
    def quarter(self): return (self.quarter_num % 4) + 1
    @property
    def total_quarters(self): return DIFFICULTY[self.difficulty]["quarters"]
    @property
    def season(self):
        q = self.quarter_num + 1
        return 1 if q <= 4 else (2 if q <= 8 else 3)
    @property
    def season_info(self): return SEASONS[self.season]

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS saves (
        slot INTEGER PRIMARY KEY, data TEXT, ts TEXT, label TEXT)""")
    conn.commit(); conn.close()

def save_game(slot: int, gs: GameState, label: str = ""):
    conn = sqlite3.connect(DB_PATH)
    data = json.dumps({
        **{k: v for k, v in gs.__dict__.items() if not k.startswith("_")},
        "companies": [c.__dict__ for c in gs.companies],
        "exited": gs.exited,
        "deals": [d.__dict__ for d in gs.deals],
    }, default=str)
    conn.execute("INSERT OR REPLACE INTO saves VALUES (?,?,?,?)",
                 (slot, data, datetime.now().isoformat(), label or gs.firm_name))
    conn.commit(); conn.close()

def load_game(slot: int) -> Optional[GameState]:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT data FROM saves WHERE slot=?", (slot,)).fetchone()
    conn.close()
    if not row: return None
    d = json.loads(row[0])
    gs = GameState()
    for k, v in d.items():
        if k == "companies":
            gs.companies = [Company(**c) for c in v]
        elif k == "deals":
            gs.deals = [Company(**c) for c in v]
        elif hasattr(gs, k):
            setattr(gs, k, v)
    return gs

def list_saves():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT slot,label,ts FROM saves ORDER BY ts DESC").fetchall()
    conn.close()
    return rows

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

def G() -> GameState:
    if "gs" not in st.session_state:
        st.session_state.gs = GameState()
    gs = st.session_state.gs
    # Migrate missing fields on old sessions
    for field_name, default in [("sound_queue",[]),("season_shown",0),
                                  ("forced_exit_id",""),("total_realized",0.0),
                                  ("achievements",[]),("event_log",[])]:
        if not hasattr(gs, field_name): setattr(gs, field_name, default)
    return gs

def get_tab() -> str:
    return st.session_state.get("tab", "overview")

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def mc(v):   return "g" if v >= 2.0 else "go" if v >= 1.3 else "r"
def cf(v):   return f"${v/1e9:.2f}B" if abs(v) >= 1e9 else f"${v/1e6:.1f}M"
def lpc(s):  return "#4ade80" if s >= 60 else "#fbbf24" if s >= 35 else "#f87171"
def hdot(m): return "🟢" if m >= 1.10 else ("🔴" if m <= 0.85 else "🟡")
def sdot(sector):
    c = SECTOR_DOT_COLOR.get(sector, "#64748b")
    return f'<span class="dot" style="background:{c}"></span>'
def sec_head(label: str):
    st.markdown(f'<div class="sec"><span>{label}</span><hr></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GAME LOGIC — LBO ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def make_deal_pitch(company: Company) -> str:
    """Generate a one-line flavorful pitch for a company."""
    pitches = {
        "SaaS": [f"{company.name} automates workflows for mid-market enterprises.",
                 f"Vertical SaaS for regulated industries. NRR above 115%.",
                 f"AI-native platform replacing 3-year-old incumbents."],
        "Hardware": [f"Proprietary hardware for industrial automation.",
                     f"Defense-grade components with 5-year government contracts.",
                     f"Next-gen semiconductor equipment for EV manufacturers."],
        "Healthcare": [f"Value-based care platform in underserved markets.",
                       f"Medical device company with FDA clearance.",
                       f"Outpatient specialty care rollup across 7 states."],
        "Fintech": [f"Embedded payments for B2B marketplaces.",
                    f"Cross-border treasury management for mid-size corporates.",
                    f"Credit risk platform used by top 10 regional banks."],
        "Logistics": [f"Last-mile delivery network in Tier-2 cities.",
                      f"Cold-chain logistics for pharmaceutical distribution.",
                      f"Real-time freight visibility platform."],
        "Media": [f"Creator economy platform with 4M monthly creators.",
                  f"Niche B2B media with premium subscriptions.",
                  f"Sports-focused streaming aggregator."],
        "Industrial": [f"Precision machining for aerospace & defense.",
                       f"Specialty chemicals for battery manufacturing.",
                       f"Robotics maintenance-as-a-service."],
        "Consumer": [f"Premium pet nutrition DTC brand.",
                     f"Wellness CPG with strong retail velocity.",
                     f"Outdoor recreation brand with cult following."],
    }
    options = pitches.get(company.sector, [f"{company.name} in the {company.sector} space."])
    return random.choice(options)

def make_deals(gs: GameState, n: int = 5) -> list:
    """Procedurally generate deal flow."""
    used = {c.name for c in gs.companies}
    deals = []
    for _ in range(n):
        sector = random.choice(list(SECTORS))
        p = SECTORS[sector]
        rev   = np.random.uniform(*p["rev"])
        mg    = np.random.uniform(*p["margin"])
        eb    = rev * mg
        gr    = np.random.uniform(*p["growth"])
        em    = round(np.random.uniform(6.5, 9.8), 1)
        ev    = eb * em
        debt  = eb * np.random.uniform(3.0, 5.2)
        eq    = max(ev - debt, ev * 0.08)
        pool  = [x for x in COMPANY_NAMES.get(sector, ["Unnamed"]) if x not in used]
        if not pool: pool = COMPANY_NAMES.get(sector, ["Unnamed"])
        name  = random.choice(pool)
        used.add(name)
        sc    = gr * 0.55 + mg * 0.45
        tier  = "hot" if sc > 0.23 and em < 8.2 else ("risky" if em > 8.8 or mg < 0.09 else "standard")
        c = Company(
            id=hashlib.md5(f"{name}{datetime.now()}{random.random()}".encode()).hexdigest()[:8],
            name=name, sector=sector, ceo=random.choice(CEO_NAMES),
            revenue=rev, ebitda=eb, margin=mg, growth=gr,
            entry_multiple=em, entry_ev=ev, entry_debt=debt, entry_equity=eq,
            entry_quarter=gs.quarter_num, tier=tier,
        )
        c.pitch = make_deal_pitch(c)
        deals.append(c)
    return deals

def calc(c: Company, gs: GameState) -> dict:
    """Core LBO calculation — returns current metrics for a held company."""
    qh  = gs.quarter_num - c.entry_quarter
    yh  = qh / 4.0
    si  = gs.season_info
    sm  = gs.sector_mods.get(c.sector, 1.0)

    # Growth decays after 8 quarters (company matures)
    mature_yrs = max(qh - 8, 0) / 4.0
    eg = c.growth * gs.growth_mod * sm * si["growth_mod"] * ((1 - 0.07) ** mature_yrs)

    # Debt paydown — year by year
    debt = c.entry_debt
    for yr in range(1, int(yh) + 1):
        my    = max((yr * 4 - 8) / 4, 0)
        y_eg  = c.growth * gs.growth_mod * sm * si["growth_mod"] * ((1 - 0.07) ** my)
        yr_e  = c.revenue * ((1 + y_eg) ** yr) * c.margin
        debt  = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)

    # Current financials
    rev    = c.revenue * ((1 + eg) ** yh)
    ebitda = rev * c.margin

    # Peak exit window (sweet spot ~2–3.5 years)
    pm = 0.88 + yh * 0.12 if yh < 1.0 else (1.0 + (yh - 1.0) * 0.05 if yh <= 3.0
         else 1.10 - (yh - 3.0) * 0.04)

    cfg    = DIFFICULTY[gs.difficulty]
    em     = cfg["exit_mult"] * gs.exit_mult_mod * sm * pm * si["exit_mod"]
    equity = max(ebitda * em - debt, 0) * max(c.moic_modifier, 0.10)
    moic   = max(equity / max(c.entry_equity, 1), 0.95 if yh < 0.25 else 0)
    irr    = (moic ** (1 / max(yh, 0.25)) - 1) if yh > 0 else 0

    return {
        "revenue": rev, "ebitda": ebitda, "equity": equity, "debt": debt,
        "moic": moic, "irr": irr, "yh": yh, "pm": pm,
        "leverage": debt / max(ebitda, 1),
        "interest_cov": ebitda / max(debt * 0.065, 1),
    }

def proj3(d: Company, gs: GameState) -> float:
    """Projected MOIC at 3-year hold for deal cards."""
    r3 = d.revenue * ((1 + d.growth) ** 3)
    eb3 = r3 * d.margin
    debt = d.entry_debt
    for yr in range(1, 4):
        yr_e = d.revenue * ((1 + d.growth) ** yr) * d.margin
        debt = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)
    em = DIFFICULTY[gs.difficulty]["exit_mult"] * 1.12
    return max(eb3 * em - debt, 0) / max(d.entry_equity, 1)

def blended_moic(gs: GameState) -> float:
    """Total portfolio + realized MOIC."""
    ti = sum(c.entry_equity for c in gs.companies) + sum(e.get("eq", 0) for e in gs.exited)
    to = sum(calc(c, gs)["equity"] for c in gs.companies) * 0.72 + sum(e.get("proc", 0) for e in gs.exited)
    return to / max(ti, 1)

def check_paths(gs: GameState) -> dict:
    """Evaluate the three win paths."""
    cfg = DIFFICULTY[gs.difficulty]["paths"]
    bm  = blended_moic(gs)
    q   = max(gs.quarter_num, 1)
    tot = gs.total_quarters
    return {
        "returns": {"hit": bm >= cfg["moic"], "target": cfg["moic"], "actual": round(bm, 2),
                    "label": "💰 Returns King", "desc": f"Hit {cfg['moic']}× MOIC",
                    "pace": "ahead" if bm/cfg["moic"]/(q/tot) > 1.1 else "behind" if bm/cfg["moic"]/(q/tot) < 0.65 else "ok"},
        "lp":      {"hit": gs.lp_satisfaction >= cfg["lp"], "target": cfg["lp"], "actual": gs.lp_satisfaction,
                    "label": "🤝 LP Legend", "desc": f"Keep LPs ≥{cfg['lp']}",
                    "pace": "ahead" if gs.lp_satisfaction >= cfg["lp"] else "behind"},
        "exits":   {"hit": len(gs.exited) >= cfg["exits"], "target": cfg["exits"], "actual": len(gs.exited),
                    "label": "🏆 Deal Maker", "desc": f"{cfg['exits']}+ exits",
                    "pace": "ahead" if len(gs.exited)/max(cfg["exits"],1)/(q/tot) > 1.0 else "behind"},
    }

def sell_company(gs: GameState, idx: int) -> dict:
    c = gs.companies[idx]; m = calc(c, gs)
    gs.cash += m["equity"]
    gs.total_realized += m["equity"]
    gs.exited.append({"name": c.name, "sector": c.sector, "ceo": c.ceo,
                      "moic": m["moic"], "irr": m["irr"],
                      "proc": m["equity"], "eq": c.entry_equity, "yh": m["yh"]})
    gs.companies.pop(idx)
    gs.lp_satisfaction = min(100, gs.lp_satisfaction + 9)
    gs.event_log.insert(0, f"Exited {c.name} at {m['moic']:.2f}×. LPs satisfied.")
    gs.event_log = gs.event_log[:8]
    # Achievements
    if m["moic"] >= 3.0 and "triple" not in gs.achievements:
        gs.achievements.append("triple"); gs.event_log.insert(0, "🏆 Achievement: First 3× exit!")
    return m

def apply_effect(gs: GameState, key: str, cid: Optional[str]):
    eff = EFFECTS.get(key, EFFECTS["nothing"])
    if cid:
        for c in gs.companies:
            if c.id == cid:
                if "moic_d" in eff:
                    c.moic_modifier = max(0.10, min(c.moic_modifier + eff["moic_d"], 3.0))
                if eff.get("force_exit"):
                    gs.forced_exit_id = c.id
                break
    if "lp_d" in eff:
        gs.lp_satisfaction = max(0, min(100, gs.lp_satisfaction + eff["lp_d"]))
    gs.event_log.insert(0, eff["msg"])
    gs.event_log = gs.event_log[:8]

def pick_event(gs: GameState) -> Optional[dict]:
    if not gs.companies: return None
    pool  = [e for e in NARRATIVE_EVENTS if e["type"] in ("crisis","opportunity")] * 2
    pool += [e for e in NARRATIVE_EVENTS if e["type"] == "rival"]
    if not gs.exited and gs.quarter_num > 3:
        pool += [e for e in NARRATIVE_EVENTS if e["type"] == "lp"] * 3
    if not pool: return None
    ev   = random.choice(pool)
    co   = random.choice(gs.companies)
    lp   = random.choice(LP_CHARACTERS)
    text = ev["template"]
    text = text.replace("{co}", f"**{co.name}**").replace("{ceo}", co.ceo)
    text = text.replace("{rival}", gs.rival.get("name", "a rival"))
    text = text.replace("{lp}", lp["name"])
    return {"id": ev["id"], "type": ev["type"], "title": ev["title"], "icon": ev["icon"],
            "text": text, "choices": ev["choices"], "cid": co.id}

def advance_quarter(gs: GameState):
    prev = gs.season
    gs.quarter_num += 1
    gs.sound_queue.append("TICK")
    if not gs.exited and gs.quarter_num > 4:
        gs.lp_satisfaction = max(0, gs.lp_satisfaction - 3)
    gs.deals = make_deals(gs, 5)
    if gs.quarter_num >= gs.total_quarters:
        gs.screen = "score"; return
    new = gs.season
    if new != prev and gs.season_shown < new:
        gs.season_shown = new; si = SEASONS[new]
        gs.sound_queue.append("SEASON")
        gs.pending_event = {"id": f"season_{new}", "type": "season",
            "title": si["title"], "icon": si["emoji"], "text": si["text"],
            "choices": [{"label": "Got it. Keep moving.", "effect": "nothing"}], "cid": None}
        return
    if random.random() < 0.62:
        ev = pick_event(gs)
        if ev:
            gs.pending_event = ev
            gs.sound_queue.append({"crisis":"CRISIS","opportunity":"OPPORTUNITY",
                                    "rival":"RIVAL","lp":"LP"}.get(ev["type"],"TICK"))

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
    TABS = [("overview","🏠","Home"),("deals","🎯","Deals"),
            ("portfolio","📊","Port."),("market","🌍","Market"),("fund","💰","Fund")]
    import random as _r
    components.html(f"""
    <script>
    (function(){{
      var TABS={str([(k,i,l) for k,i,l in TABS])};
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
        var key=tab[0],icon=tab[1],lbl=tab[2],isAct=(key===active);
        var item=window.parent.document.createElement('button');
        item.innerHTML='<span style="font-size:1.2rem;display:block;line-height:1">'+icon
          +(key==='market'&&badge?'<sup style="font-size:.45rem;color:#f87171">●</sup>':'')
          +'</span><span style="font-size:.56rem;display:block;margin-top:2px;font-weight:'
          +(isAct?'700':'500')+'">'+lbl+'</span>';
        item.style.cssText='flex:1;background:none;border:none;cursor:pointer;padding:6px 2px;'
          +'color:'+(isAct?'#4ade80':'#64748b')+';outline:none;'
          +'-webkit-tap-highlight-color:transparent;transition:color .18s;';
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
          <div class="num-md"><span class="{sc}">{si['emoji']}</span> {gs.year} Q{gs.quarter}</div>
          <div class="lbl">{si['name']}</div></div>""", unsafe_allow_html=True)
    with c4:
        if st.button(f"⏭  Next Quarter  ({qtl})", key="nq"):
            advance_quarter(gs); st.rerun()

    # LP bar
    lp_c = lpc(gs.lp_satisfaction)
    lp_em = "😊" if gs.lp_satisfaction >= 70 else ("😐" if gs.lp_satisfaction >= 45 else "😡")
    st.markdown(f"""
    <div class="lp-row">
      <span style="font-size:.68rem;color:#64748b;white-space:nowrap">{lp_em} LPs</span>
      <div class="lp-track">
        <div class="lp-fill" style="width:{gs.lp_satisfaction}%;background:{lp_c};
             box-shadow:0 0 8px {lp_c}55"></div>
      </div>
      <span style="font-size:.7rem;color:{lp_c};font-weight:700">{gs.lp_satisfaction}/100</span>
    </div>""", unsafe_allow_html=True)

    if gs.lp_satisfaction < 35:   st.error("🚨 LPs threatening to pull. Exit something now.")
    elif gs.lp_satisfaction < 50: st.warning("⚠️ LPs getting restless. They want returns.")

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
          👋 <strong>Welcome to CarryForge.</strong> Head to <strong>Deals</strong>
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
        tier_chip = (f'<span class="chip chip-hot">🔥 Hot</span>' if d.tier == "hot"
                     else f'<span class="chip chip-risk">⚠ Risk</span>' if d.tier == "risky" else "")

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
            lbl = "Buy" if can else ("Full" if full else "💸")
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
        status = (' <span style="color:#f87171;font-size:.7rem">⚠ damaged</span>' if c.moic_modifier < 0.85
                  else (' <span style="color:#4ade80;font-size:.7rem">✨ boosted</span>' if c.moic_modifier > 1.15 else ""))
        cov_warn = " 🔴" if m["leverage"] > 3.5 or m["interest_cov"] < 1.5 else ""

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
            if st.button("Sell", key=f"sell_{i}_{gs.quarter_num}"):
                sell_idx = i

    if sell_idx is not None:
        m     = calc(gs.companies[sell_idx], gs)
        cname = gs.companies[sell_idx].name
        sell_company(gs, sell_idx)
        gs.sound_queue.append("SELL_WIN" if m["moic"] >= 2.0 else ("SELL_OK" if m["moic"] >= 1.3 else "SELL_BAD"))
        em = "🏆" if m["moic"] >= 2.0 else "✅" if m["moic"] >= 1.4 else "📉"
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
    c1.metric("Season", f"{si['emoji']} {si['name']}", si["desc"] if hasattr(si, "get") else "")
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
                showframe=False, showcoastlines=True, coastlinecolor='rgba(255,255,255,.08)',
                showland=True, landcolor='#141928',
                showocean=True, oceancolor='#0d111e',
                showlakes=False, bgcolor='rgba(0,0,0,0)',
                projection_type='natural earth',
                showgrid=False,
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
           letter-spacing:.1em;margin-bottom:.35rem">🔓 On Track For</div>
      <div style="font-size:1.1rem;font-weight:800;color:#fbbf24">{unlock['fund']} — {cf(next_cash)}</div>
      <div style="font-size:.82rem;color:#64748b;margin:.35rem 0 0">{unlock['msg']}</div>
    </div>""", unsafe_allow_html=True)

    # LP characters
    sec_head("LIMITED PARTNERS")
    for lp in LP_CHARACTERS:
        ok    = gs.lp_satisfaction >= 60
        col   = "#4ade80" if ok else "#fbbf24"
        msg   = random.choice(lp["happy_msg"] if ok else lp["angry_msg"])
        st.markdown(f"""
        <div class="card" style="margin-bottom:.4rem">
          <div style="display:flex;align-items:flex-start;gap:.75rem">
            <span style="font-size:2rem;line-height:1">{lp['emoji']}</span>
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
        st.markdown(f"""
        <div class="ev ev-rival">
          <span style="font-size:1.5rem">{gs.rival.get('emoji','🏢')}</span>
          <strong> {gs.rival.get('name','')}</strong>
          <span class="mu" style="font-size:.78rem"> — {gs.rival.get('style','').capitalize()} style</span>
          <div style="font-size:.82rem;color:#a78bfa;margin-top:.4rem;font-style:italic">
            "{gs.rival.get('motto','')}"</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# EVENT SCREEN
# ─────────────────────────────────────────────────────────────────────────────

def screen_event(gs: GameState):
    ev  = gs.pending_event
    css = {"crisis":"ev-crisis","opportunity":"ev-opportunity",
           "rival":"ev-rival","lp":"ev-lp","season":"ev-season"}.get(ev.get("type",""),"ev-season")

    st.markdown(f"""
    <div class="ev {css}">
      <div style="font-size:2rem;margin-bottom:.5rem">{ev.get('icon','📋')}</div>
      <h2 style="margin:0 0 .6rem;font-size:1.15rem">{ev.get('title','')}</h2>
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
           filter:drop-shadow(0 0 28px rgba(74,222,128,.45))">💼</div>
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
                if st.button(f"📂 {label}\n{date_str}", key=f"load_{slot}"):
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
            <span style="color:#4ade80">💰 {p['moic']}× MOIC</span>
            <span style="color:#2dd4bf">🤝 LPs ≥{p['lp']}</span>
            <span style="color:#fbbf24">🏆 {p['exits']} exits</span>
          </div>
        </div>""", unsafe_allow_html=True)
        if st.form_submit_button("🚀 Launch Fund I"):
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
    t1, t2, t3, t4, t5 = st.tabs(["🏠 Overview", "🎯 Deals", "📊 Portfolio", "🌍 Market", "💰 Fund"])
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
        nl = f"Start {unlock['fund']} →" if fn < 3 else "🔄 New Fund"
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
        if st.button("🔄 New Game", key="new_game"):
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
           letter-spacing:.1em;margin-bottom:.4rem">{'🔓 Unlocked' if fn<3 else '🏆 Endgame'}</div>
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
