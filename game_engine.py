"""
CarryForge — Game Engine
========================
Pure game logic with no Streamlit dependencies.
Imported by carryforge.py (UI) and audit_sim.py (simulation).
"""
import numpy as np
import random
import json
import sqlite3
import os
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

MAX_PORTFOLIO = 4
# /tmp is writable on Streamlit Cloud; .claude works locally
DB_PATH = "/tmp/carryforge.db" if os.path.exists("/tmp") else ".claude/carryforge.db"
try:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
except Exception:
    pass

SEASONS = {
    1: {"name":"Bull Run","dot":"#4ade80","css":"s1c","exit_mod":1.15,"growth_mod":1.10,
        "title":"The Bull Is Running",
        "text":"Rates near zero. Every growth equity fund in NYC has more capital than ideas. "
               "Sellers know it. Price accordingly."},
    2: {"name":"The Turn","dot":"#fbbf24","css":"s2c","exit_mod":1.00,"growth_mod":0.95,
        "title":"The Market Has Turned",
        "text":"Easy money is gone. Buyers are more selective. Your LPs have started "
               "CC'ing their advisors on emails."},
    3: {"name":"The Reckoning","dot":"#f87171","css":"s3c","exit_mod":0.85,"growth_mod":0.88,
        "title":"Batten Down the Hatches",
        "text":"Rates up 300bps. Debt markets nearly closed. Companies that haven't "
               "exited are sitting a while longer."},
}

# Sectors: abbr = display tag, css = card gradient class
SECTORS = {
    "SaaS":       {"abbr":"SW",  "css":"card-saas",  "rev":(40,180), "margin":(.28,.50),"growth":(.12,.38)},
    "Hardware":   {"abbr":"HW",  "css":"card-hw",    "rev":(90,320), "margin":(.08,.20),"growth":(.04,.16)},
    "Healthcare": {"abbr":"HC",  "css":"card-health","rev":(70,260), "margin":(.14,.30),"growth":(.08,.24)},
    "Fintech":    {"abbr":"FT",  "css":"card-fin",   "rev":(35,130), "margin":(.22,.45),"growth":(.22,.50)},
    "Logistics":  {"abbr":"LG",  "css":"card-log",   "rev":(100,400),"margin":(.06,.14),"growth":(.05,.14)},
    "Media":      {"abbr":"MD",  "css":"card-media", "rev":(30,110), "margin":(.15,.32),"growth":(.10,.30)},
    "Industrial": {"abbr":"IN",  "css":"card-ind",   "rev":(120,380),"margin":(.08,.16),"growth":(.04,.12)},
    "Consumer":   {"abbr":"CS",  "css":"card-con",   "rev":(60,220), "margin":(.10,.22),"growth":(.06,.18)},
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
    {"name":"Apex Capital","initials":"AC","color":"#f87171","style":"aggressive","motto":"We don't pass. We outbid."},
    {"name":"Redwood PE","initials":"RW","color":"#4ade80","style":"conservative","motto":"Boring is beautiful."},
    {"name":"Meridian Partners","initials":"MP","color":"#a78bfa","style":"sleazy","motto":"Relationships. Always."},
    {"name":"Pinnacle Fund","initials":"PF","color":"#fbbf24","style":"arrogant","motto":"Second place is first loser."},
]

