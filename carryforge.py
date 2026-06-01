"""
CarryForge v7.0 — PE Empire with BitLife-style narrative
==========================================================
Complete redesign of the game feel.

What BitLife does that we're copying:
- Named characters with personality (CEOs, LPs, rivals)
- Choice events with REAL consequences (not just +5% modifiers)
- Narrative voice: specific, dark-ish humor, never generic
- Rival firms that compete, trash-talk, and create drama
- LP pressure that builds over time
- Company stories that feel personal
- Genuine surprise moments
- Bad things happen and really hurt

Removed: generic market banners, meaningless modifiers.
Added:   choice events, named characters, rivalry, LP drama, company crises.
"""

import streamlit as st
import numpy as np
import random
from dataclasses import dataclass, field
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="CarryForge", page_icon="💼",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  :root {
    --bg:#080d1e; --card:#111827; --card2:#1a2235;
    --green:#10b981; --gold:#f59e0b; --red:#ef4444;
    --blue:#3b82f6; --purple:#8b5cf6; --pink:#ec4899; --teal:#14b8a6;
    --border:rgba(255,255,255,0.08); --text:#f1f5f9; --muted:#64748b;
  }
  html,body,.stApp{background:var(--bg)!important;color:var(--text);}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding:1.25rem 1.25rem 4rem;max-width:1060px;margin:0 auto;}

  h1{font-size:1.85rem;font-weight:800;margin:0;color:var(--text);}
  h2{font-size:1.2rem;font-weight:700;margin:.9rem 0 .5rem;color:var(--text);}
  h3{font-size:1rem;font-weight:600;margin:0;color:var(--text);}

  .stButton>button{
    background:linear-gradient(135deg,var(--green),#059669);color:#fff!important;
    border:none!important;border-radius:10px;font-weight:700;font-size:.88rem;
    padding:.6rem 1rem;width:100%;transition:transform .15s,box-shadow .15s;
    box-shadow:0 4px 12px rgba(16,185,129,.22);
  }
  .stButton>button:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(16,185,129,.38);}
  .stButton>button:disabled{background:#1e293b!important;color:#475569!important;
    box-shadow:none!important;transform:none!important;}

  hr{border-color:var(--border);margin:.8rem 0;}

  /* stat */
  .stat{text-align:center;}
  .stat-val{font-size:1.3rem;font-weight:800;color:var(--text);line-height:1.2;}
  .stat-lbl{font-size:.65rem;font-weight:600;color:var(--muted);text-transform:uppercase;
             letter-spacing:.07em;margin-top:.15rem;}

  /* deal card */
  .dcard{background:var(--card);border:1px solid var(--border);
         border-left:3px solid transparent;border-radius:13px;
         padding:.85rem 1rem;margin-bottom:.45rem;}
  .dcard-SaaS{border-left-color:var(--blue);}
  .dcard-Hardware{border-left-color:var(--purple);}
  .dcard-Healthcare{border-left-color:var(--pink);}
  .dcard-Fintech{border-left-color:var(--teal);}

  .tag{display:inline-block;background:var(--card2);border:1px solid var(--border);
       border-radius:6px;padding:.18rem .48rem;font-size:.72rem;font-weight:600;
       color:var(--muted);margin:2px;}
  .tag span{color:var(--text);}

  /* narrative event card */
  .ev-card{background:var(--card);border:1px solid;border-radius:14px;
           padding:1.2rem 1.4rem;margin:.5rem 0;}
  .ev-crisis{border-color:#ef4444;background:rgba(239,68,68,.06);}
  .ev-opportunity{border-color:#10b981;background:rgba(16,185,129,.06);}
  .ev-rival{border-color:#8b5cf6;background:rgba(139,92,246,.06);}
  .ev-lp{border-color:#f59e0b;background:rgba(245,158,11,.06);}
  .ev-neutral{border-color:var(--border);}

  /* choice button — override green */
  .choice-btn button{
    background:var(--card2)!important;border:1px solid var(--border)!important;
    color:var(--text)!important;box-shadow:none!important;text-align:left!important;
  }
  .choice-btn button:hover{border-color:var(--green)!important;color:var(--green)!important;transform:none!important;}

  /* goal bar */
  .goal-track{background:var(--card2);border-radius:999px;height:8px;overflow:hidden;margin:.2rem 0;}
  .goal-fill{height:8px;border-radius:999px;
             background:linear-gradient(90deg,var(--green),#34d399);transition:width .5s;}

  /* score */
  .score-box{background:var(--card);border:1px solid var(--border);border-radius:18px;
             padding:2rem;text-align:center;max-width:500px;margin:1.5rem auto;}

  .c-green{color:var(--green)!important;font-weight:700;}
  .c-gold{color:var(--gold)!important;font-weight:700;}
  .c-red{color:var(--red)!important;font-weight:700;}
  .c-muted{color:var(--muted)!important;}
  .fw7{font-weight:700;}

  .lp-bar{height:6px;border-radius:999px;background:var(--card2);overflow:hidden;margin:.25rem 0;}
  .lp-fill{height:6px;border-radius:999px;background:linear-gradient(90deg,#f59e0b,#f97316);}

  @media(max-width:640px){
    .block-container{padding:.9rem .9rem 5rem;}
    .stat-val{font-size:1.05rem;}
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONTENT TABLES
# ─────────────────────────────────────────────

SECTORS = {
    "SaaS":      {"emoji":"💻","rev":(40,160),"margin":(.28,.48),"growth":(.12,.32)},
    "Hardware":  {"emoji":"🔧","rev":(90,300),"margin":(.08,.18),"growth":(.04,.14)},
    "Healthcare":{"emoji":"🏥","rev":(70,240),"margin":(.14,.28),"growth":(.08,.22)},
    "Fintech":   {"emoji":"💰","rev":(35,120),"margin":(.22,.42),"growth":(.22,.48)},
}

CEO_NAMES = [
    "Marcus Webb","Priya Sharma","Derek Lund","Sophie Chen","Raj Patel",
    "Chloe Kim","Jake Torres","Nadia Okafor","Ben Holt","Mei Lin",
    "Aaron Voss","Tara Flynn","Luis Reyes","Iris Park","Owen Grant",
    "Valentina Cruz","Sam Adeyemi","Petra Novak","Cal Morrison","Zoe Tanaka",
]

COMPANY_NAMES = {
    "SaaS":      ["CloudVault","DataFlow","SyncHub","AutoScale","SnapMetrics","PipelineAI","GridLogic","NovaDash"],
    "Hardware":  ["TechWorks","PrecisionCo","SmartBuild","CoreForge","IronStack","PeakSystems","NexHardware","OrbDrive"],
    "Healthcare":["HealthPlus","CareFlow","MedTech","PulseCare","BioServe","ClearMed","VitalPath","RxBridge"],
    "Fintech":   ["PayHub","TradeFlow","VaultSecure","ClearPay","LedgerX","SwiftBridge","CapitalOps","NovaMoney"],
}

RIVAL_FIRMS = [
    {"name":"Apex Capital","style":"aggressive","emoji":"🦅"},
    {"name":"Redwood PE","style":"conservative","emoji":"🌲"},
    {"name":"Meridian Partners","style":"sleazy","emoji":"🐍"},
    {"name":"Pinnacle Fund","style":"arrogant","emoji":"🏔"},
]

LP_NAMES = [
    {"name":"Westfield Endowment","type":"university","commitment":15e6},
    {"name":"CalPERS West","type":"pension","commitment":20e6},
    {"name":"Hartley Family Office","type":"family","commitment":10e6},
    {"name":"Atlas Foundation","type":"nonprofit","commitment":5e6},
]

# Vivid, specific, funny narrative events — triggered based on context
# type: crisis / opportunity / rival / lp / windfall
NARRATIVE_EVENTS = [
    # CEO drama
    {
        "id":"ceo_offer","type":"crisis","title":"Your CEO Got Poached",
        "icon":"😬",
        "template":"**{ceo}** — the CEO of {co} — just got a $2.4M offer from {rival}. "
                   "They called you from the parking lot of their kid's school to tell you.",
        "choices":[
            {"label":"Counter with a 2% equity stake","key":"equity","cost":0,"effect":"ceo_stays","desc":""},
            {"label":"Match their salary, nothing else","key":"salary","cost":0,"effect":"ceo_leaves_slow","desc":""},
            {"label":"Wish them luck and start interviewing","key":"wish","cost":0,"effect":"ceo_gone","desc":""},
        ]
    },
    {
        "id":"ceo_arrested","type":"crisis","title":"Legal Situation",
        "icon":"🚔",
        "template":"The CEO of {co}, **{ceo}**, was arrested this morning. "
                   "Unrelated to the business, apparently. SEC says otherwise.",
        "choices":[
            {"label":"Terminate immediately, full PR blackout","key":"fire","cost":0,"effect":"ceo_gone_clean","desc":""},
            {"label":"Hire a crisis lawyer, ride it out","key":"lawyer","cost":0,"effect":"crisis_managed","desc":""},
            {"label":"Publicly back them — they said they're innocent","key":"back","cost":0,"effect":"disaster","desc":""},
        ]
    },
    # Revenue / operations
    {
        "id":"major_customer","type":"opportunity","title":"Enterprise Deal",
        "icon":"🤝",
        "template":"{co} just got a letter of intent from **Fortune 50 company** — "
                   "a $12M ARR contract that would add ~30% to revenue overnight.",
        "choices":[
            {"label":"Staff up fast to deliver — hire 40 people","key":"staff","cost":0,"effect":"big_growth","desc":""},
            {"label":"Sign it, figure out delivery later","key":"sign","cost":0,"effect":"medium_growth","desc":""},
            {"label":"Pass — too much execution risk","key":"pass","cost":0,"effect":"nothing","desc":""},
        ]
    },
    {
        "id":"customer_churn","type":"crisis","title":"Client Just Walked",
        "icon":"💨",
        "template":"{co}'s **largest customer** — 18% of ARR — terminated their contract. "
                   "Their new CFO called your portfolio company 'a nice experiment that didn't work.'",
        "choices":[
            {"label":"Fly out immediately, offer a discount to stay","key":"fly","cost":0,"effect":"partial_save","desc":""},
            {"label":"Accept it and focus on new pipeline","key":"accept","cost":0,"effect":"slight_hit","desc":""},
            {"label":"Sue for breach of contract","key":"sue","cost":0,"effect":"war","desc":""},
        ]
    },
    # Rival drama
    {
        "id":"rival_bid","type":"rival","title":"Competing Bid",
        "icon":"😤",
        "template":"**{rival}** just submitted a competing bid for {co} — $8M over your offer. "
                   "Word is they're using leverage you'd never touch.",
        "choices":[
            {"label":"Walk away — you have discipline","key":"walk","cost":0,"effect":"lose_deal","desc":""},
            {"label":"Match their price, tighten terms elsewhere","key":"match","cost":0,"effect":"win_expensive","desc":""},
            {"label":"Go $2M lower and pitch your operational value","key":"pitch","cost":0,"effect":"win_clever","desc":""},
        ]
    },
    {
        "id":"rival_email","type":"rival","title":"Interesting Email",
        "icon":"📧",
        "template":"You receive an email from **{rival_name}** at {rival}: "
                   "*'Heard you picked up {co}. Brave choice given the cap table mess. "
                   "Let us know when you're ready to recap at a fair price.'*",
        "choices":[
            {"label":"Reply with a screenshot of your DPI","key":"flex","cost":0,"effect":"rivalry_up","desc":""},
            {"label":"Ignore it — they're trying to get in your head","key":"ignore","cost":0,"effect":"nothing","desc":""},
            {"label":"Forward it to your LP — let them laugh too","key":"forward","cost":0,"effect":"lp_amused","desc":""},
        ]
    },
    # LP pressure
    {
        "id":"lp_call","type":"lp","title":"LP on Line 1",
        "icon":"📞",
        "template":"**{lp}** is calling. Again. They want to know why DPI is still at 0x "
                   "and whether you've 'considered your exit timeline.' "
                   "The call is in 15 minutes.",
        "choices":[
            {"label":"Take the call, promise Q3 exit for one company","key":"promise","cost":0,"effect":"pressure_sell","desc":""},
            {"label":"Send an update deck with 'pipeline is strong'","key":"deck","cost":0,"effect":"bought_time","desc":""},
            {"label":"Have your associate take the call","key":"dodge","cost":0,"effect":"lp_annoyed","desc":""},
        ]
    },
    {
        "id":"lp_pullout","type":"lp","title":"LP Threatening to Withdraw",
        "icon":"🚨",
        "template":"**{lp}** says they need liquidity. They're threatening to sell their LP stake "
                   "at a 30% discount unless you can offer a partial return.",
        "choices":[
            {"label":"Orchestrate a small dividend recap on one company","key":"recap","cost":0,"effect":"lp_happy_hit","desc":""},
            {"label":"Help them find a secondary buyer","key":"secondary","cost":0,"effect":"lp_exits","desc":""},
            {"label":"Call their bluff — they won't actually sell","key":"bluff","cost":0,"effect":"lp_furious","desc":""},
        ]
    },
    # Windfall
    {
        "id":"unsolicited_bid","type":"opportunity","title":"Someone Wants to Buy",
        "icon":"💸",
        "template":"A **strategic buyer** just made an unsolicited offer for {co} at "
                   "a 35% premium to your last valuation. Their banker called your banker "
                   "on a Tuesday at 7am. They want an answer by Friday.",
        "choices":[
            {"label":"Sell now — take the money","key":"sell","cost":0,"effect":"forced_exit","desc":""},
            {"label":"Run a full process, see if others bid","key":"process","cost":0,"effect":"auction","desc":""},
            {"label":"Decline — you're just getting started","key":"decline","cost":0,"effect":"nothing","desc":""},
        ]
    },
    {
        "id":"ipo_buzz","type":"opportunity","title":"Bankers Are Calling",
        "icon":"🏦",
        "template":"Goldman and Morgan Stanley are both calling about an IPO for {co}. "
                   "The analyst said 'you're exactly what the market wants right now.' "
                   "That's either true or a sales pitch.",
        "choices":[
            {"label":"Explore it — set up a bake-off","key":"explore","cost":0,"effect":"ipo_prep","desc":""},
            {"label":"Too early — wait another year","key":"wait","cost":0,"effect":"nothing","desc":""},
            {"label":"Take their lunch but say no","key":"lunch","cost":0,"effect":"nothing","desc":""},
        ]
    },
    # Market
    {
        "id":"rate_shock","type":"crisis","title":"Rate Shock",
        "icon":"📉",
        "template":"The Fed just raised rates **75bps**. Your debt cost just went up $2M annually across the portfolio. "
                   "Blackstone sent an email titled 'Navigating the New Normal.' You deleted it.",
        "choices":[
            {"label":"Refinance early on best company — lock in rates","key":"refi","cost":0,"effect":"rate_hedged","desc":""},
            {"label":"Accelerate exits before credit tightens","key":"exit_fast","cost":0,"effect":"pressure_sell","desc":""},
            {"label":"Weather it — rates won't stay high forever","key":"weather","cost":0,"effect":"slight_hit","desc":""},
        ]
    },
    {
        "id":"market_crash","type":"crisis","title":"Rough Week",
        "icon":"🔴",
        "template":"S&P is down 18% this month. Your LPs are all losing money elsewhere. "
                   "Your board deck's first slide just got changed from 'Record Momentum' to 'Resilience.'",
        "choices":[
            {"label":"Double down — buy the dip if possible","key":"buy","cost":0,"effect":"contrarian_win","desc":""},
            {"label":"Go defensive — stop new investments","key":"defensive","cost":0,"effect":"protected","desc":""},
            {"label":"Start working on that exit you've been delaying","key":"exit_now","cost":0,"effect":"pressure_sell","desc":""},
        ]
    },
    {
        "id":"sector_boom","type":"opportunity","title":"Your Sector is Hot",
        "icon":"🔥",
        "template":"**{co}'s sector** just got featured on the cover of Fortune. "
                   "Every growth equity fund in NYC is now looking at your deal. "
                   "Exit multiples in the sector are up 2x from a year ago.",
        "choices":[
            {"label":"Exit now while multiples are peak","key":"exit_peak","cost":0,"effect":"forced_exit","desc":""},
            {"label":"Hold for the wave — more to come","key":"hold","cost":0,"effect":"risky_hold","desc":""},
            {"label":"Use the hype to recruit a tier-1 CEO","key":"recruit","cost":0,"effect":"ceo_upgrade","desc":""},
        ]
    },
    {
        "id":"management_fight","type":"crisis","title":"Board Meeting Gone Wrong",
        "icon":"🥊",
        "template":"Your last board meeting for {co} ended with **{ceo}** and your operating partner "
                   "not speaking to each other. The CFO texted you afterward: 'That was not great.'",
        "choices":[
            {"label":"Back the CEO — they're right","key":"back_ceo","cost":0,"effect":"mgmt_stable","desc":""},
            {"label":"Back the OP — shake up management","key":"back_op","cost":0,"effect":"ceo_gone","desc":""},
            {"label":"Mediator call this week, forced alignment","key":"mediate","cost":0,"effect":"slow_resolution","desc":""},
        ]
    },
    {
        "id":"add_on","type":"opportunity","title":"Bolt-On Opportunity",
        "icon":"🧩",
        "template":"{co} found a **smaller competitor** willing to sell for $8M. "
                   "Tuck-in would add 15% revenue and a decent customer list. "
                   "CEO is excited. You've seen this movie before.",
        "choices":[
            {"label":"Fund it — bolt-ons create value","key":"fund","cost":0,"effect":"addon_win","desc":""},
            {"label":"Pass — keep management focused","key":"pass","cost":0,"effect":"nothing","desc":""},
            {"label":"Tell them to come back with a lower price","key":"negotiate","cost":0,"effect":"addon_maybe","desc":""},
        ]
    },
]

# Effect definitions: what each choice key does to the company/game
EFFECTS = {
    "ceo_stays":         {"moic_delta": +0.20, "msg": "CEO stayed. Wrote them a heartfelt note. Equity vesting updated."},
    "ceo_leaves_slow":   {"moic_delta": -0.10, "msg": "They took the other offer. At least you have 90 days to find someone."},
    "ceo_gone":          {"moic_delta": -0.25, "msg": "CEO is out. The team is nervous. Search firm on retainer."},
    "ceo_gone_clean":    {"moic_delta": -0.20, "msg": "Terminated. Business is wobbling but the legal risk is contained."},
    "crisis_managed":    {"moic_delta": -0.10, "msg": "Lawyer got charges reduced. Stock-based optics are now your problem."},
    "disaster":          {"moic_delta": -0.40, "msg": "The SEC subpoenas arrived Friday afternoon. Press release drafted."},
    "big_growth":        {"moic_delta": +0.30, "msg": "Bold bet paid off. Revenue up 28% next quarter. CEO is insufferable about it."},
    "medium_growth":     {"moic_delta": +0.15, "msg": "Bumpy delivery but the contract held. Client renewed last minute."},
    "nothing":           {"moic_delta":  0.00, "msg": "Status quo. The quarterly deck looks exactly the same as last quarter."},
    "partial_save":      {"moic_delta": -0.08, "msg": "Negotiated a 12-month extension. They're still going to leave."},
    "slight_hit":        {"moic_delta": -0.12, "msg": "Revenue down 18% this quarter. Pipeline is 'robust' apparently."},
    "war":               {"moic_delta": -0.30, "msg": "Litigation is expensive. Distraction is worse. Everyone is losing."},
    "lose_deal":         {"moic_delta":  0.00, "msg": "Deal lost. You walk out of the GP meeting saying 'discipline.'"},
    "win_expensive":     {"moic_delta": -0.05, "msg": "Won the deal but paid over market. Your model needs a hero exit."},
    "win_clever":        {"moic_delta": +0.08, "msg": "Seller picked you over the higher bid. Your reputation is good for something."},
    "rivalry_up":        {"moic_delta":  0.00, "msg": "They didn't reply. Probably furious."},
    "lp_amused":         {"lp_delta":  +5,     "msg": "LP laughed. Said quote 'these guys.' Good relationship."},
    "pressure_sell":     {"force_exit": True,  "msg": "You committed to an exit. Now you have to deliver one."},
    "bought_time":       {"lp_delta":  -3,     "msg": "They accepted the deck but called again 3 weeks later."},
    "lp_annoyed":        {"lp_delta": -10,     "msg": "Associate told them 'he's in a deal.' LP is 63 years old and has been in PE since before you were born."},
    "lp_happy_hit":      {"moic_delta": -0.05, "lp_delta": +10, "msg": "LP is placated. Your company took a small leverage hit."},
    "lp_exits":          {"lp_delta": -20,     "msg": "LP sold their stake at a 35% discount. New holder is a hedge fund that emails weekly."},
    "lp_furious":        {"lp_delta": -25,     "msg": "They called the bluff. You now have to personally call every LP on a Friday night."},
    "forced_exit":       {"force_exit": True,  "msg": "Company is going to market. You're about to find out what your IRR actually is."},
    "auction":           {"moic_delta": +0.12, "msg": "Four bidders showed up. You extracted another 18% on the price."},
    "ipo_prep":          {"moic_delta": +0.08, "msg": "12-month IPO process begins. Dress rehearsal with analysts next quarter."},
    "rate_hedged":       {"moic_delta": +0.05, "msg": "Locked in 6.2% for 5 years. Feels smart in 3 months."},
    "contrarian_win":    {"moic_delta": +0.18, "msg": "Bought the dip. Looks genius in hindsight. Was terrifying at the time."},
    "protected":         {"moic_delta": +0.03, "msg": "Portfolio stable. New deal paused. Capital preserved."},
    "risky_hold":        {"moic_delta": +0.10, "msg": "The wave didn't come. Multiple contracted 15%. You're still holding."},
    "ceo_upgrade":       {"moic_delta": +0.15, "msg": "Hired ex-Stripe COO. First week: restructured the entire sales team."},
    "mgmt_stable":       {"moic_delta": +0.05, "msg": "Operating partner is annoyed but professional. Board meetings are quieter."},
    "slow_resolution":   {"moic_delta": -0.05, "msg": "Mediation took 6 weeks. Everyone is technically aligned."},
    "addon_win":         {"moic_delta": +0.15, "msg": "Tuck-in closed. Customer cross-sell is already working."},
    "addon_maybe":       {"moic_delta": +0.05, "msg": "They came back 20% lower. You counter-signed the same afternoon."},
}

DIFFICULTY = {
    "Easy":    {"cash":60e6,"exit_mult":9.5,"goal":1.25,"quarters":12,"lp_patience":80},
    "Balanced":{"cash":50e6,"exit_mult":8.5,"goal":1.40,"quarters":12,"lp_patience":65},
    "Hard":    {"cash":40e6,"exit_mult":7.5,"goal":1.60,"quarters":12,"lp_patience":45},
}

MAX_PORTFOLIO = 4

# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class Company:
    id: str
    name: str
    sector: str
    ceo: str
    revenue: float
    ebitda: float
    margin: float
    growth: float
    entry_multiple: float
    entry_ev: float
    entry_debt: float
    entry_equity: float
    entry_quarter: int = 0
    debt: float = 0.0
    moic_modifier: float = 1.0   # additive MOIC penalty/bonus from events

@dataclass
class GameState:
    screen: str = "start"
    difficulty: str = "Balanced"
    quarter_num: int = 0
    cash: float = 50e6
    firm_name: str = ""
    partner_name: str = ""
    companies: list = field(default_factory=list)
    exited: list = field(default_factory=list)
    deals: list = field(default_factory=list)
    pending_event: dict = field(default_factory=dict)
    event_log: list = field(default_factory=list)  # last few outcomes
    lp_satisfaction: int = 70    # 0–100
    rival: dict = field(default_factory=dict)
    exit_mult_mod: float = 1.0
    growth_mod: float = 1.0
    sector_mods: dict = field(default_factory=dict)
    forced_exit_company_id: str = ""

    @property
    def year(self): return 2024 + self.quarter_num // 4
    @property
    def quarter(self): return (self.quarter_num % 4) + 1
    @property
    def total_quarters(self): return DIFFICULTY[self.difficulty]["quarters"]

# ─────────────────────────────────────────────
# GAME LOGIC
# ─────────────────────────────────────────────

def make_deals(gs: GameState, n: int = 5) -> list:
    deals = []
    used_names: set = {c.name for c in gs.companies}
    for _ in range(n):
        sector = random.choice(list(SECTORS))
        p = SECTORS[sector]
        rev    = np.random.uniform(*p["rev"])
        margin = np.random.uniform(*p["margin"])
        ebitda = rev * margin
        growth = np.random.uniform(*p["growth"])
        em     = round(np.random.uniform(6.5, 9.5), 1)
        ev     = ebitda * em
        debt   = ebitda * np.random.uniform(3.0, 5.0)
        eq     = max(ev - debt, ev * 0.10)
        name   = random.choice(COMPANY_NAMES[sector])
        ceo    = random.choice(CEO_NAMES)
        deals.append(Company(
            id=f"{name[:3]}{random.randint(100,999)}",
            name=name, sector=sector, ceo=ceo,
            revenue=rev, ebitda=ebitda, margin=margin, growth=growth,
            entry_multiple=em, entry_ev=ev, entry_debt=debt,
            entry_equity=eq, entry_quarter=gs.quarter_num, debt=debt,
        ))
    return deals

def calc(c: Company, gs: GameState) -> dict:
    qh = gs.quarter_num - c.entry_quarter
    yh = qh / 4.0
    sm = gs.sector_mods.get(c.sector, 1.0)
    mature_yrs = max(qh - 8, 0) / 4.0
    eg = c.growth * gs.growth_mod * sm * ((1 - 0.08) ** mature_yrs)

    debt = c.entry_debt
    for yr in range(1, int(yh) + 1):
        my = max((yr * 4 - 8) / 4, 0)
        y_eg = c.growth * gs.growth_mod * sm * ((1 - 0.08) ** my)
        yr_e = c.revenue * ((1 + y_eg) ** yr) * c.margin
        debt = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)

    rev    = c.revenue * ((1 + eg) ** yh)
    ebitda = rev * c.margin

    if yh < 1.0: pm = 0.88 + yh * 0.12
    elif yh <= 3.0: pm = 1.0 + (yh - 1.0) * 0.05
    else: pm = 1.10 - (yh - 3.0) * 0.05

    cfg    = DIFFICULTY[gs.difficulty]
    em     = cfg["exit_mult"] * gs.exit_mult_mod * sm * pm
    equity = max(ebitda * em - debt, 0)
    moic   = (equity / max(c.entry_equity, 1)) * max(c.moic_modifier, 0.1)
    irr    = (moic ** (1 / max(yh, 0.25)) - 1) if yh > 0 else 0
    return {"revenue": rev, "ebitda": ebitda, "equity": equity,
            "moic": moic, "irr": irr, "yh": yh, "peak_mod": pm}

def blended_moic(gs: GameState) -> float:
    ti = sum(c.entry_equity for c in gs.companies) + sum(e["entry_eq"] for e in gs.exited)
    to = sum(calc(c, gs)["equity"] for c in gs.companies) * 0.70 + sum(e["proceeds"] for e in gs.exited)
    return to / max(ti, 1)

def proj_moic_3yr(d: Company, gs: GameState) -> float:
    rev3   = d.revenue * ((1 + d.growth) ** 3)
    ebitda = rev3 * d.margin
    debt   = d.entry_debt
    for yr in range(1, 4):
        yr_e = d.revenue * ((1 + d.growth) ** yr) * d.margin
        debt = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)
    em  = DIFFICULTY[gs.difficulty]["exit_mult"] * 1.10
    eq  = max(ebitda * em - debt, 0)
    return eq / max(d.entry_equity, 1)

def sell_company(gs: GameState, idx: int):
    c = gs.companies[idx]
    m = calc(c, gs)
    gs.cash += m["equity"]
    gs.exited.append({
        "name": c.name, "sector": c.sector, "ceo": c.ceo,
        "moic": m["moic"], "irr": m["irr"],
        "proceeds": m["equity"], "entry_eq": c.entry_equity,
        "yh": m["yh"],
    })
    gs.companies.pop(idx)

def pick_narrative_event(gs: GameState) -> dict | None:
    """Pick a contextually appropriate event."""
    pool = []

    # Events that need a portfolio company
    if gs.companies:
        pool += [e for e in NARRATIVE_EVENTS if e["type"] in ("crisis","opportunity")]
        pool += [e for e in NARRATIVE_EVENTS if e["type"] == "rival"]
        # LP events when DPI is low
        if not gs.exited and gs.quarter_num > 4:
            pool += [e for e in NARRATIVE_EVENTS if e["type"] == "lp"] * 3   # weight up LP drama

    if not pool:
        return None
    ev = random.choice(pool)
    co = random.choice(gs.companies) if gs.companies else None
    rival = gs.rival

    # Fill template
    text = ev["template"]
    if co:
        text = text.replace("{co}", f"**{co.name}**")
        text = text.replace("{ceo}", co.ceo)
    text = text.replace("{rival}", rival.get("name","a rival firm"))
    text = text.replace("{rival_name}", random.choice(["Tyler Marsh","Carter Wells","Blake Nguyen","Alexis Brandt"]))
    text = text.replace("{lp}", random.choice([lp["name"] for lp in LP_NAMES]))

    return {
        "id": ev["id"],
        "type": ev["type"],
        "title": ev["title"],
        "icon": ev["icon"],
        "text": text,
        "choices": ev["choices"],
        "company_id": co.id if co else None,
    }

def apply_effect(gs: GameState, effect_key: str, company_id: str | None):
    eff = EFFECTS.get(effect_key, EFFECTS["nothing"])

    # Apply to company
    if company_id:
        for c in gs.companies:
            if c.id == company_id:
                if "moic_delta" in eff:
                    c.moic_modifier += eff["moic_delta"]
                    c.moic_modifier = max(0.1, min(c.moic_modifier, 3.0))
                if eff.get("force_exit"):
                    gs.forced_exit_company_id = c.id
                break

    # Apply LP delta
    if "lp_delta" in eff:
        gs.lp_satisfaction = max(0, min(100, gs.lp_satisfaction + eff["lp_delta"]))

    # Log outcome
    gs.event_log.insert(0, eff["msg"])
    gs.event_log = gs.event_log[:4]   # keep last 4

def advance_quarter(gs: GameState):
    gs.quarter_num += 1

    # Natural LP decay if no exits
    if not gs.exited and gs.quarter_num > 3:
        gs.lp_satisfaction = max(0, gs.lp_satisfaction - 3)

    # Refresh deals
    gs.deals = make_deals(gs, 5)

    # Check end
    if gs.quarter_num >= gs.total_quarters:
        gs.screen = "score"
        return

    # Roll for narrative event (~60% chance)
    if random.random() < 0.60 and gs.companies:
        ev = pick_narrative_event(gs)
        if ev:
            gs.pending_event = ev

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

def mc(v): return "c-green" if v >= 2.0 else "c-gold" if v >= 1.3 else "c-red"
def cf(v): return f"${v/1e9:.2f}B" if abs(v) >= 1e9 else f"${v/1e6:.1f}M"
def lp_color(s): return "#10b981" if s >= 60 else "#f59e0b" if s >= 35 else "#ef4444"

# ─────────────────────────────────────────────
# SCREEN: START
# ─────────────────────────────────────────────

def screen_start():
    st.markdown("""
    <div style="text-align:center;padding:2.5rem 0 1.5rem;">
      <div style="font-size:52px;margin-bottom:.75rem;">💼</div>
      <h1 style="font-size:2.8rem;background:linear-gradient(135deg,#10b981,#f59e0b);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;">
        CarryForge
      </h1>
      <p style="font-size:1rem;color:#64748b;margin:.5rem 0 1.5rem;">
        Build a PE empire. Handle the drama. Get your LPs paid.
      </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("setup_form"):
        c1, c2 = st.columns(2)
        with c1:
            firm = st.text_input("Firm name", placeholder="e.g. Meridian Capital")
        with c2:
            partner = st.text_input("Your name", placeholder="e.g. Alex Chen")

        st.markdown("<br>", unsafe_allow_html=True)
        d1, d2, d3 = st.columns(3)
        diff = st.radio("Difficulty", ["Easy","Balanced","Hard"],
                        horizontal=True, index=1,
                        captions=["$60M · Goal 1.25×","$50M · Goal 1.40×","$40M · Goal 1.60×"])

        submitted = st.form_submit_button("Start Game →", use_container_width=True)
        if submitted:
            gs = GameState(
                screen="game",
                difficulty=diff,
                cash=DIFFICULTY[diff]["cash"],
                lp_satisfaction=DIFFICULTY[diff]["lp_patience"],
                firm_name=firm.strip() or "Genesis Capital",
                partner_name=partner.strip() or "Alex",
                rival=random.choice(RIVAL_FIRMS),
            )
            gs.deals = make_deals(gs, 5)
            st.session_state.gs = gs
            st.rerun()

# ─────────────────────────────────────────────
# SCREEN: EVENT (BitLife-style choice card)
# ─────────────────────────────────────────────

def screen_event():
    gs = G()
    ev = gs.pending_event
    type_css = {
        "crisis":"ev-crisis", "opportunity":"ev-opportunity",
        "rival":"ev-rival", "lp":"ev-lp",
    }.get(ev.get("type","neutral"), "ev-neutral")

    st.markdown(f"""
    <div class="ev-card {type_css}">
      <div style="font-size:2rem;margin-bottom:.5rem;">{ev.get('icon','📋')}</div>
      <h2 style="margin:0 0 .75rem;">{ev.get('title','Event')}</h2>
      <p style="font-size:.95rem;color:var(--text);line-height:1.6;">{ev.get('text','')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**What do you do?**")

    choices = ev.get("choices", [])
    cols = st.columns(len(choices))
    for i, ch in enumerate(choices):
        with cols[i]:
            st.markdown('<div class="choice-btn">', unsafe_allow_html=True)
            if st.button(ch["label"], key=f"ch_{i}", use_container_width=True):
                apply_effect(gs, ch["effect"], ev.get("company_id"))
                gs.pending_event = {}
                # If a forced exit was set, do it
                if gs.forced_exit_company_id:
                    idx = next((i for i, c in enumerate(gs.companies)
                                if c.id == gs.forced_exit_company_id), None)
                    if idx is not None:
                        sell_company(gs, idx)
                    gs.forced_exit_company_id = ""
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Show outcome hint (last event result if any)
    if gs.event_log and len(gs.event_log) > 1:
        st.markdown(f"""
        <div style="margin-top:1.25rem;padding:.6rem 1rem;background:var(--card2);
             border-radius:10px;font-size:.83rem;color:var(--muted);">
          <strong>Last quarter:</strong> {gs.event_log[1]}
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCREEN: GAME
# ─────────────────────────────────────────────

def screen_game():
    gs = G()

    # If there's a pending event, show that first
    if gs.pending_event:
        screen_event()
        return

    cfg = DIFFICULTY[gs.difficulty]

    # ── Header ──────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 1.2, 1.6])
    with c1:
        firm_display = gs.firm_name or "CarryForge"
        st.markdown(f"<h1>{firm_display}</h1>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat"><div class="stat-val">{cf(gs.cash)}</div>
          <div class="stat-lbl">Cash</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat"><div class="stat-val">{gs.year} Q{gs.quarter}</div>
          <div class="stat-lbl">Period</div></div>""", unsafe_allow_html=True)
    with c4:
        bm = blended_moic(gs)
        st.markdown(f"""<div class="stat">
          <div class="stat-val {mc(bm)}">{bm:.2f}×</div>
          <div class="stat-lbl">Portfolio</div></div>""", unsafe_allow_html=True)
    with c5:
        if st.button("⏭  Next Quarter", use_container_width=True, key="nq"):
            advance_quarter(gs)
            st.rerun()

    # ── Goal + LP bar ────────────────────────────────────────
    goal      = cfg["goal"]
    qtrs_left = gs.total_quarters - gs.quarter_num
    goal_pct  = min(bm / goal, 1.0)
    lp_c      = lp_color(gs.lp_satisfaction)

    st.markdown(f"""
    <div style="margin:.15rem 0 .85rem;">
      <div style="display:flex;justify-content:space-between;font-size:.74rem;
           color:var(--muted);margin-bottom:.2rem;">
        <span>Goal <strong style="color:var(--text)">{goal}×</strong></span>
        <span>{qtrs_left} qtrs left</span>
      </div>
      <div class="goal-track"><div class="goal-fill" style="width:{int(goal_pct*100)}%"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;
           color:var(--muted);margin-top:.45rem;margin-bottom:.15rem;">
        <span>LP Satisfaction</span>
        <span style="color:{lp_c};font-weight:700;">{gs.lp_satisfaction}/100</span>
      </div>
      <div class="lp-bar">
        <div class="lp-fill" style="width:{gs.lp_satisfaction}%;background:{lp_c};"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # LP crisis warning
    if gs.lp_satisfaction < 35:
        st.error("🚨 LPs are threatening to pull out. Exit a company or this gets ugly.")
    elif gs.lp_satisfaction < 55:
        st.warning("⚠️ LPs are getting impatient. They want to see distributions.")

    # Recent outcome log
    if gs.event_log:
        st.markdown(f"""
        <div style="padding:.55rem .9rem;background:var(--card2);border-radius:10px;
             font-size:.82rem;color:var(--muted);margin-bottom:.6rem;">
          <strong style="color:var(--text);">Last quarter:</strong> {gs.event_log[0]}
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Portfolio ────────────────────────────────────────────
    if gs.companies:
        st.markdown(f"<h2>📊 Portfolio ({len(gs.companies)}/{MAX_PORTFOLIO})</h2>",
                    unsafe_allow_html=True)
        if len(gs.companies) >= MAX_PORTFOLIO:
            st.markdown('<div style="font-size:.8rem;color:var(--red);margin-bottom:.4rem;">🔴 Portfolio full — sell before buying new deals</div>', unsafe_allow_html=True)

        sell_idx = None
        for i, c in enumerate(gs.companies):
            m   = calc(c, gs)
            sec = SECTORS[c.sector]
            yh  = m["yh"]
            age = f"{yh:.1f}y" if yh >= 1 else f"{int(round(yh * 4))}q"
            pm  = m["peak_mod"]
            win = "🟢" if pm >= 1.08 else ("🟡" if pm >= 0.98 else "🔴")
            mod_hint = ""
            if c.moic_modifier < 0.85:
                mod_hint = f' <span style="color:var(--red);font-size:.73rem;">⚠ damaged</span>'
            elif c.moic_modifier > 1.15:
                mod_hint = f' <span style="color:var(--green);font-size:.73rem;">✨ boosted</span>'

            ca, cb, cc, cd, ce = st.columns([3, 1.1, 1.1, 1.1, .9])
            with ca:
                st.markdown(f"""<div class="dcard dcard-{c.sector}">
                  <span class="fw7">{sec['emoji']} {c.name}</span>
                  <span class="c-muted" style="font-size:.74rem;margin-left:.3rem;">
                    CEO: {c.ceo} · {age} · {win}</span>{mod_hint}
                </div>""", unsafe_allow_html=True)
            with cb:
                st.markdown(f"""<div class="stat"><div class="stat-val">{cf(m['revenue'])}</div>
                  <div class="stat-lbl">Revenue</div></div>""", unsafe_allow_html=True)
            with cc:
                st.markdown(f"""<div class="stat">
                  <div class="stat-val {mc(m['moic'])}">{m['moic']:.2f}×</div>
                  <div class="stat-lbl">MOIC</div></div>""", unsafe_allow_html=True)
            with cd:
                st.markdown(f"""<div class="stat"><div class="stat-val">{m['irr']*100:.0f}%</div>
                  <div class="stat-lbl">IRR</div></div>""", unsafe_allow_html=True)
            with ce:
                if st.button("Sell", key=f"sell_{i}_{gs.quarter_num}", use_container_width=True):
                    sell_idx = i

        if sell_idx is not None:
            c = gs.companies[sell_idx]
            m = calc(c, gs)
            sell_company(gs, sell_idx)
            emoji = "🏆" if m["moic"] >= 2.0 else "✅" if m["moic"] >= 1.4 else "📉"
            gs.lp_satisfaction = min(100, gs.lp_satisfaction + 8)  # LPs love exits
            gs.event_log.insert(0, f"Exited {c.name} at {m['moic']:.2f}× — LPs satisfied.")
            gs.event_log = gs.event_log[:4]
            st.success(f"{emoji} Exited **{c.name}** — {m['moic']:.2f}× · {cf(m['equity'])} proceeds")
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Deal Flow ─────────────────────────────────────────────
    full = len(gs.companies) >= MAX_PORTFOLIO
    st.markdown("<h2>🎯 Deal Flow</h2>", unsafe_allow_html=True)

    buy_idx = None
    for i, d in enumerate(gs.deals):
        sec  = SECTORS[d.sector]
        pm3  = proj_moic_3yr(d, gs)
        can  = d.entry_equity <= gs.cash and not full

        ca, cb, cc, cd, ce = st.columns([3, 1.1, 1.1, 1.1, .9])
        with ca:
            st.markdown(f"""<div class="dcard dcard-{d.sector}">
              <h3>{sec['emoji']} {d.name}</h3>
              <span class="c-muted" style="font-size:.74rem;">CEO: {d.ceo}</span><br>
              <span class="tag">{d.sector}</span>
              <span class="tag">In: <span>{d.entry_multiple:.1f}×</span></span>
              <span class="tag">Growth: <span>{d.growth*100:.0f}%</span></span>
              <span class="tag">Margin: <span>{d.margin*100:.0f}%</span></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""<div class="stat"><div class="stat-val">{cf(d.entry_equity)}</div>
              <div class="stat-lbl">Equity</div></div>""", unsafe_allow_html=True)
        with cc:
            st.markdown(f"""<div class="stat"><div class="stat-val">{cf(d.entry_debt)}</div>
              <div class="stat-lbl">Debt</div></div>""", unsafe_allow_html=True)
        with cd:
            st.markdown(f"""<div class="stat">
              <div class="stat-val {mc(pm3)}">{pm3:.1f}×</div>
              <div class="stat-lbl">3yr Est.</div></div>""", unsafe_allow_html=True)
        with ce:
            lbl = "Buy" if can else ("Full" if full else "💸")
            if st.button(lbl, key=f"buy_{i}_{gs.quarter_num}",
                         use_container_width=True, disabled=not can):
                buy_idx = i

    if buy_idx is not None:
        d = gs.deals[buy_idx]
        gs.cash -= d.entry_equity
        d.entry_quarter = gs.quarter_num
        gs.companies.append(d)
        gs.deals.pop(buy_idx)
        gs.event_log.insert(0, f"Closed {d.name}. {d.ceo} is 'excited about the partnership.'")
        gs.event_log = gs.event_log[:4]
        st.rerun()

    # ── Exits log ────────────────────────────────────────────
    if gs.exited:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2>🏆 Realized Exits</h2>", unsafe_allow_html=True)
        for e in reversed(gs.exited[-5:]):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.5rem .85rem;background:var(--card);border-radius:10px;margin-bottom:.3rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong>
                <span class="c-muted" style="font-size:.75rem;"> — {e['yh']:.1f}yr hold</span></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proceeds'])}</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCREEN: SCORE
# ─────────────────────────────────────────────

def screen_score():
    gs  = G()
    cfg = DIFFICULTY[gs.difficulty]
    bm  = blended_moic(gs)
    goal = cfg["goal"]

    if bm >= goal * 1.30: grade, gc = "S", "#f59e0b"
    elif bm >= goal:       grade, gc = "A", "#10b981"
    elif bm >= goal * .82: grade, gc = "B", "#3b82f6"
    else:                  grade, gc = "C", "#ef4444"

    realized = sum(e["proceeds"] for e in gs.exited)

    # LP outcome
    if gs.lp_satisfaction >= 70:
        lp_line = "LPs are already asking about Fund II. Block your calendar."
    elif gs.lp_satisfaction >= 45:
        lp_line = "LPs are satisfied. One asked if you're 'considering expanding the strategy.'"
    elif gs.lp_satisfaction >= 25:
        lp_line = "LPs are polite but distant. The Hartley Family Office CC'd their attorney on the last email."
    else:
        lp_line = "The Westfield Endowment investment committee wants a meeting. On a Saturday."

    st.markdown(f"""
    <div class="score-box">
      <div style="font-size:3.5rem;font-weight:900;color:{gc};">{grade}</div>
      <h1 style="margin:.4rem 0;">{"Fund Closed. Well Done." if bm>=goal else "Time's Up."}</h1>
      <p style="margin-bottom:1.25rem;">{lp_line}</p>
      <div style="display:flex;justify-content:space-around;margin:.75rem 0;">
        <div class="stat"><div class="stat-val" style="color:{gc};">{bm:.2f}×</div>
          <div class="stat-lbl">Final MOIC</div></div>
        <div class="stat"><div class="stat-val">{len(gs.exited)}</div>
          <div class="stat-lbl">Exits</div></div>
        <div class="stat"><div class="stat-val">{cf(realized)}</div>
          <div class="stat-lbl">Realized</div></div>
        <div class="stat">
          <div class="stat-val" style="color:{lp_color(gs.lp_satisfaction)};">{gs.lp_satisfaction}</div>
          <div class="stat-lbl">LP Score</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    if gs.exited:
        st.markdown("<h2 style='text-align:center;'>Deal Recap</h2>", unsafe_allow_html=True)
        for e in sorted(gs.exited, key=lambda x: -x["moic"]):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:.55rem .9rem;
                 background:var(--card);border-radius:10px;margin-bottom:.3rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong>
                <span class="c-muted" style="font-size:.75rem;"> (CEO: {e['ceo']})</span></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proceeds'])}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1,1,1])
    with c2:
        if st.button("🔄 New Fund", use_container_width=True):
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
