"""
CarryForge — Premium PE Empire Game
===================================
Pure game experience. Fast, fun, smooth, visually beautiful.
No educational bloat. Just enjoyment.

Tech: Streamlit + Plotly + SQLite
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass
import random
import hashlib

# ============================================================================
# CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="CarryForge",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    :root {
        --dark: #0a0e27;
        --card: #1a1f3a;
        --accent: #10b981;
        --gold: #f59e0b;
        --red: #ef4444;
        --text: #f0f0f0;
        --muted: #a0a0a0;
    }

    * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }

    body, .stApp {
        background-color: var(--dark);
        color: var(--text);
    }

    .stApp {
        background-image:
            radial-gradient(circle at 20% 50%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(245, 158, 11, 0.03) 0%, transparent 50%);
    }

    /* Cards */
    .game-card {
        background: linear-gradient(135deg, var(--card) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }

    .game-card:hover {
        border-color: var(--accent);
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.2);
        transform: translateY(-2px);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
        font-size: 14px;
    }

    .stButton > button:hover {
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.35);
        transform: translateY(-2px);
    }

    /* Metrics */
    .metric-big {
        text-align: center;
        padding: 20px;
        background: var(--card);
        border-radius: 12px;
        margin: 8px 0;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--accent);
        margin: 8px 0;
    }

    .metric-label {
        font-size: 12px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Text colors */
    .text-green { color: var(--accent); font-weight: 600; }
    .text-gold { color: var(--gold); font-weight: 600; }
    .text-red { color: var(--red); font-weight: 600; }

    h1, h2, h3 { color: var(--text); margin-top: 20px; margin-bottom: 10px; }
    h1 { font-size: 32px; font-weight: 700; }
    h2 { font-size: 24px; font-weight: 600; }
    h3 { font-size: 18px; font-weight: 600; }

    /* Sidebar */
    .stSidebar { display: none; }

    /* Expander */
    .streamlit-expanderHeader { font-weight: 600; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

def init_game():
    if "game" not in st.session_state:
        st.session_state.game = {
            "screen": "start",
            "year": 2024,
            "quarter": 1,
            "cash": 50_000_000,
            "companies": [],
            "exited": [],
            "difficulty": "Balanced",
        }
    if "deals" not in st.session_state:
        st.session_state.deals = generate_deals(6)

# ============================================================================
# GAME LOGIC
# ============================================================================

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
    entry_year: int = 0

SECTORS = {
    "SaaS": {"emoji": "💻", "color": "#3b82f6", "rev": (50, 150), "margin": (0.30, 0.50), "growth": (0.15, 0.35)},
    "Hardware": {"emoji": "🔧", "color": "#8b5cf6", "rev": (100, 300), "margin": (0.08, 0.20), "growth": (0.05, 0.15)},
    "Healthcare": {"emoji": "🏥", "color": "#ec4899", "rev": (80, 250), "margin": (0.15, 0.30), "growth": (0.10, 0.25)},
    "Fintech": {"emoji": "💰", "color": "#14b8a6", "rev": (40, 120), "margin": (0.20, 0.40), "growth": (0.25, 0.50)},
}

def generate_deals(count=6):
    deals = []
    for _ in range(count):
        sector = random.choice(list(SECTORS.keys()))
        params = SECTORS[sector]

        rev = np.random.uniform(*params["rev"])
        margin = np.random.uniform(*params["margin"])
        ebitda = rev * margin
        growth = np.random.uniform(*params["growth"])
        entry_mult = np.random.uniform(6.5, 9.5)
        entry_equity = ebitda * entry_mult
        entry_debt = entry_equity * np.random.uniform(1.8, 2.8)

        names = {
            "SaaS": ["CloudVault", "DataFlow", "SyncHub", "AutoScale", "SnapMetrics"],
            "Hardware": ["TechWorks", "PrecisionCo", "SmartBuild", "InnovateLabs"],
            "Healthcare": ["HealthPlus", "CareFlow", "MedTech", "LifeSpan"],
            "Fintech": ["PayHub", "BlockChain+", "TradeFlow", "VaultSecure"],
        }

        company = Company(
            id=hashlib.md5(f"{datetime.now()}{random.random()}".encode()).hexdigest()[:8],
            name=random.choice(names[sector]),
            sector=sector,
            revenue=rev,
            ebitda=ebitda,
            margin=margin,
            growth=growth,
            entry_multiple=entry_mult,
            entry_equity=entry_equity,
            entry_debt=entry_debt,
            debt=0,
        )
        deals.append(company)

    return deals

def calc_company(c: Company, year: int):
    """Calculate current metrics."""
    years_held = year - c.entry_year

    revenue = c.revenue * ((1 + c.growth) ** years_held)
    ebitda = revenue * c.margin

    # Debt paydown
    fcf = ebitda * 0.60
    principal = min(max(fcf * 0.25, 0), c.debt)
    debt = max(c.debt - principal, 0)

    # Exit
    exit_mult = 8.5
    ev = ebitda * exit_mult
    equity = max(ev - debt, 0)
    moic = equity / max(c.entry_equity, 1)
    irr = ((moic) ** (1 / max(years_held, 1)) - 1) if years_held > 0 else 0

    return {
        "revenue": revenue,
        "ebitda": ebitda,
        "debt": debt,
        "equity": equity,
        "moic": moic,
        "irr": irr,
    }

# ============================================================================
# SCREENS
# ============================================================================

def screen_start():
    """Start screen."""
    st.markdown("""
    <div style='text-align: center; padding: 60px 0; max-width: 600px; margin: 0 auto;'>
        <div style='font-size: 64px; margin-bottom: 20px;'>💼</div>
        <h1 style='font-size: 48px; margin: 0; background: linear-gradient(135deg, #10b981, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            CarryForge
        </h1>
        <p style='font-size: 18px; color: #a0a0a0; margin-top: 10px;'>Build your PE empire</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("🎮 Easy", use_container_width=True, key="easy"):
            st.session_state.game["difficulty"] = "Easy"
            st.session_state.game["screen"] = "game"
            st.rerun()

    with col2:
        if st.button("⚖️ Balanced", use_container_width=True, key="balanced"):
            st.session_state.game["difficulty"] = "Balanced"
            st.session_state.game["screen"] = "game"
            st.rerun()

    with col3:
        if st.button("🔥 Hard", use_container_width=True, key="hard"):
            st.session_state.game["difficulty"] = "Hard"
            st.session_state.game["screen"] = "game"
            st.rerun()