LP_CHARACTERS = [
    {"name":"Dr. Eleanor Voss","type":"Westfield Endowment","initials":"EV","color":"#60a5fa","personality":"conservative",
     "trait":"Demands quarterly ESG updates. Loves 10-year IRR charts.",
     "happy_msg":["Impressed with your discipline.", "The board was pleased this quarter.", "Exactly what we expected from you."],
     "angry_msg":["We're concerned about the leverage.", "Expected better DPI by now.", "My investment committee is asking questions."]},
    {"name":"Mike Carbone","type":"CalPERS West","initials":"MC","color":"#f87171","personality":"aggressive",
     "trait":"Wants top-quartile returns. 'Don't bore me with process.'",
     "happy_msg":["Now we're talking. Keep pushing.", "That's what I like to see.", "The committee is smiling. Good work."],
     "angry_msg":["These returns are embarrassing.", "My buddy at Apex is killing it.", "Give me a reason not to pull out."]},
    {"name":"Hartley & Hartley","type":"Family Office","initials":"HH","color":"#fbbf24","personality":"relationship",
     "trait":"Three generations of investing. Values honesty and quarterly calls.",
     "happy_msg":["Pleasure doing business, as always.", "The family is happy. That matters.", "Worth every dollar of carry."],
     "angry_msg":["Father wouldn't have tolerated this.", "We expected a call, not a deck.", "Trust is everything."]},
    {"name":"Atlas Foundation","type":"Nonprofit Endowment","initials":"AF","color":"#34d399","personality":"esg",
     "trait":"ESG-focused. Refuses to back extractive industries or high-polluters.",
     "happy_msg":["This aligns with our mission beautifully.", "Great returns. Great impact.", "The board gave a standing ovation."],
     "angry_msg":["This company's carbon footprint is unacceptable.", "Returns don't justify the harm.", "We need to discuss compliance."]},
]

FIRM_DEFAULTS = ["Genesis Capital","Ironwood Partners","Crestview Equity","Summit PE","Clarendon Fund","Northstar PE"]

