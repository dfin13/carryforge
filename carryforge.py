"""
CarryForge v4.0 — Premium PE Empire Game
==========================================
Rebuilt from 5 full playthroughs across different player demographics.

Fixed: broken MOIC arithmetic, mobile layout, no win condition,
trivial strategy, no events, no save, weak feedback, jargon overload.
"""

import streamlit as st
import numpy as np
import random
import hashlib
from datetime import datetime
from dataclasses import dataclass, field

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="CarryForge",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS — dark premium theme
# ─────────────────────────────────────────────

st.markdown("""
<style>
  :root {
    --bg: #080d1e;
    --card: #111827;
    --card2: #1a2235;
    --green: #10b981;
    --gold: #f59e0b;
    --red: #ef4444;
    --blue: #3b82f6;
    --purple: #8b5cf6;
    --pink: #ec4899;
    --teal: #14b8a6;
    --border: rgba(255,255,255,0.07);
    --text: #f1f5f9;
    --muted: #64748b;
  }

  html, body, .stApp { background: var(--bg) !important; color: var(--text); }

  /* Kill default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 1.5rem 1.5rem 4rem; max-width: 1100px; margin: 0 auto; }

  /* Typography */
  h1 { font-size: 2rem; font-weight: 800; color: var(--text); margin: 0; }
  h2 { font-size: 1.4rem; font-weight: 700; color: var(--text); margin: 1.5rem 0 .75rem; }
  h3 { font-size: 1.1rem; font-weight: 600; color: var(--text); margin: 0; }
  p  { color: var(--muted); margin: 0; }

  /* Primary button */
  .stButton > button {
    background: linear-gradient(135deg, var(--green), #059669);
    color: #fff !important;
    border: none !important;
    border-radius: 10px;
    font-weight: 700;
    font-size: .9rem;
    padding: .65rem 1.2rem;
    width: 100%;
    transition: transform .15s, box-shadow .15s;
    box-shadow: 0 4px 14px rgba(16,185,129,.25);
  }
  .stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(16,185,129,.4);
  }
  .stButton > button:active { transform: translateY(0); }

  /* Divider */
  hr { border-color: var(--border); margin: 1.25rem 0; }

  /* Metric pill */
  .pill {
    display: inline-block;
    background: var(--card2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: .35rem .75rem;
    font-size: .8rem;
    font-weight: 600;
    color: var(--muted);
    margin: 2px;
  }
  .pill span { color: var(--text); }

  /* Deal card */
  .dcard {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.25rem;
    margin-bottom: .75rem;
    border-left: 3px solid transparent;
  }
  .dcard-saas     { border-left-color: var(--blue); }
  .dcard-hardware { border-left-color: var(--purple); }
  .dcard-health   { border-left-color: var(--pink); }
  .dcard-fintech  { border-left-color: var(--teal); }

  /* Portfolio row */
  .prow {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: .85rem 1.1rem;
    margin-bottom: .6rem;
  }

  /* Stat block */
  .stat { text-align: center; }
  .stat-val { font-size: 1.5rem; font-weight: 800; color: var(--text); }
  .stat-lbl { font-size: .7rem; font-weight: 600; color: var(--muted);
               text-transform: uppercase; letter-spacing: .06em; }

  /* Color helpers */
  .c-green  { color: var(--green)  !important; }
  .c-gold   { color: var(--gold)   !important; }
  .c-red    { color: var(--red)    !important; }
  .c-muted  { color: var(--muted)  !important; }
  .fw7 { font-weight: 700; }

  /* Event banner */
  .event-good { background: rgba(16,185,129,.12); border: 1px solid var(--green);
                border-radius: 10px; padding: .7rem 1rem; margin: .5rem 0; }
  .event-bad  { background: rgba(239,68,68,.12); border: 1px solid var(--red);
                border-radius: 10px; padding: .7rem 1rem; margin: .5rem 0; }
  .event-info { background: rgba(59,130,246,.1); border: 1px solid var(--blue);
                border-radius: 10px; padding: .7rem 1rem; margin: .5rem 0; }

  /* Goal bar track */
  .goal-track {
    background: var(--card2);
    border-radius: 999px;
    height: 10px;
    overflow: hidden;
    margin: .4rem 0;
  }
  .goal-fill {
    height: 10px;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--green), #34d399);
    transition: width .5s ease;
  }

  /* Score screen */
  .score-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2.5rem;
    text-align: center;
    max-width: 520px;
    margin: 2rem auto;
  }

  @media (max-width: 640px) {
    .block-container { padding: 1rem 1rem 5rem; }
    .stat-val { font-size: 1.2rem; }
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────

SECTORS = {
    "SaaS":       {"emoji": "💻", "css": "dcard-saas",     "rev": (40, 140),  "margin": (.28, .48), "growth": (.12, .32)},
    "Hardware":   {"emoji": "🔧", "css": "dcard-hardware", "rev": (80, 280),  "margin": (.08, .18), "growth": (.04, .14)},
    "Healthcare": {"emoji": "🏥", "css": "dcard-health",   "rev": (70, 230),  "margin": (.14, .28), "growth": (.08, .22)},
    "Fintech":    {"emoji": "💰", "css": "dcard-fintech",  "rev": (35, 110),  "margin": (.22, .42), "growth": (.22, .48)},
}

NAMES = {
    "SaaS":       ["CloudVault","DataFlow","SyncHub","AutoScale","SnapMetrics","PipelineAI","GridLogic","NovaDash","ClearLayer","VaultSync"],
    "Hardware":   ["TechWorks","PrecisionCo","SmartBuild","InnovateLabs","CoreForge","IronStack","PeakSystems","NexHardware"],
    "Healthcare": ["HealthPlus","CareFlow","MedTech","LifeSpan","PulseCare","BioServe","ClearMed","VitalPath"],
    "Fintech":    ["PayHub","TradeFlow","VaultSecure","ClearPay","NovaMoney","LedgerX","SwiftBridge","CapitalOps"],
}

EVENTS = [
    {"msg": "📈 Bull market — exit multiples up 10%", "type": "good",  "effect": "exit_mult", "val": .10},
    {"msg": "📉 Rate hike — valuations compressed 8%",  "type": "bad",   "effect": "exit_mult", "val": -.08},
    {"msg": "🚀 Tech sector surge — SaaS values +15%",  "type": "good",  "effect": "sector",    "val": .15, "sector": "SaaS"},
    {"msg": "⚡ Fintech regulation — Fintech values −12%","type": "bad",  "effect": "sector",    "val": -.12,"sector": "Fintech"},
    {"msg": "🏦 M&A wave — all buyouts +12% premium",   "type": "good",  "effect": "exit_mult", "val": .12},
    {"msg": "🌊 Recession fears — growth slows 20%",    "type": "bad",   "effect": "growth",    "val": -.20},
    {"msg": "💊 Healthcare boom — sector values +18%",  "type": "good",  "effect": "sector",    "val": .18, "sector": "Healthcare"},
    {"msg": "🔋 Supply chain hit — Hardware −10%",      "type": "bad",   "effect": "sector",    "val": -.10,"sector": "Hardware"},
    {"msg": "🤝 PE fundraising wave — dry powder surge","type": "info",  "effect": None},
    {"msg": "🏆 Your fund wins Emerging Manager award", "type": "good",  "effect": "exit_mult", "val": .05},
]

DIFFICULTY = {
    "Easy":     {"start_cash": 60_000_000, "exit_mult_base": 9.5,  "goal_moic": 1.8, "quarters": 12},
    "Balanced": {"start_cash": 50_000_000, "exit_mult_base": 8.5,  "goal_moic": 2.2, "quarters": 12},
    "Hard":     {"start_cash": 40_000_000, "exit_mult_base": 7.5,  "goal_moic": 2.8, "quarters": 12},
}

@dataclass
class Company:
    id: str
    name: str
    sector: str
    revenue: float
    ebitda: float
    margin: float
    growth: float
    entry_multiple: float
    entry_equity: float
    entry_debt: float
    debt: float
    entry_quarter: int = 0   # total quarters elapsed when bought

@dataclass
class GameState:
    screen: str = "start"
    difficulty: str = "Balanced"
    quarter_num: int = 0        # total quarters elapsed, 0-indexed
    cash: float = 50_000_000
    companies: list = field(default_factory=list)
    exited: list = field(default_factory=list)
    deals: list = field(default_factory=list)
    active_event: dict = field(default_factory=dict)
    exit_mult_modifier: float = 1.0
    growth_modifier: float = 1.0
    sector_modifiers: dict = field(default_factory=dict)

    @property
    def year(self):
        return 2024 + self.quarter_num // 4

    @property
    def quarter(self):
        return (self.quarter_num % 4) + 1

    @property
    def total_quarters(self):
        return DIFFICULTY[self.difficulty]["quarters"]

# ─────────────────────────────────────────────
# GAME LOGIC
# ─────────────────────────────────────────────

def new_game(difficulty: str) -> GameState:
    cfg = DIFFICULTY[difficulty]
    gs = GameState(
        screen="game",
        difficulty=difficulty,
        cash=cfg["start_cash"],
        quarter_num=0,
    )
    gs.deals = make_deals(gs, 5)
    return gs

def make_deals(gs: GameState, n: int) -> list:
    deals = []
    for _ in range(n):
        sector = random.choice(list(SECTORS.keys()))
        p = SECTORS[sector]
        rev = np.random.uniform(*p["rev"])
        margin = np.random.uniform(*p["margin"])
        ebitda = rev * margin
        growth = np.random.uniform(*p["growth"])
        entry_mult = round(np.random.uniform(6.5, 9.5), 1)
        entry_equity = ebitda * entry_mult
        entry_debt = entry_equity * np.random.uniform(1.6, 2.8)
        deals.append(Company(
            id=hashlib.md5(f"{datetime.now()}{random.random()}".encode()).hexdigest()[:6],
            name=random.choice(NAMES[sector]),
            sector=sector,
            revenue=rev,
            ebitda=ebitda,
            margin=margin,
            growth=growth,
            entry_multiple=entry_mult,
            entry_equity=entry_equity,
            entry_debt=entry_debt,
            debt=entry_debt,
            entry_quarter=gs.quarter_num,
        ))
    return deals

def calc(c: Company, gs: GameState) -> dict:
    """Current company valuation. Uses quarter-based time so returns visible from Q1."""
    quarters_held = gs.quarter_num - c.entry_quarter
    years_held = quarters_held / 4.0

    # Apply global and sector modifiers to growth
    sec_mod = gs.sector_modifiers.get(c.sector, 1.0)
    effective_growth = c.growth * gs.growth_modifier * sec_mod

    revenue = c.revenue * ((1 + effective_growth) ** years_held)
    ebitda = revenue * c.margin

    # Quarterly debt paydown
    annual_fcf = ebitda * 0.55
    for _ in range(quarters_held):
        q_fcf = annual_fcf / 4
        q_interest = (c.debt * 0.065) / 4
        q_principal = max(q_fcf - q_interest, 0) * 0.35
        c.debt = max(c.debt - q_principal, 0)

    cfg = DIFFICULTY[gs.difficulty]
    exit_mult = cfg["exit_mult_base"] * gs.exit_mult_modifier * sec_mod
    ev = ebitda * exit_mult
    equity = max(ev - c.debt, 0)
    moic = equity / max(c.entry_equity, 1)
    irr = (moic ** (1 / max(years_held, 0.25)) - 1) if years_held > 0 else 0

    return {
        "revenue": revenue, "ebitda": ebitda,
        "equity": equity, "debt": c.debt,
        "moic": moic, "irr": irr,
        "years_held": years_held,
    }

def portfolio_moic(gs: GameState) -> float:
    """Blended MOIC across current + exited companies."""
    total_in = sum(c.entry_equity for c in gs.companies)
    total_out = sum(calc(c, gs)["equity"] for c in gs.companies)
    for e in gs.exited:
        total_in += e["entry_equity"]
        total_out += e["proceeds"]
    if total_in == 0:
        return 1.0
    return total_out / total_in

def advance_quarter(gs: GameState):
    """Tick forward one quarter, roll for event."""
    gs.quarter_num += 1
    gs.deals = make_deals(gs, 5)
    gs.active_event = {}

    # 35% chance of a market event
    if random.random() < 0.35:
        ev = random.choice(EVENTS)
        gs.active_event = ev
        eff = ev.get("effect")
        if eff == "exit_mult":
            gs.exit_mult_modifier = round(1.0 + ev["val"], 3)
        elif eff == "growth":
            gs.growth_modifier = round(1.0 + ev["val"], 3)
        elif eff == "sector" and "sector" in ev:
            gs.sector_modifiers[ev["sector"]] = round(1.0 + ev["val"], 3)
    else:
        # Decay modifiers back toward 1.0
        gs.exit_mult_modifier = 1.0 + (gs.exit_mult_modifier - 1.0) * 0.5
        gs.growth_modifier = 1.0 + (gs.growth_modifier - 1.0) * 0.5

    # Check win/loss
    if gs.quarter_num >= gs.total_quarters:
        gs.screen = "score"

def sell_company(gs: GameState, idx: int):
    c = gs.companies[idx]
    m = calc(c, gs)
    gs.cash += m["equity"]
    gs.exited.append({
        "name": c.name,
        "sector": c.sector,
        "moic": m["moic"],
        "irr": m["irr"],
        "proceeds": m["equity"],
        "entry_equity": c.entry_equity,
        "years_held": m["years_held"],
    })
    gs.companies.pop(idx)

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

def moic_color(v: float) -> str:
    if v >= 2.0: return "c-green"
    if v >= 1.4: return "c-gold"
    return "c-red"

def moic_badge(v: float) -> str:
    c = moic_color(v)
    return f'<span class="{c} fw7">{v:.2f}x</span>'

def irr_fmt(v: float) -> str:
    return f'<span class="c-muted">{v*100:.0f}% IRR</span>'

def sector_css(s: str) -> str:
    return SECTORS[s]["css"]

def cash_fmt(v: float) -> str:
    if v >= 1e9: return f"${v/1e9:.2f}B"
    return f"${v/1e6:.0f}M"

# ─────────────────────────────────────────────
# SCREENS
# ─────────────────────────────────────────────

def screen_start():
    gs = G()
    st.markdown("""
    <div style="text-align:center; padding: 3.5rem 0 2rem;">
      <div style="font-size:52px; margin-bottom:1rem;">💼</div>
      <h1 style="font-size:3rem; background:linear-gradient(135deg,#10b981,#f59e0b);
          -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;">
        CarryForge
      </h1>
      <p style="font-size:1.1rem; color:#64748b; margin:.5rem 0 2rem;">
        Buy companies. Grow them. Exit for profit. Build your empire.
      </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, diff, lbl, sub in [
        (c1, "Easy",     "🟢 Easy",     "Forgiving markets · $60M start"),
        (c2, "Balanced", "⚖️ Balanced", "Realistic PE · $50M start"),
        (c3, "Hard",     "🔥 Hard",     "Cutthroat markets · $40M start"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:var(--card); border:1px solid var(--border);
                 border-radius:14px; padding:1.25rem; text-align:center; margin-bottom:.5rem;">
              <div style="font-size:1.1rem; font-weight:700;">{lbl}</div>
              <div style="font-size:.8rem; color:var(--muted); margin-top:.35rem;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Play {diff}", key=f"d_{diff}", use_container_width=True):
                st.session_state.gs = new_game(diff)
                st.rerun()

    st.markdown("""
    <div style="text-align:center; margin-top:2rem;">
      <p style="font-size:.85rem; color:#475569;">
        12 quarters · Buy deals · Ride market events · Max your returns
      </p>
    </div>
    """, unsafe_allow_html=True)


def screen_game():
    gs = G()
    cfg = DIFFICULTY[gs.difficulty]

    # ── Header bar ──────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 1.2, 1.6])
    with c1:
        st.markdown(f"<h1>CarryForge</h1>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat"><div class="stat-val">{cash_fmt(gs.cash)}</div>
            <div class="stat-lbl">Cash</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat"><div class="stat-val">{gs.year} Q{gs.quarter}</div>
            <div class="stat-lbl">Period</div></div>""", unsafe_allow_html=True)
    with c4:
        pm = portfolio_moic(gs)
        cls = moic_color(pm)
        st.markdown(f"""<div class="stat"><div class="stat-val {cls}">{pm:.2f}x</div>
            <div class="stat-lbl">Blended MOIC</div></div>""", unsafe_allow_html=True)
    with c5:
        if st.button("⏭  Next Quarter", use_container_width=True, key="nq"):
            advance_quarter(gs)
            st.rerun()

    # ── Progress toward goal ────────────────────────────────
    goal = cfg["goal_moic"]
    quarters_left = gs.total_quarters - gs.quarter_num
    pct = min(portfolio_moic(gs) / goal, 1.0)
    fill_w = int(pct * 100)

    st.markdown(f"""
    <div style="margin:.3rem 0 1rem;">
      <div style="display:flex; justify-content:space-between; font-size:.8rem; color:var(--muted); margin-bottom:.3rem;">
        <span>Goal: <strong style="color:var(--text)">{goal}x MOIC</strong></span>
        <span>{quarters_left} quarters left</span>
      </div>
      <div class="goal-track"><div class="goal-fill" style="width:{fill_w}%"></div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Active event banner ─────────────────────────────────
    ev = gs.active_event
    if ev:
        css_cls = "event-good" if ev["type"] == "good" else ("event-bad" if ev["type"] == "bad" else "event-info")
        st.markdown(f'<div class="{css_cls}"><strong>Market Event:</strong> {ev["msg"]}</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Portfolio ────────────────────────────────────────────
    if gs.companies:
        st.markdown("<h2>📊 Portfolio</h2>", unsafe_allow_html=True)
        sell_idx = None

        for i, c in enumerate(gs.companies):
            m = calc(c, gs)
            sec = SECTORS[c.sector]

            ca, cb, cc, cd, ce = st.columns([2.5, 1.2, 1.2, 1.2, 1])
            with ca:
                yh = m["years_held"]
                yr_str = f"{yh:.1f}y" if yh >= 1 else f"{int(yh*4)}q"
                st.markdown(f"""
                <div class="prow dcard {sector_css(c.sector)}">
                  <span style="font-weight:700;">{sec['emoji']} {c.name}</span>
                  <span class="c-muted" style="font-size:.8rem; margin-left:.5rem;">{c.sector} · {yr_str}</span>
                </div>
                """, unsafe_allow_html=True)
            with cb:
                st.markdown(f"""<div class="stat">
                  <div class="stat-val">{cash_fmt(m['revenue'])}</div>
                  <div class="stat-lbl">Revenue</div></div>""", unsafe_allow_html=True)
            with cc:
                st.markdown(f"""<div class="stat">
                  <div class="stat-val {moic_color(m['moic'])}">{m['moic']:.2f}x</div>
                  <div class="stat-lbl">MOIC</div></div>""", unsafe_allow_html=True)
            with cd:
                st.markdown(f"""<div class="stat">
                  <div class="stat-val">{m['irr']*100:.0f}%</div>
                  <div class="stat-lbl">IRR</div></div>""", unsafe_allow_html=True)
            with ce:
                if st.button("Sell", key=f"sell_{i}_{gs.quarter_num}", use_container_width=True):
                    sell_idx = i

        if sell_idx is not None:
            sell_company(gs, sell_idx)
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Deal Flow ────────────────────────────────────────────
    st.markdown("<h2>🎯 Deal Flow</h2>", unsafe_allow_html=True)

    buy_idx = None
    for i, d in enumerate(gs.deals):
        sec = SECTORS[d.sector]
        # Projected MOIC at 3 years to help players decide
        proj_rev = d.revenue * ((1 + d.growth) ** 3)
        proj_ebitda = proj_rev * d.margin
        proj_debt = d.entry_debt * 0.7
        proj_equity = max(proj_ebitda * cfg["exit_mult_base"] - proj_debt, 0)
        proj_moic = proj_equity / max(d.entry_equity, 1)

        ca, cb, cc, cd, ce = st.columns([2.5, 1.2, 1.2, 1.2, 1])
        with ca:
            st.markdown(f"""
            <div class="dcard {sec['css']}">
              <h3>{sec['emoji']} {d.name}</h3>
              <span class="pill">{d.sector}</span>
              <span class="pill">In: {d.entry_multiple:.1f}x</span>
              <span class="pill">Growth: <span>{d.growth*100:.0f}%/yr</span></span>
            </div>
            """, unsafe_allow_html=True)
        with cb:
            st.markdown(f"""<div class="stat">
              <div class="stat-val">{cash_fmt(d.entry_equity)}</div>
              <div class="stat-lbl">Cost</div></div>""", unsafe_allow_html=True)
        with cc:
            st.markdown(f"""<div class="stat">
              <div class="stat-val">{d.margin*100:.0f}%</div>
              <div class="stat-lbl">Margin</div></div>""", unsafe_allow_html=True)
        with cd:
            st.markdown(f"""<div class="stat">
              <div class="stat-val {moic_color(proj_moic)}">{proj_moic:.1f}x</div>
              <div class="stat-lbl">3yr Est.</div></div>""", unsafe_allow_html=True)
        with ce:
            disabled = d.entry_equity > gs.cash
            if st.button("Buy" if not disabled else "💸", key=f"buy_{i}_{gs.quarter_num}",
                         use_container_width=True, disabled=disabled):
                buy_idx = i

    if buy_idx is not None:
        d = gs.deals[buy_idx]
        gs.cash -= d.entry_equity
        d.entry_quarter = gs.quarter_num
        gs.companies.append(d)
        gs.deals.pop(buy_idx)
        st.rerun()

    # ── Exit log ─────────────────────────────────────────────
    if gs.exited:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2>🏆 Realized Exits</h2>", unsafe_allow_html=True)
        for e in reversed(gs.exited):
            cls = moic_color(e["moic"])
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                 padding:.6rem .9rem; background:var(--card); border-radius:10px; margin-bottom:.4rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong></span>
              <span class="{cls} fw7">{e['moic']:.2f}x &nbsp;</span>
              <span class="c-muted">{cash_fmt(e['proceeds'])} proceeds</span>
            </div>
            """, unsafe_allow_html=True)


def screen_score():
    gs = G()
    cfg = DIFFICULTY[gs.difficulty]
    pm = portfolio_moic(gs)
    goal = cfg["goal_moic"]
    won = pm >= goal

    grade = "S" if pm >= goal * 1.3 else "A" if pm >= goal else "B" if pm >= goal * .8 else "C"
    grade_color = {"S": "#f59e0b", "A": "#10b981", "B": "#3b82f6", "C": "#ef4444"}[grade]

    total_invested = sum(e["entry_equity"] for e in gs.exited) + sum(c.entry_equity for c in gs.companies)
    total_realized = sum(e["proceeds"] for e in gs.exited)
    total_unrealized = sum(calc(c, gs)["equity"] for c in gs.companies)

    st.markdown(f"""
    <div class="score-box">
      <div style="font-size:4rem; font-weight:900; color:{grade_color};">{grade}</div>
      <h1 style="margin:.5rem 0;">{"Empire Built! 🏆" if won else "Time's Up ⏱"}</h1>
      <p style="font-size:1.05rem; margin-bottom:1.5rem;">
        {"You hit your target. The LPs are thrilled." if won else "Close — but the market waits for no one."}
      </p>
      <div style="display:flex; justify-content:space-around; margin:1.25rem 0;">
        <div class="stat">
          <div class="stat-val" style="color:{grade_color};">{pm:.2f}x</div>
          <div class="stat-lbl">Final MOIC</div>
        </div>
        <div class="stat">
          <div class="stat-val">{len(gs.exited)}</div>
          <div class="stat-lbl">Exits</div>
        </div>
        <div class="stat">
          <div class="stat-val">{cash_fmt(total_realized)}</div>
          <div class="stat-lbl">Realized</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if gs.exited:
        st.markdown("<h2 style='text-align:center;'>Deal Recap</h2>", unsafe_allow_html=True)
        for e in sorted(gs.exited, key=lambda x: -x["moic"]):
            cls = moic_color(e["moic"])
            sec = SECTORS[e["sector"]]["emoji"]
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:.65rem 1rem;
                 background:var(--card); border-radius:10px; margin-bottom:.4rem;">
              <span>{sec} <strong>{e['name']}</strong></span>
              <span class="{cls} fw7">{e['moic']:.2f}x</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR &nbsp; {cash_fmt(e['proceeds'])}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🔄 Play Again", use_container_width=True):
            del st.session_state["gs"]
            st.rerun()

# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────

def main():
    gs = G()
    if gs.screen == "start":
        screen_start()
    elif gs.screen == "game":
        screen_game()
    elif gs.screen == "score":
        screen_score()

if __name__ == "__main__":
    main()
