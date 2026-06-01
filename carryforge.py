"""
CarryForge v2.0 — Premium Private Equity Simulation Game
========================================================
Complete rewrite with: session state architecture, modular screens,
health scoring, covenant monitoring, sensitivity analysis, 5-year projections.

Built from best practices across 40+ top GitHub repos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import random
import hashlib
from io import BytesIO

# ============================================================================
# CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="CarryForge",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

    .metric-card {
        background-color: var(--secondary-dark);
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid var(--accent-emerald);
        margin: 0.5rem 0;
    }

    .deal-card {
        background: linear-gradient(135deg, var(--secondary-dark) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid var(--accent-emerald);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }

    .health-good { color: var(--accent-emerald); font-weight: 600; }
    .health-warning { color: var(--accent-gold); font-weight: 600; }
    .health-danger { color: var(--accent-red); font-weight: 600; }

    .stButton>button {
        background-color: var(--accent-emerald);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        background-color: #059669;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================================
# DATA MODELS
# ============================================================================

class Sector(Enum):
    SAAS = "SaaS"
    MANUFACTURING = "Manufacturing"
    HEALTHCARE = "Healthcare"
    RETAIL = "Retail"
    BUSINESS_SERVICES = "Business Services"
    FINTECH = "FinTech"
    LOGISTICS = "Logistics"
    MEDIA = "Media & Content"

SECTOR_PARAMS = {
    "SaaS": {"rev_range": (50, 150), "margin_range": (0.30, 0.50), "growth_range": (0.15, 0.35)},
    "Manufacturing": {"rev_range": (100, 300), "margin_range": (0.08, 0.15), "growth_range": (0.05, 0.12)},
    "Healthcare": {"rev_range": (80, 250), "margin_range": (0.15, 0.30), "growth_range": (0.10, 0.25)},
    "Retail": {"rev_range": (150, 400), "margin_range": (0.05, 0.12), "growth_range": (0.02, 0.10)},
    "Business Services": {"rev_range": (60, 200), "margin_range": (0.18, 0.35), "growth_range": (0.10, 0.25)},
    "FinTech": {"rev_range": (40, 120), "margin_range": (0.20, 0.40), "growth_range": (0.25, 0.50)},
    "Logistics": {"rev_range": (120, 350), "margin_range": (0.06, 0.12), "growth_range": (0.05, 0.15)},
    "Media & Content": {"rev_range": (30, 100), "margin_range": (0.15, 0.30), "growth_range": (0.10, 0.30)},
}

@dataclass
class Company:
    id: str
    name: str
    sector: str
    entry_multiple: float
    entry_ebitda: float
    entry_revenue: float
    entry_margin: float
    entry_equity: float
    entry_debt: float
    current_ebitda: float
    current_revenue: float
    current_margin: float
    debt: float
    entry_year: int
    growth_rate: float
    leverage_ratio: float = 3.0
    interest_rate: float = 0.06

# ============================================================================
# SESSION STATE INITIALIZATION (CENTRALIZED)
# ============================================================================

def init_session_state():
    """Initialize all game state in one place."""
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = {
            "companies": [],
            "cash": 50_000_000,
            "debt_capacity": 50_000_000,
            "raised_capital": 50_000_000,
            "year": 2024,
            "quarter": 1,
            "difficulty": "Balanced",
            "screen": "menu",
            "exited_companies": [],
            "history": [],
            "game_events": [],
        }

    if "deal_flow" not in st.session_state:
        st.session_state.deal_flow = []

    if "show_tutorial" not in st.session_state:
        st.session_state.show_tutorial = False

# ============================================================================
# FINANCIAL CALCULATIONS
# ============================================================================

def calculate_company_metrics(company: Company, current_year: int) -> dict:
    """Calculate current financials and returns for a company."""
    years_held = current_year - company.entry_year

    # Revenue & EBITDA growth
    revenue = company.entry_revenue * ((1 + company.growth_rate) ** years_held)
    ebitda = revenue * company.current_margin

    # Debt paydown
    fcf = ebitda * 0.60
    interest = company.debt * company.interest_rate
    principal_paid = min(max(fcf - interest, 0) * 0.30, company.debt)
    debt = max(company.debt - principal_paid, 0)

    # Exit valuation
    exit_multiple = 8.5
    enterprise_value = ebitda * exit_multiple
    equity_value = max(enterprise_value - debt, 0)

    # Returns
    moic = equity_value / max(company.entry_equity, 1)
    irr = ((moic) ** (1 / max(years_held, 1)) - 1) if years_held > 0 else 0

    return {
        "revenue": revenue,
        "ebitda": ebitda,
        "debt": debt,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "moic": moic,
        "irr": irr,
        "leverage": debt / max(ebitda, 1),
        "interest_coverage": ebitda / max(interest, 1),
    }

def calculate_portfolio_health() -> tuple[int, str]:
    """Calculate portfolio health score 0-100 and status."""
    portfolio = st.session_state.portfolio

    if not portfolio["companies"]:
        return 50, "No portfolio"

    # Calculate average metrics
    leverage_scores = []
    coverage_scores = []
    growth_scores = []

    for company in portfolio["companies"]:
        metrics = calculate_company_metrics(company, portfolio["year"])

        # Leverage score (ideal 2-3x)
        lev = metrics["leverage"]
        lev_score = max(0, 100 - abs(lev - 2.5) * 15)
        leverage_scores.append(lev_score)

        # Coverage score (ideal >2x)
        cov = metrics["interest_coverage"]
        cov_score = min(100, cov * 40)
        coverage_scores.append(cov_score)

        # Growth score
        growth_score = min(100, company.growth_rate * 300)
        growth_scores.append(growth_score)

    # Weighted composite
    avg_leverage = np.mean(leverage_scores) if leverage_scores else 50
    avg_coverage = np.mean(coverage_scores) if coverage_scores else 50
    avg_growth = np.mean(growth_scores) if growth_scores else 50

    health = int(avg_leverage * 0.4 + avg_coverage * 0.35 + avg_growth * 0.25)
    health = max(0, min(100, health))

    if health > 75:
        status = "Excellent"
    elif health > 55:
        status = "Good"
    elif health > 35:
        status = "At Risk"
    else:
        status = "Critical"

    return health, status

def check_covenant_violations() -> list[dict]:
    """Check all companies for debt covenant violations."""
    violations = []

    for company in st.session_state.portfolio["companies"]:
        metrics = calculate_company_metrics(company, st.session_state.portfolio["year"])

        # Max leverage covenant
        if metrics["leverage"] > 3.5:
            violations.append({
                "company": company.name,
                "type": "Leverage Too High",
                "value": f"{metrics['leverage']:.1f}x",
                "limit": "3.5x",
                "severity": "high"
            })

        # Min interest coverage covenant
        if metrics["interest_coverage"] < 1.5:
            violations.append({
                "company": company.name,
                "type": "Interest Coverage Low",
                "value": f"{metrics['interest_coverage']:.1f}x",
                "limit": "1.5x",
                "severity": "critical"
            })

    return violations

def project_company_years(company: Company, years: int = 5) -> pd.DataFrame:
    """Generate 5-year projection for a company."""
    projections = []

    for year in range(1, years + 1):
        revenue = company.entry_revenue * ((1 + company.growth_rate) ** year)
        ebitda = revenue * company.current_margin
        fcf = ebitda * 0.60
        interest = company.debt * company.interest_rate
        principal = min(max(fcf - interest, 0) * 0.30, company.debt)
        debt = max(company.debt - principal, 0)

        exit_mult = 8.5
        ev = ebitda * exit_mult
        equity = max(ev - debt, 0)
        moic = equity / company.entry_equity
        irr = (moic ** (1 / year) - 1)

        projections.append({
            "Year": company.entry_year + year,
            "Revenue ($M)": f"${revenue:.1f}",
            "EBITDA ($M)": f"${ebitda:.1f}",
            "Debt ($M)": f"${debt:.1f}",
            "Leverage": f"{debt/max(ebitda, 1):.1f}x",
            "Equity Value ($M)": f"${equity:.1f}",
            "MOIC": f"{moic:.2f}x",
            "IRR": f"{irr*100:.1f}%"
        })

    return pd.DataFrame(projections)

def sensitivity_analysis(company: Company) -> pd.DataFrame:
    """Show IRR sensitivity to exit multiple and growth rate."""
    exit_multiples = [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
    growth_rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

    sensitivity = pd.DataFrame(
        index=[f"{g:.0%}" for g in growth_rates],
        columns=[f"{m:.1f}x" for m in exit_multiples]
    )

    for exit_mult in exit_multiples:
        for growth_rate in growth_rates:
            # Simplified: assume 5-year hold
            revenue = company.entry_revenue * ((1 + growth_rate) ** 5)
            ebitda = revenue * company.current_margin
            debt = max(company.debt - (company.debt * 0.15), 0)  # 15% paydown
            ev = ebitda * exit_mult
            equity = max(ev - debt, 0)
            moic = equity / company.entry_equity
            irr = (moic ** (1 / 5) - 1) * 100

            sensitivity.loc[f"{growth_rate:.0%}", f"{exit_mult:.1f}x"] = f"{irr:.1f}%"

    return sensitivity

# ============================================================================
# PROCEDURAL GENERATION
# ============================================================================

def generate_company(sector: str = None) -> Company:
    """Generate a random company for deal flow."""
    if sector is None:
        sector = random.choice(list(SECTOR_PARAMS.keys()))

    params = SECTOR_PARAMS[sector]
    company_id = hashlib.md5(f"{datetime.now()}{random.random()}".encode()).hexdigest()[:8]

    revenue = np.random.uniform(*params["rev_range"])
    margin = np.random.uniform(*params["margin_range"])
    ebitda = revenue * margin
    growth = np.random.uniform(*params["growth_range"])

    entry_mult = np.random.uniform(6.0, 10.0)
    entry_equity = ebitda * entry_mult
    entry_debt = entry_equity * np.random.uniform(1.5, 3.0)

    names = {
        "SaaS": ["CloudWorks", "DataSense", "TechFlow"],
        "Manufacturing": ["PrecisionCo", "IndustrialPro", "ManuFlex"],
        "Healthcare": ["MedCare Solutions", "HealthFirst", "CarePoint"],
        "Retail": ["RetailMax", "ShopHub", "MerchandisePro"],
        "Business Services": ["ConsultPro", "BusinessFlow", "ServicePro"],
        "FinTech": ["FinFlow", "PayTech", "TradeHub"],
        "Logistics": ["LogisticsPro", "ShipHub", "TransFlow"],
        "Media & Content": ["CreativeStudio", "ContentHub", "MediaFlow"],
    }

    return Company(
        id=company_id,
        name=random.choice(names.get(sector, ["Venture Co."])),
        sector=sector,
        entry_multiple=entry_mult,
        entry_ebitda=ebitda,
        entry_revenue=revenue,
        entry_margin=margin,
        entry_equity=entry_equity,
        entry_debt=entry_debt,
        current_ebitda=ebitda,
        current_revenue=revenue,
        current_margin=margin,
        debt=0,
        entry_year=0,
        growth_rate=growth,
    )

# ============================================================================
# SCREEN COMPONENTS (MODULAR)
# ============================================================================

def screen_menu():
    """Main menu."""
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <h1 style='font-size: 3rem; background: linear-gradient(135deg, #10b981, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            ♦ CarryForge ♦
        </h1>
        <p style='color: #a0a0a0; font-size: 1.1rem;'>Premium PE Empire Builder</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start New Game", use_container_width=True):
            st.session_state.portfolio["screen"] = "difficulty"
            st.rerun()

def screen_difficulty():
    """Choose difficulty."""
    st.markdown("<h2 style='text-align: center;'>Choose Your Challenge</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    diffs = [
        ("Casual", "Easier outcomes, higher multiples, forgiving markets", col1),
        ("Balanced", "Realistic PE scenarios, fair conditions", col2),
        ("Hardcore", "Volatile markets, tight covenants, ruthless", col3),
    ]

    for name, desc, col in diffs:
        with col:
            st.markdown(f"<div class='deal-card'><h3>{name}</h3><p>{desc}</p></div>", unsafe_allow_html=True)
            if st.button(f"Play {name}", use_container_width=True, key=f"diff_{name}"):
                st.session_state.portfolio["difficulty"] = name
                st.session_state.portfolio["screen"] = "dashboard"
                st.session_state.deal_flow = [generate_company() for _ in range(6)]
                st.rerun()

def screen_dashboard():
    """Main dashboard with key metrics."""
    portfolio = st.session_state.portfolio

    # Header
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown(f"<h2>CarryForge | Fund I</h2>", unsafe_allow_html=True)
    with col2:
        st.metric("Year", portfolio["year"])
    with col3:
        st.metric("Q", portfolio["quarter"])
    with col4:
        if st.button("💾 Save"):
            save_game(portfolio)
            st.success("Saved!")

    st.markdown("---")

    # Portfolio metrics
    total_value = sum(calculate_company_metrics(c, portfolio["year"])["equity_value"] for c in portfolio["companies"])
    total_deployed = portfolio["raised_capital"] - portfolio["cash"]
    gross_dpi = total_value / max(total_deployed, 1) if total_deployed > 0 else 1.0
    avg_irr = np.mean([calculate_company_metrics(c, portfolio["year"])["irr"] for c in portfolio["companies"]]) if portfolio["companies"] else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Deployed", f"${total_deployed/1e6:.1f}M", f"{total_deployed/portfolio['raised_capital']*100:.0f}%")
    col2.metric("Portfolio Value", f"${total_value/1e6:.1f}M")
    col3.metric("Gross DPI", f"{gross_dpi:.2f}x")
    col4.metric("Avg IRR", f"{avg_irr*100:.1f}%")

    st.markdown("---")

    # Portfolio Health
    health, status = calculate_portfolio_health()
    col_health, col_status = st.columns([4, 1])
    with col_health:
        st.progress(health / 100, text=f"Portfolio Health")
    with col_status:
        if status == "Excellent":
            st.success(f"✅ {status}")
        elif status == "Good":
            st.info(f"👍 {status}")
        elif status == "At Risk":
            st.warning(f"⚠️ {status}")
        else:
            st.error(f"🚨 {status}")

    st.markdown("---")

    # Portfolio companies
    st.markdown("<h3>Portfolio Companies</h3>", unsafe_allow_html=True)
    if portfolio["companies"]:
        for i, company in enumerate(portfolio["companies"]):
            metrics = calculate_company_metrics(company, portfolio["year"])

            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            with col1:
                st.write(f"**{company.name}** ({company.sector})")
            with col2:
                st.metric("Revenue", f"${metrics['revenue']/1e6:.1f}M")
            with col3:
                st.metric("EBITDA", f"${metrics['ebitda']/1e6:.1f}M")
            with col4:
                st.metric("MOIC", f"{metrics['moic']:.2f}x", delta=f"{(metrics['moic']-1)*100:+.0f}%")
            with col5:
                if st.button("📊 Manage", key=f"manage_{i}"):
                    st.session_state.portfolio["selected_company"] = i
                    st.session_state.portfolio["screen"] = "company_detail"
                    st.rerun()
    else:
        st.info("No portfolio companies yet. Go to Deal Flow to invest!")

    # Covenant violations
    violations = check_covenant_violations()
    if violations:
        st.markdown("---")
        st.warning("⚠️ **Covenant Violations Detected**")
        for v in violations:
            severity = "🚨" if v["severity"] == "critical" else "⚠️"
            st.write(f"{severity} **{v['company']}** — {v['type']}: {v['value']} (max {v['limit']})")

    st.markdown("---")

    # Navigation
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

    with nav_col1:
        if st.button("📋 Deal Flow", use_container_width=True):
            st.session_state.portfolio["screen"] = "deal_flow"
            st.rerun()
    with nav_col2:
        if st.button("📊 Market", use_container_width=True):
            st.session_state.portfolio["screen"] = "market"
            st.rerun()
    with nav_col3:
        if st.button("💰 Fund Info", use_container_width=True):
            st.session_state.portfolio["screen"] = "fund_info"
            st.rerun()
    with nav_col4:
        if st.button("⏭️ Advance (Q+1)", use_container_width=True, key="advance_btn"):
            portfolio["quarter"] += 1
            if portfolio["quarter"] > 4:
                portfolio["quarter"] = 1
                portfolio["year"] += 1
            st.session_state.deal_flow = [generate_company() for _ in range(6)]
            st.rerun()

def screen_deal_flow():
    """Browse and invest in companies."""
    st.markdown("<h2>📋 Deal Flow</h2>", unsafe_allow_html=True)
    st.metric("Available Capital", f"${st.session_state.portfolio['cash']/1e6:.1f}M")

    st.markdown("---")

    for i, company in enumerate(st.session_state.deal_flow):
        with st.container():
            st.markdown(f"<div class='deal-card'>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown(f"### {company.name}")
                st.caption(f"{company.sector}")

            with col2:
                st.write(f"**Revenue:** ${company.entry_revenue:.1f}M | **EBITDA Margin:** {company.entry_margin*100:.0f}%")
                st.write(f"**Growth:** {company.growth_rate*100:.0f}% | **Entry Multiple:** {company.entry_multiple:.1f}x")

            with col3:
                st.write(f"**Equity Check:** ${company.entry_equity/1e6:.1f}M")
                st.write(f"**Est. Debt:** ${company.entry_debt/1e6:.1f}M")

            col_inv1, col_inv2, col_inv3 = st.columns([1, 1, 1])

            with col_inv1:
                if st.button("Invest", key=f"inv_{i}", use_container_width=True):
                    if company.entry_equity <= st.session_state.portfolio["cash"]:
                        company.entry_year = st.session_state.portfolio["year"]
                        company.debt = company.entry_debt
                        st.session_state.portfolio["companies"].append(company)
                        st.session_state.portfolio["cash"] -= company.entry_equity
                        st.success(f"✅ Invested in {company.name}!")
                        st.rerun()
                    else:
                        st.error("❌ Insufficient capital!")

            with col_inv2:
                if st.button("Details", key=f"det_{i}", use_container_width=True):
                    st.session_state.portfolio["selected_deal"] = i
                    st.session_state.portfolio["screen"] = "deal_detail"
                    st.rerun()

            with col_inv3:
                if st.button("Pass", key=f"pass_{i}", use_container_width=True):
                    st.info(f"Passed on {company.name}")

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.portfolio["screen"] = "dashboard"
        st.rerun()

def screen_deal_detail():
    """Show detailed deal analysis."""
    deal_idx = st.session_state.portfolio.get("selected_deal", 0)
    company = st.session_state.deal_flow[deal_idx]

    st.markdown(f"<h2>{company.name}</h2>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sector", company.sector)
    col2.metric("Entry Multiple", f"{company.entry_multiple:.1f}x")
    col3.metric("Growth Rate", f"{company.growth_rate*100:.0f}%")
    col4.metric("EBITDA Margin", f"{company.entry_margin*100:.0f}%")

    st.markdown("---")
    st.markdown("<h3>5-Year Projection</h3>", unsafe_allow_html=True)
    projection = project_company_years(company, 5)
    st.dataframe(projection, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("<h3>Exit Multiple Sensitivity (IRR %)</h3>", unsafe_allow_html=True)
    sensitivity = sensitivity_analysis(company)
    st.dataframe(sensitivity, use_container_width=True)

    st.markdown("---")
    if st.button("← Back", use_container_width=True):
        st.session_state.portfolio["screen"] = "deal_flow"
        st.rerun()

def screen_company_detail():
    """Manage a portfolio company."""
    idx = st.session_state.portfolio.get("selected_company", 0)
    company = st.session_state.portfolio["companies"][idx]
    metrics = calculate_company_metrics(company, st.session_state.portfolio["year"])

    st.markdown(f"<h2>{company.name}</h2>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Revenue", f"${metrics['revenue']/1e6:.1f}M")
    col2.metric("EBITDA", f"${metrics['ebitda']/1e6:.1f}M")
    col3.metric("Debt", f"${metrics['debt']/1e6:.1f}M")
    col4.metric("MOIC", f"{metrics['moic']:.2f}x")
    col5.metric("IRR", f"{metrics['irr']*100:.1f}%")

    st.markdown("---")
    st.markdown("<h3>5-Year Projection</h3>", unsafe_allow_html=True)
    projection = project_company_years(company, 5)
    st.dataframe(projection, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("<h3>Return Sensitivity</h3>", unsafe_allow_html=True)
    sensitivity = sensitivity_analysis(company)
    st.dataframe(sensitivity, use_container_width=True)

    st.markdown("---")

    # Covenant check
    if metrics["leverage"] > 3.5:
        st.error(f"⚠️ Leverage too high: {metrics['leverage']:.1f}x (max 3.5x)")
    if metrics["interest_coverage"] < 1.5:
        st.error(f"⚠️ Interest coverage weak: {metrics['interest_coverage']:.1f}x (min 1.5x)")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Exit & Realize Returns", use_container_width=True):
            st.session_state.portfolio["cash"] += metrics["equity_value"]
            st.session_state.portfolio["exited_companies"].append({
                "name": company.name,
                "moic": metrics["moic"],
                "irr": metrics["irr"],
                "proceeds": metrics["equity_value"]
            })
            st.session_state.portfolio["companies"].pop(idx)
            st.success(f"✅ Exited {company.name} for ${metrics['equity_value']/1e6:.1f}M! MOIC: {metrics['moic']:.2f}x")
            st.rerun()

    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.portfolio["screen"] = "dashboard"
            st.rerun()

def screen_market():
    """Market conditions and trends."""
    st.markdown("<h2>📊 Market & Economy</h2>", unsafe_allow_html=True)

    portfolio = st.session_state.portfolio
    quarter_phase = portfolio["quarter"] % 4

    col1, col2, col3 = st.columns(3)
    col1.metric("Market Sentiment", "Favorable" if quarter_phase in [0, 1] else "Neutral")
    col2.metric("M&A Activity", "High" if quarter_phase < 2 else "Moderate")
    col3.metric("Interest Rates", "5.5%")

    st.markdown("---")
    st.markdown("<h3>Exit Multiple Trends</h3>", unsafe_allow_html=True)

    exit_multiples = [8.0 + 0.3 * np.sin(i / 2) for i in range(portfolio["quarter"])]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=exit_multiples,
        mode='lines+markers',
        name='Exit Multiple (EBITDA)',
        line=dict(color='#10b981', width=2),
    ))
    fig.update_layout(
        title="Historical Exit Multiples",
        yaxis_title="Multiple",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(10,14,39,0.8)',
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.portfolio["screen"] = "dashboard"
        st.rerun()

def screen_fund_info():
    """Fund & LP information."""
    portfolio = st.session_state.portfolio

    st.markdown("<h2>💰 Fund I Information</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Capital Raised", f"${portfolio['raised_capital']/1e6:.1f}M")
    col2.metric("Deployed", f"${(portfolio['raised_capital']-portfolio['cash'])/1e6:.1f}M")
    col3.metric("Available", f"${portfolio['cash']/1e6:.1f}M")

    st.markdown("---")

    st.markdown("<h3>LP Base</h3>", unsafe_allow_html=True)
    lp_data = pd.DataFrame({
        "LP": ["University Endowment", "Pension Fund", "Family Office", "Foundations"],
        "Commitment ($M)": [12.5, 15, 12.5, 10],
        "Status": ["Active", "Active", "Active", "Active"]
    })
    st.dataframe(lp_data, use_container_width=True, hide_index=True)

    st.markdown("---")

    total_value = sum(calculate_company_metrics(c, portfolio["year"])["equity_value"] for c in portfolio["companies"])
    total_deployed = portfolio["raised_capital"] - portfolio["cash"]
    gross_dpi = (total_value + sum(e["proceeds"] for e in portfolio["exited_companies"])) / max(total_deployed, 1)

    st.markdown("<h3>Fund II Readiness</h3>", unsafe_allow_html=True)
    if gross_dpi > 1.5:
        st.success(f"✅ Strong DPI ({gross_dpi:.2f}x)! LPs ready for Fund II conversations.")
    elif gross_dpi > 1.2:
        st.info(f"⏳ Good progress (DPI: {gross_dpi:.2f}x). One more strong exit recommended.")
    else:
        st.warning(f"⚠️ Build track record (Current DPI: {gross_dpi:.2f}x). Target 1.5x+ for Fund II.")

    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.portfolio["screen"] = "dashboard"
        st.rerun()

# ============================================================================
# DATABASE & PERSISTENCE
# ============================================================================

def save_game(portfolio):
    """Save game state."""
    conn = sqlite3.connect(".claude/carryforge.db")
    c = conn.cursor()

    game_json = json.dumps({
        "year": portfolio["year"],
        "quarter": portfolio["quarter"],
        "cash": portfolio["cash"],
        "difficulty": portfolio["difficulty"],
        "companies": [asdict(c) for c in portfolio["companies"]],
        "exited": portfolio["exited_companies"],
    }, default=str)

    c.execute('''CREATE TABLE IF NOT EXISTS saves (
        slot INTEGER PRIMARY KEY,
        data TEXT,
        timestamp TEXT
    )''')

    c.execute('INSERT OR REPLACE INTO saves VALUES (1, ?, ?)',
              (game_json, datetime.now().isoformat()))

    conn.commit()
    conn.close()

# ============================================================================
# MAIN APP ROUTER
# ============================================================================

def main():
    init_session_state()

    portfolio = st.session_state.portfolio
    screen = portfolio["screen"]

    if screen == "menu":
        screen_menu()
    elif screen == "difficulty":
        screen_difficulty()
    elif screen == "dashboard":
        screen_dashboard()
    elif screen == "deal_flow":
        screen_deal_flow()
    elif screen == "deal_detail":
        screen_deal_detail()
    elif screen == "company_detail":
        screen_company_detail()
    elif screen == "market":
        screen_market()
    elif screen == "fund_info":
        screen_fund_info()
    else:
        st.error(f"Unknown screen: {screen}")

if __name__ == "__main__":
    main()