DIFFICULTY = {
    "Casual":   {"cash":70e6,"exit_mult":10.5,"quarters":12,"lp_start":85,"lp_floor":28,"paths":{"moic":1.3,"lp":52,"exits":1}},
    "Balanced": {"cash":50e6,"exit_mult":9.2, "quarters":12,"lp_start":72,"lp_floor":20,"paths":{"moic":1.8,"lp":62,"exits":3}},
    "Hardcore": {"cash":35e6,"exit_mult":8.0, "quarters":12,"lp_start":55,"lp_floor":15,"paths":{"moic":2.2,"lp":58,"exits":4}},
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
    {"id":"ceo_poached","type":"crisis","title":"Your CEO Got Poached","icon":"",
     "template":"**{ceo}** — CEO of {co} — just got a $2.8M offer from {rival}. "
                "They called from the school parking lot.",
     "choices":[
        {"label":"Counter with 2% equity stake (+$300K)","effect":"ceo_stays"},
        {"label":"Match salary only","effect":"ceo_slows"},
        {"label":"Wish them luck. Start a search.","effect":"ceo_gone"},
     ]},
    {"id":"ceo_arrested","type":"crisis","title":"Legal Situation","icon":"",
     "template":"CEO of {co}, **{ceo}**, was arrested. 'Unrelated to business.' SEC says otherwise.",
     "choices":[
        {"label":"Terminate immediately. PR blackout.","effect":"ceo_fired_clean"},
        {"label":"Hire crisis lawyer, ride it out","effect":"crisis_lawyer"},
        {"label":"Back them publicly","effect":"disaster"},
     ]},
    {"id":"big_contract","type":"opportunity","title":"Enterprise Contract","icon":"",
     "template":"{co} got an LOI from a Fortune 50 — $14M ARR adding ~32% to revenue overnight.",
     "choices":[
        {"label":"Staff up fast — hire 45 people","effect":"big_growth"},
        {"label":"Sign it, figure out delivery later","effect":"medium_growth"},
        {"label":"Pass — too much execution risk","effect":"nothing"},
     ]},
    {"id":"customer_churn","type":"crisis","title":"Client Just Walked","icon":"",
     "template":"{co}'s largest customer — 19% of ARR — terminated. Their CFO: 'a nice experiment.'",
     "choices":[
        {"label":"Fly out, offer discount to stay","effect":"partial_save"},
        {"label":"Accept it and focus on pipeline","effect":"slight_miss"},
        {"label":"Sue for breach","effect":"litigation"},
     ]},
    {"id":"rival_bid","type":"rival","title":"Competing Bid","icon":"",
     "template":"**{rival}** just bid $9M over your offer for {co}. 'Using leverage we'd never touch.'",
     "choices":[
        {"label":"Walk away — discipline first","effect":"deal_lost"},
        {"label":"Match, tighten terms elsewhere","effect":"deal_expensive"},
        {"label":"Go lower, pitch operational value","effect":"deal_clever"},
     ]},
    {"id":"rival_email","type":"rival","title":"Interesting Email","icon":"",
     "template":"Email from **{rival}**: *'Heard you picked up {co}. Brave given the cap table. "
                "Let us know when you're ready to recap at a fair price.'*",
     "choices":[
        {"label":"Reply with a screenshot of your DPI","effect":"rival_rivalry"},
        {"label":"Ignore it","effect":"nothing"},
        {"label":"Forward to LP for a laugh","effect":"lp_amused"},
     ]},
    {"id":"lp_call","type":"lp","title":"LP on Line 1","icon":"",
     "template":"**{lp}** calling. DPI still 0x. 'Have you considered your exit timeline?' "
                "Call in 15 minutes.",
     "choices":[
        {"label":"Take it — promise Q3 exit","effect":"pressure_exit"},
        {"label":"Send deck — 'pipeline is strong'","effect":"bought_time"},
        {"label":"Have associate take it","effect":"lp_annoyed"},
     ]},
    {"id":"lp_pullout","type":"lp","title":"LP Threatening Withdrawal","icon":"",
     "template":"**{lp}** needs liquidity. Threatening to sell their stake at 30% discount.",
     "choices":[
        {"label":"Dividend recap on one company","effect":"recap_lp"},
        {"label":"Help find secondary buyer","effect":"lp_secondary"},
        {"label":"Call the bluff","effect":"lp_furious"},
     ]},
    {"id":"unsolicited_bid","type":"opportunity","title":"Someone Wants to Buy","icon":"",
     "template":"Strategic buyer: unsolicited offer for {co} at 38% premium. Answer by Friday.",
     "choices":[
        {"label":"Sell — take the money","effect":"force_exit"},
        {"label":"Run a full process","effect":"auction_process"},
        {"label":"Decline — just getting started","effect":"nothing"},
     ]},
    {"id":"add_on_deal","type":"opportunity","title":"Bolt-On Opportunity","icon":"",
     "template":"{co} found a smaller competitor for $9M. Adds 18% revenue and a great customer list.",
     "choices":[
        {"label":"Fund it","effect":"addon_success"},
        {"label":"Pass — keep management focused","effect":"nothing"},
        {"label":"Negotiate 20% lower first","effect":"addon_negotiate"},
     ]},
    {"id":"rate_shock","type":"crisis","title":"Fed Rate Shock","icon":"",
     "template":"Fed raised 75bps. Debt cost up $2.3M annually. "
                "Blackstone sent 'Navigating the New Normal.' You deleted it.",
     "choices":[
        {"label":"Refinance early on strongest company","effect":"rate_hedge"},
        {"label":"Accelerate exits","effect":"pressure_exit"},
        {"label":"Weather it","effect":"slight_miss"},
     ]},
    {"id":"sector_hot","type":"opportunity","title":"Your Sector Is Hot","icon":"",
     "template":"{co}'s sector on Fortune cover. Exit multiples doubled from a year ago.",
     "choices":[
        {"label":"Exit now at peak multiples","effect":"force_exit"},
        {"label":"Hold — ride the wave","effect":"risky_hold"},
        {"label":"Hire tier-1 CEO to prep for sale","effect":"ceo_upgrade"},
     ]},
    {"id":"mgmt_fight","type":"crisis","title":"Board Meeting Gone Wrong","icon":"",
     "template":"**{ceo}** and your operating partner aren't speaking after last board meeting. "
                "CFO: 'That was not great.'",
     "choices":[
        {"label":"Back the CEO","effect":"mgmt_stable"},
        {"label":"Side with the OP — shake up management","effect":"ceo_gone"},
        {"label":"Bring in a mediator","effect":"slow_resolution"},
     ]},
    {"id":"ipo_buzz","type":"opportunity","title":"Bankers Calling","icon":"",
     "template":"Goldman and Morgan both pitching IPO for {co}. Analyst: 'Exactly what the market wants.'",
     "choices":[
        {"label":"Set up a bake-off","effect":"ipo_process"},
        {"label":"Too early — wait another year","effect":"nothing"},
        {"label":"Take lunch but say no","effect":"nothing"},
     ]},
    {"id":"key_departure","type":"crisis","title":"Key Person Risk","icon":"",
     "template":"{co}'s CTO — author of 60% of the codebase — just handed in their notice.",
     "choices":[
        {"label":"Aggressive retention package","effect":"key_retained"},
        {"label":"Restructure team, promote from within","effect":"mgmt_stable"},
        {"label":"External search immediately","effect":"slight_miss"},
     ]},
    {"id":"partnership","type":"opportunity","title":"Strategic Partnership","icon":"",
     "template":"{co} offered an exclusive distribution deal with a 500-store retail chain.",
     "choices":[
        {"label":"Sign the exclusive","effect":"big_growth"},
        {"label":"Negotiate non-exclusive terms","effect":"medium_growth"},
        {"label":"Pass — don't like the counterparty","effect":"nothing"},
     ]},
]