def screen_game():
    """Main game screen."""
    game = st.session_state.game

    # Header
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        st.markdown(f"<h2 style='margin: 0;'>CarryForge</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-big'><div class='metric-value'>${game['cash']/1e6:.0f}M</div><div class='metric-label'>Cash</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-big'><div class='metric-value'>{game['year']}</div><div class='metric-label'>Year</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-big'><div class='metric-value'>Q{game['quarter']}</div><div class='metric-label'>Quarter</div></div>", unsafe_allow_html=True)
    with col5:
        if st.button("→ Next Q", use_container_width=True, key="next_quarter"):
            game["quarter"] += 1
            if game["quarter"] > 4:
                game["quarter"] = 1
                game["year"] += 1
            st.session_state.deals = generate_deals(6)
            st.rerun()

    st.markdown("---")

    # Portfolio summary
    if game["companies"]:
        st.markdown("<h3>📊 Your Portfolio</h3>", unsafe_allow_html=True)

        for i, company in enumerate(game["companies"]):
            metrics = calc_company(company, game["year"])
            sector_info = SECTORS[company.sector]

            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

            with col1:
                st.markdown(f"**{sector_info['emoji']} {company.name}** ({company.sector})")
            with col2:
                st.markdown(f"<div class='text-green'>${metrics['revenue']/1e6:.0f}M rev</div>", unsafe_allow_html=True)
            with col3:
                moic_color = "text-green" if metrics["moic"] > 1.5 else "text-gold" if metrics["moic"] > 1.2 else ""
                st.markdown(f"<div class='{moic_color}'>{metrics['moic']:.2f}x</div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"{metrics['irr']*100:.0f}% IRR")
            with col5:
                if st.button("Sell", key=f"sell_{i}", use_container_width=True):
                    game["cash"] += metrics["equity"]
                    game["exited"].append({
                        "name": company.name,
                        "moic": metrics["moic"],
                        "proceeds": metrics["equity"],
                    })
                    game["companies"].pop(i)
                    st.balloons()
                    st.rerun()

        st.markdown("---")

    # Deal flow
    st.markdown("<h3>🎯 Available Deals (Pick 1 per quarter)</h3>", unsafe_allow_html=True)

    for i, deal in enumerate(st.session_state.deals):
        sector_info = SECTORS[deal.sector]

        st.markdown(f"<div class='game-card'>", unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns([2.5, 1, 1, 1, 1])

        with col1:
            st.markdown(f"### {sector_info['emoji']} {deal.name}")
        with col2:
            st.markdown(f"<div class='metric-label'>Entry</div><div style='font-size: 18px; font-weight: 700;'>{deal.entry_multiple:.1f}x</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-label'>Growth</div><div style='font-size: 18px; font-weight: 700;'>{deal.growth*100:.0f}%</div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='metric-label'>Cost</div><div style='font-size: 18px; font-weight: 700;'>${deal.entry_equity/1e6:.0f}M</div>", unsafe_allow_html=True)
        with col5:
            if st.button("Buy", key=f"buy_{i}", use_container_width=True):
                if deal.entry_equity <= game["cash"]:
                    deal.entry_year = game["year"]
                    deal.debt = deal.entry_debt
                    game["companies"].append(deal)
                    game["cash"] -= deal.entry_equity
                    st.session_state.deals.pop(i)
                    st.success(f"✅ Acquired {deal.name}!")
                    st.rerun()
                else:
                    st.error("❌ Not enough cash")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Results
    if game["exited"]:
        st.markdown("<h3>🎉 Exits</h3>", unsafe_allow_html=True)

        for exit_deal in game["exited"]:
            moic_color = "text-green" if exit_deal["moic"] > 2.0 else "text-gold"
            st.markdown(f"**{exit_deal['name']}** — <span class='{moic_color}'>{exit_deal['moic']:.2f}x return</span> | ${exit_deal['proceeds']/1e6:.0f}M proceeds", unsafe_allow_html=True)

# ============================================================================
# MAIN
# ============================================================================

def main():
    init_game()

    if st.session_state.game["screen"] == "start":
        screen_start()
    elif st.session_state.game["screen"] == "game":
        screen_game()

if __name__ == "__main__":
    main()
