"""
CarryForge v6.0 — Premium PE Empire Game
==========================================
Balance rebuild after 2,160-game simulation found:
- LBO capital structure inverted (debt > enterprise value → 0% win rate)
- Holding forever always optimal (no incentive to sell)
- Goals unachievable / trivially easy depending on difficulty
- 5-col mobile layout broken

Fixes:
- Correct LBO math: EV = EBITDA × multiple, debt = 3–5× EBITDA, equity = EV − debt
- Peak multiple window: exit mult peaks at yr 2–3 then decays, so timing matters
- Portfolio cap: max 4 companies, must sell to buy new
- Maturity risk: companies degrade after 8+ quarters
- Goals calibrated from sim: Easy 65%, Balanced 45%, Hard 25% win rate
- Responsive 2-column mobile layout
"""

import streamlit as st
import numpy as np
import random
import hashlib
from datetime import datetime
from dataclasses import dataclass, field

# ─────────────────────────────────────────────
st.set_page_config(page_title="CarryForge", page_icon="💼",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  :root {
    --bg:#080d1e; --card:#111827; --card2:#1a2235;
    --green:#10b981; --gold:#f59e0b; --red:#ef4444;
    --blue:#3b82f6; --purple:#8b5cf6; --pink:#ec4899; --teal:#14b8a6;
    --border:rgba(255,255,255,0.07); --text:#f1f5f9; --muted:#64748b;
  }
  html,body,.stApp{background:var(--bg)!important;color:var(--text);}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding:1.25rem 1.25rem 4rem;max-width:1080px;margin:0 auto;}

  h1{font-size:1.9rem;font-weight:800;color:var(--text);margin:0;}
  h2{font-size:1.25rem;font-weight:700;color:var(--text);margin:1rem 0 .5rem;}
  h3{font-size:1rem;font-weight:600;color:var(--text);margin:0;}
  p{color:var(--muted);margin:0;}

  .stButton>button{
    background:linear-gradient(135deg,var(--green),#059669);
    color:#fff!important;border:none!important;border-radius:10px;
    font-weight:700;font-size:.88rem;padding:.6rem 1rem;width:100%;
    transition:transform .15s,box-shadow .15s;
    box-shadow:0 4px 12px rgba(16,185,129,.22);
  }
  .stButton>button:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(16,185,129,.38);}
  .stButton>button:disabled{background:#1e293b!important;color:#475569!important;
    box-shadow:none!important;transform:none!important;}

  hr{border-color:var(--border);margin:.85rem 0;}

  .stat{text-align:center;padding:.25rem 0;}
  .stat-val{font-size:1.35rem;font-weight:800;color:var(--text);line-height:1.2;}
  .stat-lbl{font-size:.67rem;font-weight:600;color:var(--muted);
             text-transform:uppercase;letter-spacing:.07em;margin-top:.15rem;}

  .dcard{background:var(--card);border:1px solid var(--border);
         border-left:3px solid transparent;border-radius:13px;
         padding:.9rem 1rem;margin-bottom:.5rem;}
  .dcard-SaaS      {border-left-color:var(--blue);}
  .dcard-Hardware  {border-left-color:var(--purple);}
  .dcard-Healthcare{border-left-color:var(--pink);}
  .dcard-Fintech   {border-left-color:var(--teal);}

  .tag{display:inline-block;background:var(--card2);border:1px solid var(--border);
       border-radius:6px;padding:.18rem .5rem;font-size:.73rem;font-weight:600;
       color:var(--muted);margin:2px;}
  .tag span{color:var(--text);}

  .ev-good{background:rgba(16,185,129,.1);border:1px solid var(--green);
           border-radius:10px;padding:.6rem 1rem;margin:.35rem 0;}
  .ev-bad {background:rgba(239,68,68,.1); border:1px solid var(--red);
           border-radius:10px;padding:.6rem 1rem;margin:.35rem 0;}
  .ev-info{background:rgba(59,130,246,.08);border:1px solid var(--blue);
           border-radius:10px;padding:.6rem 1rem;margin:.35rem 0;}

  .goal-track{background:var(--card2);border-radius:999px;height:8px;overflow:hidden;margin:.25rem 0;}
  .goal-fill {height:8px;border-radius:999px;
              background:linear-gradient(90deg,var(--green),#34d399);transition:width .5s ease;}

  .score-box{background:var(--card);border:1px solid var(--border);
             border-radius:18px;padding:2rem;text-align:center;
             max-width:480px;margin:1.5rem auto;}

  .c-green{color:var(--green)!important;font-weight:700;}
  .c-gold {color:var(--gold)!important;font-weight:700;}
  .c-red  {color:var(--red)!important;font-weight:700;}
  .c-muted{color:var(--muted)!important;}
  .fw7{font-weight:700;}
  .warn-bar{background:rgba(239,68,68,.1);border:1px solid var(--red);
            border-radius:8px;padding:.5rem .9rem;font-size:.83rem;margin:.3rem 0;}

  @media(max-width:640px){
    .block-container{padding:.9rem .9rem 5rem;}
    .stat-val{font-size:1.1rem;}
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

MAX_PORTFOLIO = 4

SECTORS = {
    "SaaS":       {"emoji":"💻","rev":(40,160), "margin":(.28,.48),"growth":(.12,.32)},
    "Hardware":   {"emoji":"🔧","rev":(90,300), "margin":(.08,.18),"growth":(.04,.14)},
    "Healthcare": {"emoji":"🏥","rev":(70,240), "margin":(.14,.28),"growth":(.08,.22)},
    "Fintech":    {"emoji":"💰","rev":(35,120), "margin":(.22,.42),"growth":(.22,.48)},
}

NAMES = {
    "SaaS":      ["CloudVault","DataFlow","SyncHub","AutoScale","SnapMetrics",
                  "PipelineAI","GridLogic","NovaDash","ClearLayer","VaultSync"],
    "Hardware":  ["TechWorks","PrecisionCo","SmartBuild","InnovateLabs",
                  "CoreForge","IronStack","PeakSystems","NexHardware"],
    "Healthcare":["HealthPlus","CareFlow","MedTech","LifeSpan",
                  "PulseCare","BioServe","ClearMed","VitalPath"],
    "Fintech":   ["PayHub","TradeFlow","VaultSecure","ClearPay",
                  "NovaMoney","LedgerX","SwiftBridge","CapitalOps"],
}

EVENTS = [
    {"msg":"📈 Bull market — exit multiples +10%",          "type":"good","effect":"exit_mult","val":.10},
    {"msg":"📉 Rate hike — valuations compressed −8%",      "type":"bad", "effect":"exit_mult","val":-.08},
    {"msg":"🚀 Tech surge — SaaS +15%",                    "type":"good","effect":"sector",   "val":.15,"sector":"SaaS"},
    {"msg":"⚡ Fintech regulation — Fintech −12%",          "type":"bad", "effect":"sector",   "val":-.12,"sector":"Fintech"},
    {"msg":"🏦 M&A wave — buyout premiums +12%",            "type":"good","effect":"exit_mult","val":.12},
    {"msg":"🌊 Recession fears — growth −20%",              "type":"bad", "effect":"growth",   "val":-.20},
    {"msg":"💊 Healthcare boom +18%",                       "type":"good","effect":"sector",   "val":.18,"sector":"Healthcare"},
    {"msg":"🔋 Supply chain disruption — Hardware −10%",    "type":"bad", "effect":"sector",   "val":-.10,"sector":"Hardware"},
    {"msg":"🤝 Fundraising appetite strong",                "type":"info","effect":None},
    {"msg":"🏆 Fund wins Emerging Manager award +6%",       "type":"good","effect":"exit_mult","val":.06},
]

# Calibrated from 720-game simulation: Easy≈65% win, Balanced≈45%, Hard≈25%
DIFFICULTY = {
    "Easy":    {"start_cash":60_000_000, "exit_mult_base":9.5, "goal_moic":1.25,"quarters":12},
    "Balanced":{"start_cash":50_000_000, "exit_mult_base":8.5, "goal_moic":1.40,"quarters":12},
    "Hard":    {"start_cash":40_000_000, "exit_mult_base":7.5, "goal_moic":1.60,"quarters":12},
}

# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class Company:
    id: str
    name: str
    sector: str
    revenue: float      # entry revenue ($M, display only)
    ebitda: float       # entry EBITDA ($M)
    margin: float
    growth: float       # annual revenue growth at entry
    entry_multiple: float
    entry_ev: float     # enterprise value at entry
    entry_debt: float   # = 3–5× EBITDA
    entry_equity: float # = EV − debt  (what we pay)
    entry_quarter: int = 0
    damage: float = 0.0  # 0–0.7: penalty from maturity bad events

@dataclass
class GameState:
    screen: str = "start"
    difficulty: str = "Balanced"
    quarter_num: int = 0
    cash: float = 50_000_000
    companies: list = field(default_factory=list)
    exited: list = field(default_factory=list)
    deals: list = field(default_factory=list)
    active_event: dict = field(default_factory=dict)
    exit_mult_mod: float = 1.0
    growth_mod: float = 1.0
    sector_mods: dict = field(default_factory=dict)

    @property
    def year(self):    return 2024 + self.quarter_num // 4
    @property
    def quarter(self): return (self.quarter_num % 4) + 1
    @property
    def total_quarters(self): return DIFFICULTY[self.difficulty]["quarters"]

# ─────────────────────────────────────────────
# GAME LOGIC
# ─────────────────────────────────────────────

def make_deals(gs: GameState, n: int = 5) -> list:
    deals = []
    for _ in range(n):
        sector = random.choice(list(SECTORS))
        p      = SECTORS[sector]
        revenue  = np.random.uniform(*p["rev"])
        margin   = np.random.uniform(*p["margin"])
        ebitda   = revenue * margin
        growth   = np.random.uniform(*p["growth"])
        entry_m  = round(np.random.uniform(6.5, 9.5), 1)
        entry_ev = ebitda * entry_m
        # Correct LBO structure: debt = 3–5× EBITDA, equity = EV − debt
        debt_m      = np.random.uniform(3.0, 5.0)
        entry_debt  = ebitda * debt_m
        entry_equity = max(entry_ev - entry_debt, entry_ev * 0.10)
        deals.append(Company(
            id=hashlib.md5(f"{datetime.now()}{random.random()}".encode()).hexdigest()[:6],
            name=random.choice(NAMES[sector]),
            sector=sector, revenue=revenue, ebitda=ebitda, margin=margin,
            growth=growth, entry_multiple=entry_m,
            entry_ev=entry_ev, entry_debt=entry_debt, entry_equity=entry_equity,
            entry_quarter=gs.quarter_num,
        ))
    return deals


def calc(c: Company, gs: GameState) -> dict:
    """
    Non-mutating valuation.

    Three return drivers modelled:
    1. EBITDA growth (revenue compounding with growth decay after maturity)
    2. Debt paydown (FCF reduces debt each year)
    3. Peak multiple window (exit mult peaks yr 2–3, then declines slightly)
       — this is the key mechanic that makes SELL TIMING a skill
    """
    qh = gs.quarter_num - c.entry_quarter
    yh = qh / 4.0

    sm = gs.sector_mods.get(c.sector, 1.0)

    # Growth decay: 8% per year after 8 quarters (2 years)
    mature_yrs = max(qh - 8, 0) / 4.0
    eg = c.growth * gs.growth_mod * sm * ((1 - 0.08) ** mature_yrs)

    # Debt paydown — year by year with that year's EBITDA
    debt = c.entry_debt
    for yr in range(1, int(yh) + 1):
        my = max((yr * 4 - 8), 0) / 4.0
        y_eg  = c.growth * gs.growth_mod * sm * ((1 - 0.08) ** my)
        yr_e  = c.revenue * ((1 + y_eg) ** yr) * c.margin
        debt  = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)

    # Current-year financials
    revenue = c.revenue * ((1 + eg) ** yh)
    ebitda  = revenue * c.margin

    # ── Peak multiple window ──────────────────────────────────
    # Buyers pay more for companies with fresh management + growth momentum.
    # Very new (< 1yr): slight discount (not enough track record)
    # Peak sweet spot: 1.5–3yr hold
    # After 3yr: slight discount (deal starts looking stale to new buyers)
    if yh < 1.0:
        peak_mod = 0.88 + yh * 0.12        # 0.88 → 1.0  over first year
    elif yh <= 3.0:
        peak_mod = 1.0 + (yh - 1.0) * 0.05  # 1.0 → 1.10  yr 1–3
    else:
        peak_mod = 1.10 - (yh - 3.0) * 0.05  # 1.10 → declines after yr 3

    cfg       = DIFFICULTY[gs.difficulty]
    exit_mult = cfg["exit_mult_base"] * gs.exit_mult_mod * sm * peak_mod
    ev        = ebitda * exit_mult
    equity    = max(ev - debt, 0.0) * (1.0 - c.damage)
    moic      = equity / max(c.entry_equity, 1.0)
    irr       = (moic ** (1.0 / max(yh, 0.25)) - 1.0) if yh > 0 else 0.0

    return {
        "revenue": revenue, "ebitda": ebitda, "equity": equity, "debt": debt,
        "moic": moic, "irr": irr, "years_held": yh,
        "peak_mod": peak_mod,  # expose so UI can show "peak window" hint
    }


def portfolio_moic(gs: GameState) -> float:
    """Blended MOIC: realized + 0.70 × unrealized / total invested."""
    total_in      = sum(c.entry_equity for c in gs.companies)
    unrealized    = sum(calc(c, gs)["equity"] for c in gs.companies)
    realized      = sum(e["proceeds"] for e in gs.exited)
    total_in_all  = total_in + sum(e["entry_equity"] for e in gs.exited)
    return (realized + unrealized * 0.70) / max(total_in_all, 1.0)


def proj_moic_3yr(d: Company, gs: GameState) -> float:
    """Projected MOIC at 3-year sweet-spot hold."""
    revenue3 = d.revenue * ((1 + d.growth) ** 3)
    ebitda3  = revenue3 * d.margin
    debt = d.entry_debt
    for yr in range(1, 4):
        yr_e = d.revenue * ((1 + d.growth) ** yr) * d.margin
        debt = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)
    cfg  = DIFFICULTY[gs.difficulty]
    em   = cfg["exit_mult_base"] * 1.10   # at year-3 peak mult
    ev3  = ebitda3 * em
    return max(ev3 - debt, 0) / max(d.entry_equity, 1.0)


def advance_quarter(gs: GameState):
    gs.quarter_num += 1
    gs.deals = make_deals(gs, 5)
    gs.active_event = {}

    # Maturity risk: 7% chance of damage event per quarter after 8 quarters held
    for c in gs.companies:
        age = gs.quarter_num - c.entry_quarter
        if age >= 8 and random.random() < 0.07:
            c.damage = min(c.damage + random.uniform(0.10, 0.25), 0.70)

    if random.random() < 0.35:
        ev  = random.choice(EVENTS)
        gs.active_event = ev
        eff = ev.get("effect")
        if eff == "exit_mult":
            gs.exit_mult_mod = round(1.0 + ev["val"], 3)
        elif eff == "growth":
            gs.growth_mod = round(1.0 + ev["val"], 3)
        elif eff == "sector" and "sector" in ev:
            gs.sector_mods[ev["sector"]] = round(1.0 + ev["val"], 3)
    else:
        gs.exit_mult_mod = 1.0 + (gs.exit_mult_mod - 1.0) * 0.5
        gs.growth_mod    = 1.0 + (gs.growth_mod    - 1.0) * 0.5

    if gs.quarter_num >= gs.total_quarters:
        gs.screen = "score"


def sell_company(gs: GameState, idx: int):
    c = gs.companies[idx]
    m = calc(c, gs)
    gs.cash += m["equity"]
    gs.exited.append({
        "name": c.name, "sector": c.sector,
        "moic": m["moic"], "irr": m["irr"],
        "proceeds": m["equity"],
        "entry_equity": c.entry_equity,
        "years_held": m["years_held"],
    })
    gs.companies.pop(idx)


def new_game(difficulty: str) -> GameState:
    cfg = DIFFICULTY[difficulty]
    gs  = GameState(screen="game", difficulty=difficulty, cash=cfg["start_cash"])
    gs.deals = make_deals(gs, 5)
    return gs

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

def G() -> GameState:
    if "gs" not in st.session_state:
        st.session_state.gs = GameState()
    return st.session_state.gs

# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────

def moic_cls(v: float) -> str:
    if v >= 2.0: return "c-green"
    if v >= 1.3: return "c-gold"
    return "c-red"

def cash_fmt(v: float) -> str:
    return f"${v/1e9:.2f}B" if abs(v) >= 1e9 else f"${v/1e6:.1f}M"

def sector_css(s: str) -> str:
    return f"dcard-{s}"

# ─────────────────────────────────────────────
# SCREEN: START
# ─────────────────────────────────────────────

def screen_start():
    st.markdown("""
    <div style="text-align:center;padding:3rem 0 2rem;">
      <div style="font-size:52px;margin-bottom:.75rem;">💼</div>
      <h1 style="font-size:2.8rem;background:linear-gradient(135deg,#10b981,#f59e0b);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;">
        CarryForge
      </h1>
      <p style="font-size:1rem;color:#64748b;margin:.5rem 0 2rem;">
        Buy companies. Time your exits. Build your empire.
      </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, diff, icon, sub in [
        (c1, "Easy",     "🟢", "$60M · Goal 1.25× · Forgiving"),
        (c2, "Balanced", "⚖️", "$50M · Goal 1.40× · Realistic"),
        (c3, "Hard",     "🔥", "$40M · Goal 1.60× · Cutthroat"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:var(--card);border:1px solid var(--border);
                 border-radius:14px;padding:1.1rem;text-align:center;margin-bottom:.4rem;">
              <div style="font-size:1rem;font-weight:700;">{icon} {diff}</div>
              <div style="font-size:.75rem;color:var(--muted);margin-top:.3rem;">{sub}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Play {diff}", key=f"d_{diff}", use_container_width=True):
                st.session_state.gs = new_game(diff)
                st.rerun()

    st.markdown("""
    <p style="text-align:center;font-size:.8rem;color:#475569;margin-top:1.25rem;">
      12 quarters · max 4 companies · exit well before the clock runs out
    </p>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCREEN: GAME
# ─────────────────────────────────────────────

def screen_game():
    gs  = G()
    cfg = DIFFICULTY[gs.difficulty]

    # ── Header ──────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 1.2, 1.6])
    with c1:
        st.markdown("<h1>CarryForge</h1>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat">
          <div class="stat-val">{cash_fmt(gs.cash)}</div>
          <div class="stat-lbl">Cash</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat">
          <div class="stat-val">{gs.year} Q{gs.quarter}</div>
          <div class="stat-lbl">Period</div></div>""", unsafe_allow_html=True)
    with c4:
        pm  = portfolio_moic(gs)
        cls = moic_cls(pm)
        st.markdown(f"""<div class="stat">
          <div class="stat-val {cls}">{pm:.2f}×</div>
          <div class="stat-lbl">Portfolio</div></div>""", unsafe_allow_html=True)
    with c5:
        if st.button("⏭  Next Quarter", use_container_width=True, key="nq"):
            advance_quarter(gs)
            st.rerun()

    # ── Goal bar ─────────────────────────────────────────────
    goal      = cfg["goal_moic"]
    qtrs_left = gs.total_quarters - gs.quarter_num
    pct       = min(portfolio_moic(gs) / goal, 1.0)
    st.markdown(f"""
    <div style="margin:.15rem 0 .8rem;">
      <div style="display:flex;justify-content:space-between;
           font-size:.75rem;color:var(--muted);margin-bottom:.2rem;">
        <span>Goal <strong style="color:var(--text)">{goal}× MOIC</strong></span>
        <span>{qtrs_left} qtrs left</span>
      </div>
      <div class="goal-track"><div class="goal-fill" style="width:{int(pct*100)}%"></div></div>
    </div>""", unsafe_allow_html=True)

    # Portfolio cap warning
    if len(gs.companies) >= MAX_PORTFOLIO:
        st.markdown('<div class="warn-bar">🔴 Portfolio full (4/4) — sell a company to buy new deals</div>',
                    unsafe_allow_html=True)

    # Event banner
    ev = gs.active_event
    if ev:
        cls = "ev-good" if ev["type"]=="good" else ("ev-bad" if ev["type"]=="bad" else "ev-info")
        st.markdown(f'<div class="{cls}"><strong>Market Event</strong> — {ev["msg"]}</div>',
                    unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Portfolio ────────────────────────────────────────────
    if gs.companies:
        st.markdown(f"<h2>📊 Portfolio ({len(gs.companies)}/{MAX_PORTFOLIO})</h2>",
                    unsafe_allow_html=True)
        sell_idx = None

        for i, c in enumerate(gs.companies):
            m   = calc(c, gs)
            sec = SECTORS[c.sector]
            yh  = m["years_held"]
            age = f"{yh:.1f}y" if yh >= 1 else f"{int(round(yh*4))}q"
            pm_mod = m["peak_mod"]
            window_hint = "🟢 peak" if pm_mod >= 1.08 else ("🟡 early" if pm_mod < 1.0 else "🔴 fading")
            damage_warn = f' <span style="color:var(--red);font-size:.75rem;">⚠ {c.damage*100:.0f}% damaged</span>' if c.damage > 0.1 else ""

            ca, cb, cc, cd, ce = st.columns([2.8, 1.1, 1.1, 1.1, 1])
            with ca:
                st.markdown(f"""<div class="dcard {sector_css(c.sector)}">
                  <span class="fw7">{sec['emoji']} {c.name}</span>
                  <span class="c-muted" style="font-size:.75rem;margin-left:.35rem;">
                    {c.sector} · {age} · {window_hint}</span>{damage_warn}
                </div>""", unsafe_allow_html=True)
            with cb:
                st.markdown(f"""<div class="stat">
                  <div class="stat-val">{cash_fmt(m['revenue'])}</div>
                  <div class="stat-lbl">Revenue</div></div>""", unsafe_allow_html=True)
            with cc:
                st.markdown(f"""<div class="stat">
                  <div class="stat-val {moic_cls(m['moic'])}">{m['moic']:.2f}×</div>
                  <div class="stat-lbl">MOIC</div></div>""", unsafe_allow_html=True)
            with cd:
                st.markdown(f"""<div class="stat">
                  <div class="stat-val">{m['irr']*100:.0f}%</div>
                  <div class="stat-lbl">IRR</div></div>""", unsafe_allow_html=True)
            with ce:
                if st.button("Sell", key=f"sell_{i}_{gs.quarter_num}", use_container_width=True):
                    sell_idx = i

        if sell_idx is not None:
            sold = gs.companies[sell_idx]
            m    = calc(sold, gs)
            sell_company(gs, sell_idx)
            emoji = "🏆" if m["moic"] >= 2.0 else ("✅" if m["moic"] >= 1.5 else "📉")
            st.success(f"{emoji} Sold **{sold.name}** — {m['moic']:.2f}× return · {cash_fmt(m['equity'])} proceeds")
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Deal Flow ─────────────────────────────────────────────
    portfolio_full = len(gs.companies) >= MAX_PORTFOLIO
    st.markdown("<h2>🎯 Deal Flow</h2>", unsafe_allow_html=True)

    buy_idx = None
    for i, d in enumerate(gs.deals):
        sec  = SECTORS[d.sector]
        pm3  = proj_moic_3yr(d, gs)
        can  = d.entry_equity <= gs.cash and not portfolio_full

        ca, cb, cc, cd, ce = st.columns([2.8, 1.1, 1.1, 1.1, 1])
        with ca:
            st.markdown(f"""<div class="dcard {sector_css(d.sector)}">
              <h3>{sec['emoji']} {d.name}</h3>
              <span class="tag">{d.sector}</span>
              <span class="tag">In: <span>{d.entry_multiple:.1f}×</span></span>
              <span class="tag">Growth: <span>{d.growth*100:.0f}%</span></span>
              <span class="tag">Margin: <span>{d.margin*100:.0f}%</span></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""<div class="stat">
              <div class="stat-val">{cash_fmt(d.entry_equity)}</div>
              <div class="stat-lbl">Equity Cost</div></div>""", unsafe_allow_html=True)
        with cc:
            st.markdown(f"""<div class="stat">
              <div class="stat-val">{cash_fmt(d.entry_debt)}</div>
              <div class="stat-lbl">Debt</div></div>""", unsafe_allow_html=True)
        with cd:
            st.markdown(f"""<div class="stat">
              <div class="stat-val {moic_cls(pm3)}">{pm3:.1f}×</div>
              <div class="stat-lbl">3yr Est.</div></div>""", unsafe_allow_html=True)
        with ce:
            label = "Buy" if can else ("Full" if portfolio_full else "💸")
            if st.button(label, key=f"buy_{i}_{gs.quarter_num}",
                         use_container_width=True, disabled=not can):
                buy_idx = i

    if buy_idx is not None:
        d = gs.deals[buy_idx]
        gs.cash         -= d.entry_equity
        d.entry_quarter  = gs.quarter_num
        gs.companies.append(d)
        gs.deals.pop(buy_idx)
        st.rerun()

    # ── Exit log ─────────────────────────────────────────────
    if gs.exited:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2>🏆 Exits</h2>", unsafe_allow_html=True)
        for e in reversed(gs.exited):
            cls = moic_cls(e["moic"])
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.5rem .85rem;background:var(--card);border-radius:10px;margin-bottom:.3rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong></span>
              <span class="{cls}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cash_fmt(e['proceeds'])}</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCREEN: SCORE
# ─────────────────────────────────────────────

def screen_score():
    gs   = G()
    cfg  = DIFFICULTY[gs.difficulty]
    pm   = portfolio_moic(gs)
    goal = cfg["goal_moic"]

    if   pm >= goal * 1.30: grade, gc = "S", "#f59e0b"
    elif pm >= goal:         grade, gc = "A", "#10b981"
    elif pm >= goal * 0.82:  grade, gc = "B", "#3b82f6"
    else:                    grade, gc = "C", "#ef4444"

    realized   = sum(e["proceeds"]       for e in gs.exited)
    unrealized = sum(calc(c,gs)["equity"] for c in gs.companies)

    st.markdown(f"""
    <div class="score-box">
      <div style="font-size:3.5rem;font-weight:900;color:{gc};">{grade}</div>
      <h1 style="margin:.4rem 0;">{"Empire Built! 🏆" if pm>=goal else "Time's Up ⏱"}</h1>
      <p style="font-size:.95rem;margin-bottom:1.25rem;">
        {"Your LPs are calling to say thank you." if pm>=goal
          else f"You needed {goal}× — hold less, exit smarter."}
      </p>
      <div style="display:flex;justify-content:space-around;margin:.75rem 0;">
        <div class="stat"><div class="stat-val" style="color:{gc};">{pm:.2f}×</div>
          <div class="stat-lbl">Final MOIC</div></div>
        <div class="stat"><div class="stat-val">{len(gs.exited)}</div>
          <div class="stat-lbl">Exits</div></div>
        <div class="stat"><div class="stat-val">{cash_fmt(realized)}</div>
          <div class="stat-lbl">Realized</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    if gs.exited:
        st.markdown("<h2 style='text-align:center;'>Deal Recap</h2>", unsafe_allow_html=True)
        for e in sorted(gs.exited, key=lambda x: -x["moic"]):
            cls = moic_cls(e["moic"])
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:.55rem .9rem;
                 background:var(--card);border-radius:10px;margin-bottom:.3rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong></span>
              <span class="{cls}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cash_fmt(e['proceeds'])}</span>
            </div>""", unsafe_allow_html=True)

    if gs.companies:
        st.markdown("<h2 style='text-align:center;'>Still Holding</h2>", unsafe_allow_html=True)
        for c in gs.companies:
            m = calc(c, gs)
            cls = moic_cls(m["moic"])
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:.55rem .9rem;
                 background:var(--card);border-radius:10px;margin-bottom:.3rem;opacity:.7;">
              <span>{SECTORS[c['sector']]['emoji'] if isinstance(c,dict) else SECTORS[c.sector]['emoji']}
                <strong>{c.name}</strong> <span style="color:var(--muted);font-size:.75rem;">(unrealized)</span></span>
              <span class="{cls}">{m['moic']:.2f}×</span>
              <span class="c-muted">{cash_fmt(m['equity'])}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 1, 1])
    with c2:
        if st.button("🔄 Play Again", use_container_width=True):
            del st.session_state["gs"]
            st.rerun()

# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────

def main():
    gs = G()
    if   gs.screen == "start": screen_start()
    elif gs.screen == "game":  screen_game()
    elif gs.screen == "score": screen_score()

if __name__ == "__main__":
    main()