# Effect definitions
EFFECTS = {
    "ceo_stays":       {"moic_d":+.16,"msg":"CEO stayed. Equity updated. They seem pleased."},
    "ceo_slows":       {"moic_d":-.08,"msg":"They took it. You have 90 days."},
    "ceo_gone":        {"moic_d":-.18,"msg":"CEO out. Search firm on retainer."},
    "ceo_fired_clean": {"moic_d":-.12,"msg":"Terminated. Legal risk contained. Business wobbling."},
    "crisis_lawyer":   {"moic_d":-.09,"msg":"Charges reduced. Optics still your problem."},
    "disaster":        {"moic_d":-.28,"msg":"SEC subpoenas arrived Friday afternoon."},
    "big_growth":      {"moic_d":+.22,"msg":"Bold bet paid. Revenue +30%. CEO insufferable."},
    "medium_growth":   {"moic_d":+.11,"msg":"Bumpy delivery. Contract held. Client renewed."},
    "nothing":         {"moic_d":.00,"msg":"Status quo. Deck identical to last quarter."},
    "partial_save":    {"moic_d":-.07,"msg":"12-month extension. Still going to leave."},
    "slight_miss":     {"moic_d":-.11,"msg":"Revenue down 16%. Pipeline 'robust.'"},
    "litigation":      {"moic_d":-.18,"msg":"Litigation expensive. Distraction worse."},
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
    "auction_process": {"moic_d":+.10,"msg":"Four bidders. Extracted another 20% on price."},
    "addon_success":   {"moic_d":+.12,"msg":"Tuck-in closed. Customer cross-sell working."},
    "addon_negotiate": {"moic_d":+.06,"msg":"Came back 20% lower. Counter-signed same afternoon."},
    "rate_hedge":      {"moic_d":+.05,"msg":"Locked 6.2% for 5 years. Feels smart already."},
    "risky_hold":      {"moic_d":+.12,"msg":"Wave didn't materialize. Multiple contracted 12%."},
    "ceo_upgrade":     {"moic_d":+.12,"msg":"Hired ex-Stripe COO. Restructured sales week one."},
    "mgmt_stable":     {"moic_d":+.05,"msg":"OP annoyed but professional. Board quieter."},
    "slow_resolution": {"moic_d":-.04,"msg":"Mediation took 6 weeks. Everyone technically aligned."},
    "ipo_process":     {"moic_d":+.09,"msg":"12-month process begins. Analyst calls next quarter."},
    "key_retained":    {"moic_d":+.08,"msg":"Retained with RSUs. Code commit rate up 40%."},
    "ceo_gone_fired":  {"moic_d":-.22,"msg":"CEO out. Interim named. Search begins Monday."},
}

