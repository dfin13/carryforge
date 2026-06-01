"""
CarryForge: Premium Private Equity Simulation Game
===================================================
A mobile-first PE empire builder with deep mechanics and beautiful UX.

Tech: Python 3.11+ | Streamlit 1.40+ | SQLite | Plotly | Pandas
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import json
import os
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
import random
import hashlib

# ============================================================================
# CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="CarryForge",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark finance theme with emerald accents
CUSTOM_CSS = """
<style>
    :root {
        --primary-dark: #0a0e27;
        --secondary-dark: #1a1f3a;
        --accent-emerald: #10b981;
        --accent-gold: #f59e0b;
        --accent-red: #ef4444;
        --text-primary: #f0f0f0;
        --text-secondary: #a0a0a0;
        --border-color: #2d3748;
    }

    body {
        background-color: var(--primary-dark);
        color: var(--text-primary);
    }

    .stApp {
        background-color: var(--primary-dark);
        background-image:
            radial-gradient(circle at 20% 50%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(245, 158, 11, 0.03) 0%, transparent 50%);
    }

    .stMetric {
        background-color: var(--secondary-dark);
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid var(--accent-emerald);
    }

    .card {
        background-color: var(--secondary-dark);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    .card:hover {
        border-color: var(--accent-emerald);
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.1);
    }

    .deal-card {
        background: linear-gradient(135deg, var(--secondary-dark) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid var(--accent-emerald);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }

    .highlight-positive {
        color: var(--accent-emerald);
        font-weight: 600;
    }

    .highlight-negative {
        color: var(--accent-red);
        font-weight: 600;
    }

    .highlight-gold {
        color: var(--accent-gold);
        font-weight: 600;
    }

    h1, h2, h3 {
        color: var(--text-primary);
    }

    .stButton>button {
        background-color: var(--accent-emerald);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        background-color: #059669;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }

    .metric-row {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    @media (max-width: 768px) {
        .stApp {
            padding-bottom: 60px;
        }

        .metric-row {
            flex-direction: column;
        }
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================================
# DATA MODELS & ENUMS
# ============================================================================

class Difficulty(Enum):
    CASUAL = "Casual"
    BALANCED = "Balanced"
    HARDCORE = "Hardcore"

class CompanyStage(Enum):
    PROSPECT = "Prospect"
    OWNED = "Owned"
    EXITED = "Exited"

class SectorEnum(Enum):
    SAAS = "SaaS"
    MANUFACTURING = "Manufacturing"
    HEALTHCARE = "Healthcare"
    RETAIL = "Retail"
    BUSINESS_SERVICES = "Business Services"
    FINTECH = "FinTech"
    LOGISTICS = "Logistics"
    MEDIA = "Media & Content"

@dataclass
class Company:
    id: str
    name: str
    sector: str
    stage: str
    entry_year: int
    entry_multiple: float
    entry_ebitda: float
    current_ebitda: float
    revenue_growth_rate: float
    ebitda_margin: float
    revenue: float
    debt: float
    shares_owned: float
    entry_debt: float
    entry_revenue: float
    entry_equity_check: float
    add_on_acquisitions: List[Dict] = None
    events: List[Dict] = None
    value_creation_levers: Dict = None

    def __post_init__(self):
        if self.add_on_acquisitions is None:
            self.add_on_acquisitions = []
        if self.events is None:
            self.events = []
        if self.value_creation_levers is None:
            self.value_creation_levers = {
                "revenue_growth": 0,
                "margin_expansion": 0,
                "multiple_arbitrage": 0,
            }

@dataclass
class Fund:
    fund_id: str
    name: str
    raised_capital: float
    committed_capital: float
    invested_capital: float
    available_capital: float
    portfolio: List[Company] = None
    realized_distributions: float = 0.0
    dpi: float = 1.0
    moic: float = 1.0
    irr: float = 0.0
    created_quarter: int = 0

    def __post_init__(self):
        if self.portfolio is None:
            self.portfolio = []

@dataclass
class GameState:
    current_quarter: int
    current_year: int
    difficulty: str
    funds: List[Fund] = None
    portfolio_companies: List[Company] = None
    cash_balance: float = 0.0
    total_committed: float = 0.0
    game_events: List[Dict] = None
    save_timestamp: str = ""

    def __post_init__(self):
        if self.funds is None:
            self.funds = []
        if self.portfolio_companies is None:
            self.portfolio_companies = []
        if self.game_events is None:
            self.game_events = []

# ============================================================================
# DATABASE & PERSISTENCE
# ============================================================================

DB_PATH = ".claude/carryforge.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Initialize SQLite database with save slots."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS saves (
            slot_id INTEGER PRIMARY KEY,
            game_state TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            quarter INTEGER,
            fund_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_game(slot_id: int, game_state: GameState):
    """Save game to SQLite."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    game_json = json.dumps({
        "current_quarter": game_state.current_quarter,
        "current_year": game_state.current_year,
        "difficulty": game_state.difficulty,
        "cash_balance": game_state.cash_balance,
        "funds": [asdict(f) for f in game_state.funds],
        "portfolio_companies": [asdict(c) for c in game_state.portfolio_companies],
        "game_events": game_state.game_events,
    }, default=str)

    timestamp = datetime.now().isoformat()
    fund_name = game_state.funds[0].name if game_state.funds else "New Game"

    c.execute('''
        INSERT OR REPLACE INTO saves (slot_id, game_state, timestamp, quarter, fund_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (slot_id, game_json, timestamp, game_state.current_quarter, fund_name))

    conn.commit()
    conn.close()
    st.success(f"Game saved to Slot {slot_id}!")

def load_game(slot_id: int) -> Optional[GameState]:
    """Load game from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT game_state FROM saves WHERE slot_id = ?', (slot_id,))
    result = c.fetchone()
    conn.close()

    if not result:
        return None

    data = json.loads(result[0])

    # Reconstruct objects
    funds = [Fund(**f) for f in data.get("funds", [])]
    companies = [Company(**c) for c in data.get("portfolio_companies", [])]

    return GameState(
        current_quarter=data["current_quarter"],
        current_year=data["current_year"],
        difficulty=data["difficulty"],
        cash_balance=data["cash_balance"],
        funds=funds,
        portfolio_companies=companies,
        game_events=data.get("game_events", []),
    )

def get_all_saves() -> List[Tuple[int, str, str, int]]:
    """Get all saved games."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT slot_id, fund_name, timestamp, quarter FROM saves ORDER BY timestamp DESC')
    result = c.fetchall()
    conn.close()
    return result

# ============================================================================
# GAME LOGIC & MECHANICS
# ============================================================================

def generate_company(sector: Optional[str] = None, difficulty: str = "Balanced") -> Company:
    """Procedural company generator with hidden traits."""
    if sector is None:
        sector = random.choice([s.value for s in SectorEnum])

    company_id = hashlib.md5(f"{datetime.now()}{random.random()}".encode()).hexdigest()[:8]

    # Base parameters by sector
    sector_params = {
        "SaaS": {"rev_range": (50, 150), "margin_range": (0.30, 0.50), "growth_range": (0.15, 0.35)},
        "Manufacturing": {"rev_range": (100, 300), "margin_range": (0.08, 0.15), "growth_range": (0.05, 0.12)},
        "Healthcare": {"rev_range": (80, 250), "margin_range": (0.15, 0.30), "growth_range": (0.10, 0.25)},
        "Retail": {"rev_range": (150, 400), "margin_range": (0.05, 0.12), "growth_range": (0.02, 0.10)},
        "Business Services": {"rev_range": (60, 200), "margin_range": (0.18, 0.35), "growth_range": (0.10, 0.25)},
        "FinTech": {"rev_range": (40, 120), "margin_range": (0.20, 0.40), "growth_range": (0.25, 0.50)},
        "Logistics": {"rev_range": (120, 350), "margin_range": (0.06, 0.12), "growth_range": (0.05, 0.15)},
        "Media & Content": {"rev_range": (30, 100), "margin_range": (0.15, 0.30), "growth_range": (0.10, 0.30)},
    }

    params = sector_params.get(sector, sector_params["Business Services"])

    revenue = np.random.uniform(*params["rev_range"])
    margin = np.random.uniform(*params["margin_range"])
    ebitda = revenue * margin
    growth_rate = np.random.uniform(*params["growth_range"])

    # Entry terms (6-10x EBITDA multiple)
    entry_multiple = np.random.uniform(6.0, 10.0)
    entry_equity = ebitda * entry_multiple
    entry_debt = entry_equity * np.random.uniform(1.5, 3.0)

    company_names = {
        "SaaS": ["CloudWorks", "DataSense", "AnalyticsPro", "TechFlow", "SyncHub"],
        "Manufacturing": ["PrecisionCo", "IndustrialPro", "ManuFlex", "TechManuf", "Precision Plus"],
        "Healthcare": ["MedCare Solutions", "HealthFirst", "CarePoint", "MediServe", "HealthTech"],
        "Retail": ["RetailMax", "ShopHub", "MerchandisePro", "StoreFlow", "RetailCore"],
        "Business Services": ["ConsultPro", "BusinessFlow", "ServicePro", "ConsultHub", "ProServe"],
        "FinTech": ["FinFlow", "PayTech", "CryptoFlow", "TradeHub", "FinCore"],
        "Logistics": ["LogisticsPro", "ShipHub", "TransFlow", "CargoHub", "DeliveryMax"],
        "Media & Content": ["CreativeStudio", "ContentHub", "MediaFlow", "StudioPro", "CreativeForge"],
    }

    name = random.choice(company_names.get(sector, ["Venture Co.", "Innovation Inc.", "Growth Labs"]))

    return Company(
        id=company_id,
        name=name,
        sector=sector,
        stage=CompanyStage.PROSPECT.value,
        entry_year=0,
        entry_multiple=entry_multiple,
        entry_ebitda=ebitda,
        current_ebitda=ebitda,
        revenue_growth_rate=growth_rate,
        ebitda_margin=margin,
        revenue=revenue,
        debt=0,
        shares_owned=0,
        entry_debt=entry_debt,
        entry_revenue=revenue,
        entry_equity_check=entry_equity,
    )

def calculate_company_value(company: Company, year_number: int) -> Dict:
    """Calculate company value, debt, and returns metrics."""
    years_held = year_number - company.entry_year

    # EBITDA growth with margin expansion
    ebitda = company.entry_ebitda * ((1 + company.revenue_growth_rate) ** years_held)
    ebitda *= (1 + company.value_creation_levers.get("margin_expansion", 0) * 0.1)

    # Revenue growth
    revenue = company.entry_revenue * ((1 + company.revenue_growth_rate) ** years_held)

    # Debt paydown (assume 20% annual principal paydown from FCF)
    debt_schedule = company.entry_debt
    for _ in range(years_held):
        fcf = ebitda * 0.60  # Assume 60% conversion to FCF
        principal_paid = min(fcf * 0.20, debt_schedule)
        debt_schedule -= principal_paid

    debt = max(debt_schedule, 0)

    # Exit multiple (base + leverage from growth levers)
    exit_multiple = 8.5  # Base exit multiple
    exit_multiple *= (1 + company.value_creation_levers.get("multiple_arbitrage", 0) * 0.05)

    # Enterprise value at exit
    enterprise_value = ebitda * exit_multiple

    # Equity value = EV - Net Debt
    equity_value = enterprise_value - debt

    # Returns (on original equity check)
    moic = equity_value / max(company.entry_equity_check, 1)
    irr = ((moic) ** (1 / max(years_held, 1)) - 1) if years_held > 0 else 0

    return {
        "ebitda": ebitda,
        "revenue": revenue,
        "debt": debt,
        "enterprise_value": enterprise_value,
        "equity_value": max(equity_value, 0),
        "moic": moic,
        "irr": irr,
        "multiple_paid": company.entry_multiple,
        "multiple_exiting": exit_multiple,
    }

def generate_deal_flow(quarter: int, difficulty: str, num_deals: int = 6) -> List[Company]:
    """Generate random deal flow for the quarter."""
    deals = []
    for _ in range(num_deals):
        company = generate_company(difficulty=difficulty)
        company.stage = CompanyStage.PROSPECT.value
        deals.append(company)
    return deals

def generate_quarterly_events(quarter: int, fund: Fund) -> List[Dict]:
    """Generate random events and narrative moments."""
    events = []
    event_pool = [
        {"type": "market_tailwind", "text": "Strong M&A market sentiment drives multiple expansion", "impact": 0.05},
        {"type": "market_headwind", "text": "Rising rates pressure EBITDA multiples", "impact": -0.05},
        {"type": "portfolio_win", "text": "Top portfolio company exceeds guidance", "impact": 0.10},
        {"type": "portfolio_loss", "text": "One company misses targets", "impact": -0.08},
        {"type": "fundraising_opportunity", "text": "LP interest in Fund II discussions", "impact": 0.02},
        {"type": "competitor_move", "text": "Rival PE firm closes large fund", "impact": 0.00},
    ]

    # 40% chance of event per quarter
    if random.random() < 0.4:
        event = random.choice(event_pool)
        events.append({
            "quarter": quarter,
            "title": event["text"],
            "type": event["type"],
            "impact": event["impact"],
        })

    return events

def advance_quarter(game_state: GameState):
    """Simulate one quarter forward."""
    game_state.current_quarter += 1
    game_state.current_year = 2024 + (game_state.current_quarter - 1) // 4

    # Advance each portfolio company
    for company in game_state.portfolio_companies:
        if company.stage == CompanyStage.OWNED.value:
            metrics = calculate_company_value(company, game_state.current_year)
            company.current_ebitda = metrics["ebitda"]
            company.revenue = metrics["revenue"]
            company.debt = metrics["debt"]

    # Generate events
    if game_state.funds:
        new_events = generate_quarterly_events(game_state.current_quarter, game_state.funds[0])
        game_state.game_events.extend(new_events)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize or restore Streamlit session state."""
    if "game_state" not in st.session_state:
        st.session_state.game_state = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "menu"
    if "show_tutorial" not in st.session_state:
        st.session_state.show_tutorial = False

init_db()
init_session_state()

# ============================================================================
# UI PAGES
# ============================================================================

def page_main_menu():
    """Home/menu screen."""
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <h1 style='font-size: 3rem; background: linear-gradient(135deg, #10b981, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;'>
            ♦ CarryForge ♦
        </h1>
        <p style='color: #a0a0a0; font-size: 1.1rem; margin-top: 0.5rem;'>
            The Premier Private Equity Empire Builder
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown("<h3 style='text-align: center;'>Start Your PE Dynasty</h3>", unsafe_allow_html=True)

        if st.button("🚀 New Game", use_container_width=True, key="new_game_btn"):
            st.session_state.current_page = "difficulty_select"
            st.rerun()

        st.markdown("### Load Game")
        saves = get_all_saves()
        if saves:
            for slot_id, fund_name, timestamp, quarter in saves:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    if st.button(f"📊 {fund_name} (Q{quarter})", key=f"load_{slot_id}", use_container_width=True):
                        st.session_state.game_state = load_game(slot_id)
                        st.session_state.current_page = "overview"
                        st.rerun()
                with col_b:
                    st.caption(f"Slot {slot_id}")
                with col_c:
                    st.caption(timestamp.split("T")[0])
        else:
            st.info("No saved games yet. Start a new game!")

        st.markdown("---")
        st.markdown("<h3 style='text-align: center;'>How to Play</h3>", unsafe_allow_html=True)

        with st.expander("📖 Game Basics"):
            st.markdown("""
            **CarryForge** is a PE simulation where you:

            1. **Raise capital** from LPs ($50M Fund I to start)
            2. **Source deals** from the deal flow each quarter
            3. **Create value** via revenue growth, margins, and multiple expansion
            4. **Exit winners** and realize returns for your LPs
            5. **Grow your firm** by raising Fund II with strong returns

            Your goal: **Maximize MOIC (money multiple) and IRR** across your portfolio.
            """)

        with st.expander("💡 Pro Tips"):
            st.markdown("""
            - **Diversify sectors** — avoid betting everything on one industry
            - **Watch multiples** — buy at 6x EBITDA, exit at 8.5x–10x
            - **Manage leverage** — too much debt kills returns in downturns
            - **Hold winners** — patience on high-growth companies pays off
            - **Monitor events** — macro headwinds/tailwinds affect all companies
            """)

def page_difficulty_select():
    """Choose difficulty at game start."""
    st.markdown("<h2 style='text-align: center;'>Choose Your Challenge</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    difficulties = [
        ("Casual", "Easier LBO outcomes, more forgiving markets, higher exit multiples", col1),
        ("Balanced", "Realistic PE scenarios, fair market conditions", col2),
        ("Hardcore", "Volatile markets, tight covenants, ruthless competition", col3),
    ]

    for diff_name, desc, col in difficulties:
        with col:
            st.markdown(f"<div class='card'><h3>{diff_name}</h3><p>{desc}</p></div>", unsafe_allow_html=True)
            if st.button(f"Play {diff_name}", use_container_width=True, key=f"diff_{diff_name}"):
                # Initialize new game
                fund = Fund(
                    fund_id="fund_1",
                    name="Fund I: Genesis",
                    raised_capital=50_000_000,
                    committed_capital=50_000_000,
                    invested_capital=0,
                    available_capital=50_000_000,
                    portfolio=[],
                    created_quarter=1,
                )

                game_state = GameState(
                    current_quarter=1,
                    current_year=2024,
                    difficulty=diff_name,
                    funds=[fund],
                    cash_balance=50_000_000,
                )

                st.session_state.game_state = game_state
                st.session_state.current_page = "overview"
                st.session_state.show_tutorial = True
                st.rerun()

def page_overview():
    """Main dashboard/overview."""
    gs = st.session_state.game_state

    # Header with quarter/year info
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown(f"<h2>CarryForge | Fund I: Genesis</h2>", unsafe_allow_html=True)
    with col2:
        st.metric("Quarter", f"Q{gs.current_quarter}", f"Year {gs.current_year}")
    with col3:
        st.metric("Difficulty", gs.difficulty)
    with col4:
        if st.button("💾 Save Game", key="save_overview"):
            save_game(1, gs)

    # Key metrics row
    st.markdown("---")
    st.markdown("<h3>Fund Performance</h3>", unsafe_allow_html=True)

    fund = gs.funds[0]

    metrics_col1, metrics_col2, metrics_col3, metrics_col4, metrics_col5 = st.columns(5)

    with metrics_col1:
        st.metric("Capital Raised", f"${fund.raised_capital/1e6:.1f}M", "✓")
    with metrics_col2:
        st.metric("Deployed", f"${fund.invested_capital/1e6:.1f}M", f"{fund.invested_capital/fund.raised_capital*100:.0f}%")
    with metrics_col3:
        st.metric("Available", f"${fund.available_capital/1e6:.1f}M", "")
    with metrics_col4:
        st.metric("Portfolio Value", f"${sum(max(calculate_company_value(c, gs.current_year)['equity_value'], 0) for c in gs.portfolio_companies)/1e6:.1f}M", "")
    with metrics_col5:
        portfolio_moic = fund.moic if gs.portfolio_companies else 1.0
        st.metric("MOIC", f"{portfolio_moic:.2f}x", f"{(portfolio_moic-1)*100:+.1f}%")

    # Portfolio holdings
    st.markdown("---")
    st.markdown("<h3>Portfolio Companies</h3>", unsafe_allow_html=True)

    if gs.portfolio_companies:
        portfolio_data = []
        for company in gs.portfolio_companies:
            if company.stage == CompanyStage.OWNED.value:
                metrics = calculate_company_value(company, gs.current_year)
                portfolio_data.append({
                    "Company": company.name,
                    "Sector": company.sector,
                    "Revenue ($M)": f"${metrics['revenue']/1e6:.1f}",
                    "EBITDA ($M)": f"${metrics['ebitda']/1e6:.1f}",
                    "Debt ($M)": f"${metrics['debt']/1e6:.1f}",
                    "Equity Value ($M)": f"${metrics['equity_value']/1e6:.1f}",
                    "MOIC": f"{metrics['moic']:.2f}x",
                    "IRR": f"{metrics['irr']*100:.1f}%",
                })

        df_portfolio = pd.DataFrame(portfolio_data)
        st.dataframe(df_portfolio, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No portfolio companies yet. Browse deal flow to invest!")

    # Recent events
    if gs.game_events:
        st.markdown("---")
        st.markdown("<h3>Recent Events</h3>", unsafe_allow_html=True)
        for event in gs.game_events[-3:]:
            event_color = "🟢" if event["impact"] > 0 else "🔴" if event["impact"] < 0 else "⚪"
            st.markdown(f"**{event_color} Q{event['quarter']}:** {event['title']}")

    # Navigation buttons
    st.markdown("---")
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)

    with nav_col1:
        if st.button("📋 Deal Flow", use_container_width=True, key="nav_deal_flow"):
            st.session_state.current_page = "deal_flow"
            st.rerun()
    with nav_col2:
        if st.button("🎯 Portfolio", use_container_width=True, key="nav_portfolio"):
            st.session_state.current_page = "portfolio"
            st.rerun()
    with nav_col3:
        if st.button("📊 Market", use_container_width=True, key="nav_market"):
            st.session_state.current_page = "market"
            st.rerun()
    with nav_col4:
        if st.button("💰 Fund & LPs", use_container_width=True, key="nav_fund"):
            st.session_state.current_page = "fund_lps"
            st.rerun()
    with nav_col5:
        if st.button("⏭️ Advance Quarter", use_container_width=True, key="advance_quarter_btn"):
            advance_quarter(gs)
            st.rerun()

def page_deal_flow():
    """Deal sourcing and investment decisions."""
    gs = st.session_state.game_state
    fund = gs.funds[0]

    st.markdown("<h2>📋 Deal Flow</h2>", unsafe_allow_html=True)
    st.markdown(f"**Available Capital:** ${fund.available_capital/1e6:.1f}M")

    # Generate deal flow if not in session
    if "deal_flow" not in st.session_state:
        st.session_state.deal_flow = generate_deal_flow(gs.current_quarter, gs.difficulty, num_deals=6)

    deals = st.session_state.deal_flow

    for i, company in enumerate(deals):
        with st.container():
            st.markdown(f"<div class='deal-card'>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown(f"### {company.name}")
                st.markdown(f"**Sector:** {company.sector}")
            with col2:
                st.markdown(f"**Revenue:** ${company.revenue:.1f}M")
                st.markdown(f"**EBITDA:** ${company.current_ebitda:.1f}M | **Margin:** {company.ebitda_margin*100:.1f}%")
                st.markdown(f"**Growth Rate:** {company.revenue_growth_rate*100:.1f}%")
            with col3:
                st.markdown(f"**Entry Multiple:** {company.entry_multiple:.1f}x EBITDA")
                entry_cost = company.current_ebitda * company.entry_multiple
                st.markdown(f"**Equity Check:** ${entry_cost/1e6:.1f}M")
                st.markdown(f"**Est. Debt:** ${company.entry_debt/1e6:.1f}M")

            # Investment controls
            col_inv1, col_inv2, col_inv3 = st.columns([1, 2, 1])
            with col_inv1:
                if st.button(f"Invest", key=f"invest_{i}", use_container_width=True):
                    entry_cost = company.current_ebitda * company.entry_multiple
                    if entry_cost <= fund.available_capital:
                        company.stage = CompanyStage.OWNED.value
                        company.entry_year = gs.current_year
                        company.debt = company.entry_debt
                        company.entry_equity_check = entry_cost

                        gs.portfolio_companies.append(company)
                        fund.available_capital -= entry_cost
                        fund.invested_capital += entry_cost

                        st.success(f"✅ Invested ${entry_cost/1e6:.1f}M in {company.name}!")
                        st.rerun()
                    else:
                        st.error("❌ Insufficient capital!")

            with col_inv2:
                if st.button(f"View Details", key=f"details_{i}", use_container_width=True):
                    with st.expander(f"{company.name} - Full Details"):
                        st.markdown(f"""
                        **Company Profile:**
                        - Sector: {company.sector}
                        - Current Revenue: ${company.revenue:.1f}M
                        - Current EBITDA: ${company.current_ebitda:.1f}M
                        - EBITDA Margin: {company.ebitda_margin*100:.1f}%
                        - Revenue Growth: {company.revenue_growth_rate*100:.1f}%

                        **Investment Terms:**
                        - Entry Multiple: {company.entry_multiple:.1f}x EBITDA
                        - Equity Investment: ${company.current_ebitda * company.entry_multiple/1e6:.1f}M
                        - Debt Financing: ${company.entry_debt/1e6:.1f}M
                        - Total Enterprise Value: ${(company.current_ebitda * company.entry_multiple + company.entry_debt)/1e6:.1f}M
                        """)

            with col_inv3:
                if st.button(f"Pass", key=f"pass_{i}", use_container_width=True):
                    st.info(f"Passed on {company.name}")

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("← Back to Overview", use_container_width=True, key="back_to_overview_1"):
        st.session_state.current_page = "overview"
        st.rerun()

def page_portfolio():
    """Detailed portfolio management & value creation."""
    gs = st.session_state.game_state

    st.markdown("<h2>🎯 Portfolio Management</h2>", unsafe_allow_html=True)

    portfolio = [c for c in gs.portfolio_companies if c.stage == CompanyStage.OWNED.value]

    if not portfolio:
        st.info("No portfolio companies. Invest in deals from Deal Flow!")
    else:
        for company in portfolio:
            metrics = calculate_company_value(company, gs.current_year)

            with st.container():
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"### {company.name}")
                    st.caption(company.sector)
                with col2:
                    st.metric("Revenue", f"${metrics['revenue']/1e6:.1f}M", f"+{company.revenue_growth_rate*100:.1f}%")
                with col3:
                    st.metric("EBITDA", f"${metrics['ebitda']/1e6:.1f}M")
                with col4:
                    st.metric("Equity Value", f"${metrics['equity_value']/1e6:.1f}M")

                st.markdown("---")

                # Value creation levers (sliders)
                st.markdown("**Value Creation Levers:**")

                col_rev, col_margin, col_mult = st.columns(3)

                with col_rev:
                    lever = st.slider(
                        "Revenue Growth (+)",
                        min_value=0.0,
                        max_value=0.5,
                        value=company.value_creation_levers.get("revenue_growth", 0),
                        step=0.05,
                        key=f"rev_lever_{company.id}",
                    )
                    company.value_creation_levers["revenue_growth"] = lever
                    st.caption(f"Apply +{lever*100:.0f}% to base growth")

                with col_margin:
                    lever = st.slider(
                        "Margin Expansion (+)",
                        min_value=0.0,
                        max_value=0.3,
                        value=company.value_creation_levers.get("margin_expansion", 0),
                        step=0.05,
                        key=f"margin_lever_{company.id}",
                    )
                    company.value_creation_levers["margin_expansion"] = lever
                    st.caption(f"Expand margins by {lever*100:.0f}%")

                with col_mult:
                    lever = st.slider(
                        "Multiple Arbitrage (+)",
                        min_value=0.0,
                        max_value=0.3,
                        value=company.value_creation_levers.get("multiple_arbitrage", 0),
                        step=0.05,
                        key=f"mult_lever_{company.id}",
                    )
                    company.value_creation_levers["multiple_arbitrage"] = lever
                    st.caption(f"Improve exit multiple by {lever*100:.0f}%")

                st.markdown("---")
                st.markdown("**Return Summary:**")

                col_moic, col_irr, col_exit = st.columns(3)
                with col_moic:
                    st.metric("MOIC", f"{metrics['moic']:.2f}x", f"{(metrics['moic']-1)*100:+.1f}%")
                with col_irr:
                    st.metric("IRR", f"{metrics['irr']*100:.1f}%")
                with col_exit:
                    years_held = gs.current_year - company.entry_year
                    st.metric("Years Held", f"{years_held}")

                st.markdown("---")

                # Exit button
                if st.button(f"🔓 Exit & Realize Returns", key=f"exit_{company.id}", use_container_width=True):
                    company.stage = CompanyStage.EXITED.value
                    gs.funds[0].available_capital += metrics["equity_value"]
                    gs.funds[0].realized_distributions += metrics["equity_value"]
                    st.success(f"✅ Exited {company.name} for ${metrics['equity_value']/1e6:.1f}M! MOIC: {metrics['moic']:.2f}x")
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("← Back to Overview", use_container_width=True, key="back_to_overview_2"):
        st.session_state.current_page = "overview"
        st.rerun()

def page_market():
    """Market conditions & macro trends."""
    gs = st.session_state.game_state

    st.markdown("<h2>📊 Market & Economy</h2>", unsafe_allow_html=True)

    # Market sentiment (simulated)
    quarter_offset = gs.current_quarter % 4
    market_sentiment = 0.5 + 0.3 * np.sin(gs.current_quarter / 4)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Market Sentiment", f"{market_sentiment*100:.0f}%", "Favorable" if market_sentiment > 0.5 else "Uncertain")
    with col2:
        st.metric("M&A Activity", "High" if quarter_offset in [0, 1] else "Moderate")
    with col3:
        st.metric("Interest Rates", "Elevated" if gs.current_year > 2025 else "Moderate")

    st.markdown("---")

    # Historical returns chart
    st.markdown("<h3>Historical Quarterly Returns</h3>", unsafe_allow_html=True)

    historical_returns = [1.0 + random.uniform(-0.02, 0.03) for _ in range(gs.current_quarter)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, gs.current_quarter + 1)),
        y=historical_returns,
        mode='lines+markers',
        name='Market Index',
        line=dict(color='#10b981', width=2),
        marker=dict(size=6),
    ))
    fig.update_layout(
        title="Simulated Market Index",
        xaxis_title="Quarter",
        yaxis_title="Value (Normalized)",
        template="plotly_dark",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(10,14,39,0.8)',
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    if st.button("← Back to Overview", use_container_width=True, key="back_to_overview_3"):
        st.session_state.current_page = "overview"
        st.rerun()

def page_fund_lps():
    """Fund & LP management."""
    gs = st.session_state.game_state
    fund = gs.funds[0]

    st.markdown("<h2>💰 Fund & LP Relations</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Raised", f"${fund.raised_capital/1e6:.1f}M")
    with col2:
        st.metric("Deployed %", f"{fund.invested_capital/fund.raised_capital*100:.1f}%")
    with col3:
        st.metric("Gross DPI", f"{(fund.realized_distributions + sum(max(calculate_company_value(c, gs.current_year)['equity_value'], 0) for c in gs.portfolio_companies if c.stage == CompanyStage.OWNED.value)) / max(fund.invested_capital, 1):.2f}x")

    st.markdown("---")
    st.markdown("<h3>LP Base</h3>", unsafe_allow_html=True)

    lp_data = pd.DataFrame({
        "LP": ["University Endowment", "Pension Fund A", "Family Office", "Foundations"],
        "Commitment ($M)": [15, 20, 10, 5],
        "Called ($M)": [fund.invested_capital/4, fund.invested_capital/4, fund.invested_capital/4, fund.invested_capital/4],
        "Satisfaction": ["😊", "😊", "😌", "😊"],
    })

    st.dataframe(lp_data, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("<h3>Fund II Readiness</h3>", unsafe_allow_html=True)

    # Calculate DPI
    gross_dpi = (fund.realized_distributions + sum(max(calculate_company_value(c, gs.current_year)['equity_value'], 0) for c in gs.portfolio_companies if c.stage == CompanyStage.OWNED.value)) / max(fund.invested_capital, 1)

    if gross_dpi > 1.5:
        st.success("✅ Strong performance! LPs ready for Fund II discussions.")
    elif gross_dpi > 1.2:
        st.info("⏳ Good progress. One more strong exit recommended before Fund II raise.")
    else:
        st.warning("⚠️ Build track record. Target 1.5x+ DPI before Fund II fundraise.")

    st.markdown("---")
    if st.button("← Back to Overview", use_container_width=True, key="back_to_overview_4"):
        st.session_state.current_page = "overview"
        st.rerun()

# ============================================================================
# MAIN APP ROUTER
# ============================================================================

def main():
    """Main app router."""
    if st.session_state.current_page == "menu":
        page_main_menu()
    elif st.session_state.current_page == "difficulty_select":
        page_difficulty_select()
    elif st.session_state.current_page == "overview":
        page_overview()
    elif st.session_state.current_page == "deal_flow":
        page_deal_flow()
    elif st.session_state.current_page == "portfolio":
        page_portfolio()
    elif st.session_state.current_page == "market":
        page_market()
    elif st.session_state.current_page == "fund_lps":
        page_fund_lps()
    else:
        st.error("Unknown page")
        if st.button("Return to Menu"):
            st.session_state.current_page = "menu"
            st.rerun()

if __name__ == "__main__":
    main()