# ─────────────────────────────────────────────────────────────────────────────
# VALUE CREATION LEVERS — player-driven company initiatives
# Each lever: cost in cash, success_rate, moic boost on success, moic penalty
# on failure. Applied at the start of next quarter.
# ─────────────────────────────────────────────────────────────────────────────

LEVERS = {
    "sales_push": {
        "label": "Sales Push",
        "short": "Sales",
        "desc": "Drive revenue aggressively — new reps, incentives, pipeline blitz",
        "cost": 0,
        "success_rate": 0.65,
        "win_moic": +0.12,
        "loss_moic": -0.06,
        "win_msg": "Sales initiative landed. Pipeline strong. CEO insufferable about it.",
        "loss_msg": "Overpromised to close deals. Churn starting.",
        "cooldown": 2,
    },
    "cost_cut": {
        "label": "Cost Restructuring",
        "short": "Cut Costs",
        "desc": "Cut SG&A and headcount to expand EBITDA margins",
        "cost": 0,
        "success_rate": 0.68,
        "win_moic": +0.09,
        "loss_moic": -0.08,
        "win_msg": "Costs trimmed 13%. Margins expanding ahead of plan.",
        "loss_msg": "Two senior engineers resigned during restructuring.",
        "cooldown": 3,
    },
    "bolt_on": {
        "label": "Bolt-On M&A",
        "short": "Bolt-On",
        "desc": "Acquire a smaller competitor for $8M",
        "cost": 8_000_000,
        "success_rate": 0.58,
        "win_moic": +0.19,
        "loss_moic": -0.07,
        "win_msg": "Tuck-in complete. EBITDA up 19%. CEO takes full credit.",
        "loss_msg": "Integration rocky. Six months of management distraction.",
        "cooldown": 4,
    },
    "exec_hire": {
        "label": "Executive Hire",
        "short": "Hire Exec",
        "desc": "Recruit an A-player exec (CEO/CFO/CRO). Recruiting fees: $400K",
        "cost": 400_000,
        "success_rate": 0.70,
        "win_moic": +0.13,
        "loss_moic": -0.09,
        "win_msg": "New exec excellent. GTM restructured in 45 days.",
        "loss_msg": "Culture clash. Two other leaders quit in protest.",
        "cooldown": 3,
    },
    "market_expand": {
        "label": "Market Expansion",
        "short": "Expand",
        "desc": "Enter a new geography or customer segment. Cost: $2.5M",
        "cost": 2_500_000,
        "success_rate": 0.52,
        "win_moic": +0.21,
        "loss_moic": -0.05,
        "win_msg": "New market working. Revenue trajectory fundamentally changed.",
        "loss_msg": "Expansion slower than modeled. 18-month payback horizon.",
        "cooldown": 4,
    },
    "exit_prep": {
        "label": "Exit Prep",
        "short": "Exit Prep",
        "desc": "Engage bankers, clean books, prepare data room. Cost: $800K",
        "cost": 800_000,
        "success_rate": 0.80,
        "win_moic": +0.08,
        "loss_moic": -0.02,
        "win_msg": "Data room clean. Strategics inbound. Multiple bidders forming.",
        "loss_msg": "Due diligence surfaced some surprises. Buyers cautious.",
        "cooldown": 5,
    },
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
    # Value creation levers
    pending_lever: str = ""          # selected this quarter, resolved on advance
    lever_cooldowns: dict = None     # lever_id → quarter last used
    lever_history: list = None       # [{q, lever, outcome, msg}]

    def __post_init__(self):
        if self.lever_cooldowns is None: self.lever_cooldowns = {}
        if self.lever_history   is None: self.lever_history   = []

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
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""CREATE TABLE IF NOT EXISTS saves (
            slot INTEGER PRIMARY KEY, data TEXT, ts TEXT, label TEXT)""")
        conn.commit(); conn.close()
    except Exception:
        pass

def save_game(slot: int, gs: GameState, label: str = ""):
    try:
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
    except Exception:
        pass

def load_game(slot: int) -> Optional[GameState]:
    try:
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
    except Exception:
        return None

def list_saves():
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT slot,label,ts FROM saves ORDER BY ts DESC").fetchall()
        conn.close()
        return rows
    except Exception:
        return []

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

def mc(v):   return "g" if v >= 2.0 else "go" if v >= 1.3 else "r"
def cf(v):   return f"${v/1e9:.2f}B" if abs(v) >= 1e9 else f"${v/1e6:.1f}M"
def lpc(s):  return "#4ade80" if s >= 60 else "#fbbf24" if s >= 35 else "#f87171"
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
        # Revenue in real $; sector ranges are in $M so multiply by 1e6
        rev   = np.random.uniform(*p["rev"]) * 1e6
        mg    = np.random.uniform(*p["margin"])
        eb    = rev * mg
        gr    = np.random.uniform(*p["growth"])
        em    = round(np.random.uniform(6.5, 9.8), 1)
        ev    = eb * em          # Enterprise Value ($)
        debt  = eb * np.random.uniform(3.0, 5.2)  # Debt ($)
        eq    = max(ev - debt, ev * 0.08)          # Equity check ($)
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

    # Guarantee at least 2 affordable deals (cash trap fix — Audit #2)
    budget = max(gs.cash * 0.55, DIFFICULTY[gs.difficulty]["cash"] * 0.40)
    affordable = [d for d in deals if d.entry_equity <= budget]
    if len(affordable) < 2:
        for _ in range(8):
            sector = random.choice(list(SECTORS))
            p = SECTORS[sector]
            rev2  = np.random.uniform(p["rev"][0], p["rev"][0]+(p["rev"][1]-p["rev"][0])*.4) * 1e6
            mg2   = np.random.uniform(*p["margin"])
            eb2   = rev2 * mg2
            em2   = round(np.random.uniform(6.2, 7.6), 1)
            ev2   = eb2 * em2
            debt2 = eb2 * np.random.uniform(2.8, 4.0)
            eq2   = max(ev2 - debt2, ev2 * 0.08)
            if eq2 <= budget:
                pool2 = [x for x in COMPANY_NAMES.get(sector,["Unnamed"]) if x not in {d.name for d in deals}]
                if not pool2: pool2 = COMPANY_NAMES.get(sector,["Unnamed"])
                name2 = random.choice(pool2)
                sc2 = np.random.uniform(*p["growth"]); tier2 = "standard"
                c2 = Company(id=hashlib.md5(f"{name2}{random.random()}".encode()).hexdigest()[:8],
                    name=name2,sector=sector,ceo=random.choice(CEO_NAMES),revenue=rev2,ebitda=eb2,
                    margin=mg2,growth=sc2,entry_multiple=em2,entry_ev=ev2,entry_debt=debt2,
                    entry_equity=eq2,entry_quarter=gs.quarter_num,tier=tier2)
                c2.pitch = make_deal_pitch(c2)
                deals.append(c2); affordable.append(c2)
                if len(affordable)>=2: break
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
        debt  = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.50, 0)

    # Current financials
    rev    = c.revenue * ((1 + eg) ** yh)
    ebitda = rev * c.margin

    # Peak exit window (sweet spot ~2–3.5 years)
    pm = 0.88 + yh * 0.12 if yh < 1.0 else (1.0 + (yh - 1.0) * 0.073 if yh <= 3.0
         else 1.22 - (yh - 3.0) * 0.025)

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
    to = sum(calc(c, gs)["equity"] for c in gs.companies) * 0.88 + sum(e.get("proc", 0) for e in gs.exited)
    return to / max(ti, 1)

def check_paths(gs: GameState) -> dict:
    """Evaluate the three win paths."""
    cfg = DIFFICULTY[gs.difficulty]["paths"]
    bm  = blended_moic(gs)
    q   = max(gs.quarter_num, 1)
    tot = gs.total_quarters
    return {
        "returns": {"hit": bm >= cfg["moic"], "target": cfg["moic"], "actual": round(bm, 2),
                    "label": "Returns King", "desc": f"Hit {cfg['moic']}× MOIC",
                    "pace": "ahead" if bm/cfg["moic"]/(q/tot) > 1.1 else "behind" if bm/cfg["moic"]/(q/tot) < 0.65 else "ok"},
        "lp":      {"hit": gs.lp_satisfaction >= cfg["lp"], "target": cfg["lp"], "actual": gs.lp_satisfaction,
                    "label": "LP Legend", "desc": f"Keep LPs ≥{cfg['lp']}",
                    "pace": "ahead" if gs.lp_satisfaction >= cfg["lp"] else "behind"},
        "exits":   {"hit": len(gs.exited) >= cfg["exits"], "target": cfg["exits"], "actual": len(gs.exited),
                    "label": "Deal Maker", "desc": f"{cfg['exits']}+ exits",
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
        gs.achievements.append("triple"); gs.event_log.insert(0, "Achievement: First 3× exit!")
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

    # ── Resolve pending value creation levers ────────────────────────────
    for c in gs.companies:
        if c.pending_lever and c.pending_lever in LEVERS:
            lev = LEVERS[c.pending_lever]
            won = random.random() < lev["success_rate"]
            effect = lev["win_moic"] if won else lev["loss_moic"]
            c.moic_modifier = max(0.10, min(c.moic_modifier + effect, 3.0))
            msg = (lev["win_msg"] if won else lev["loss_msg"])
            result = "WIN" if won else "MISS"
            gs.event_log.insert(0, f"{c.name} · {lev['label']}: [{result}] {msg}")
            gs.event_log = gs.event_log[:8]
            c.lever_history.append({"q": gs.quarter_num, "lever": c.pending_lever,
                                     "outcome": result, "msg": msg})
            c.lever_cooldowns[c.pending_lever] = gs.quarter_num
            c.pending_lever = ""
            if won: gs.sound_queue.append("OPPORTUNITY")
            else:   gs.sound_queue.append("CRISIS")

    if not gs.exited and gs.quarter_num > 4:
        lp_floor = DIFFICULTY[gs.difficulty].get("lp_floor", 15)
        gs.lp_satisfaction = max(lp_floor, gs.lp_satisfaction - 3)
        gs.event_log.insert(0, "LP satisfaction −3 this quarter (no exits yet). Exit a company to stabilize.")
        gs.event_log = gs.event_log[:8]
    gs.deals = make_deals(gs, 5)
    if gs.quarter_num >= gs.total_quarters:
        gs.screen = "score"; return
    new = gs.season
    if new != prev and gs.season_shown < new:
        gs.season_shown = new; si = SEASONS[new]
        gs.sound_queue.append("SEASON")
        gs.pending_event = {"id": f"season_{new}", "type": "season",
            "title": si["title"], "icon": "", "text": si["text"],
            "choices": [{"label": "Got it. Keep moving.", "effect": "nothing"}], "cid": None}
        return
    if random.random() < 0.45:
        ev = pick_event(gs)
        if ev:
            gs.pending_event = ev
            gs.sound_queue.append({"crisis":"CRISIS","opportunity":"OPPORTUNITY",
                                    "rival":"RIVAL","lp":"LP"}.get(ev["type"],"TICK"))

# ─────────────────────────────────────────────────────────────────────────────
# SOUND ENGINE
# ─────────────────────────────────────────────────────────────────────────────