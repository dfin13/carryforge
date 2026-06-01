"""
CarryForge v8.0
===============
Structure: Prestige (Fund I → II → III) + Three Seasons (Bull/Turn/Reckoning)
           + Three Parallel Win Paths (Returns King / LP Legend / Deal Maker)

No more pass/fail. Every run unlocks something for Fund II.
Three ways to win — every play style has a valid path.
Market has a dramatic arc baked in.
"""

import streamlit as st
import numpy as np
import random
from dataclasses import dataclass, field

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

  .stat{text-align:center;}
  .stat-val{font-size:1.3rem;font-weight:800;color:var(--text);line-height:1.2;}
  .stat-lbl{font-size:.65rem;font-weight:600;color:var(--muted);text-transform:uppercase;
             letter-spacing:.07em;margin-top:.15rem;}

  .dcard{background:var(--card);border:1px solid var(--border);border-left:3px solid transparent;
         border-radius:13px;padding:.85rem 1rem;margin-bottom:.45rem;}
  .dcard-SaaS{border-left-color:var(--blue);}
  .dcard-Hardware{border-left-color:var(--purple);}
  .dcard-Healthcare{border-left-color:var(--pink);}
  .dcard-Fintech{border-left-color:var(--teal);}

  .tag{display:inline-block;background:var(--card2);border:1px solid var(--border);
       border-radius:6px;padding:.18rem .48rem;font-size:.72rem;font-weight:600;
       color:var(--muted);margin:2px;}
  .tag span{color:var(--text);}

  /* narrative events */
  .ev-card{background:var(--card);border:1px solid;border-radius:14px;padding:1.2rem 1.4rem;margin:.5rem 0;}
  .ev-crisis{border-color:#ef4444;background:rgba(239,68,68,.06);}
  .ev-opportunity{border-color:#10b981;background:rgba(16,185,129,.06);}
  .ev-rival{border-color:#8b5cf6;background:rgba(139,92,246,.06);}
  .ev-lp{border-color:#f59e0b;background:rgba(245,158,11,.06);}
  .ev-season{border-color:#3b82f6;background:rgba(59,130,246,.08);}
  .ev-neutral{border-color:var(--border);}

  .choice-btn button{
    background:var(--card2)!important;border:1px solid var(--border)!important;
    color:var(--text)!important;box-shadow:none!important;text-align:left!important;
  }
  .choice-btn button:hover{border-color:var(--green)!important;color:var(--green)!important;transform:none!important;}

  /* season badge */
  .season-bull    {color:#10b981;font-weight:700;}
  .season-turn    {color:#f59e0b;font-weight:700;}
  .season-bear    {color:#ef4444;font-weight:700;}

  /* win path badges */
  .path-hit   {background:rgba(16,185,129,.15);border:1px solid var(--green);
               border-radius:10px;padding:.6rem 1rem;margin:.3rem 0;}
  .path-miss  {background:var(--card2);border:1px solid var(--border);
               border-radius:10px;padding:.6rem 1rem;margin:.3rem 0;opacity:.55;}

  /* unlock card */
  .unlock-card{background:var(--card);border:1px solid rgba(245,158,11,.35);
               border-radius:14px;padding:1.25rem;margin:.5rem 0;text-align:center;}

  .goal-track{background:var(--card2);border-radius:999px;height:8px;overflow:hidden;margin:.2rem 0;}
  .goal-fill {height:8px;border-radius:999px;background:linear-gradient(90deg,var(--green),#34d399);}
  .score-box{background:var(--card);border:1px solid var(--border);border-radius:18px;
             padding:2rem;text-align:center;max-width:520px;margin:1.5rem auto;}
  .lp-bar{height:6px;border-radius:999px;background:var(--card2);overflow:hidden;margin:.25rem 0;}
  .lp-fill{height:6px;border-radius:999px;}

  .c-green{color:var(--green)!important;font-weight:700;}
  .c-gold {color:var(--gold)!important;font-weight:700;}
  .c-red  {color:var(--red)!important;font-weight:700;}
  .c-muted{color:var(--muted)!important;}
  .fw7{font-weight:700;}

  @media(max-width:640px){
    .block-container{padding:.9rem .9rem 5rem;}
    .stat-val{font-size:1.05rem;}
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

MAX_PORTFOLIO = 4

SEASONS = {
    1: {
        "name":"Bull Run","emoji":"🟢","css":"season-bull",
        "quarters":(1,4),
        "exit_mod":1.15,"growth_mod":1.10,
        "desc":"Capital is cheap. Multiples are generous. Everyone's raising.",
        "transition_title":"The Bull Is Running",
        "transition_text":"Rates are near zero. Every growth equity fund in NYC has more capital than ideas. "
                          "Sellers know it. Price accordingly.",
    },
    2: {
        "name":"The Turn","emoji":"🟡","css":"season-turn",
        "quarters":(5,8),
        "exit_mod":1.00,"growth_mod":0.95,
        "desc":"Markets normalizing. Some LPs getting nervous.",
        "transition_title":"The Market Has Turned",
        "transition_text":"The easy money is gone. Buyers are more selective. "
                          "Your LPs have started CC'ing their advisors on emails. Time to execute.",
    },
    3: {
        "name":"The Reckoning","emoji":"🔴","css":"season-bear",
        "quarters":(9,12),
        "exit_mod":0.85,"growth_mod":0.88,
        "desc":"Credit tight. Exits harder. Timing is everything.",
        "transition_title":"Batten Down the Hatches",
        "transition_text":"Rates are up 300bps. Debt markets are nearly closed. "
                          "Companies that haven't exited are going to sit a while longer. "
                          "Your LPs know this. They're watching your every move.",
    },
}

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
    {"name":"Westfield Endowment","type":"university"},
    {"name":"CalPERS West","type":"pension"},
    {"name":"Hartley Family Office","type":"family"},
    {"name":"Atlas Foundation","type":"nonprofit"},
]

NARRATIVE_EVENTS = [
    {"id":"ceo_offer","type":"crisis","title":"Your CEO Got Poached","icon":"😬",
     "template":"**{ceo}** — the CEO of {co} — just got a $2.4M offer from {rival}. "
                "They called you from the parking lot of their kid's school to tell you.",
     "choices":[
        {"label":"Counter with a 2% equity stake","effect":"ceo_stays"},
        {"label":"Match their salary, nothing else","effect":"ceo_leaves_slow"},
        {"label":"Wish them luck and start interviewing","effect":"ceo_gone"},
     ]},
    {"id":"ceo_arrested","type":"crisis","title":"Legal Situation","icon":"🚔",
     "template":"The CEO of {co}, **{ceo}**, was arrested this morning. "
                "Unrelated to the business, apparently. SEC says otherwise.",
     "choices":[
        {"label":"Terminate immediately, full PR blackout","effect":"ceo_gone_clean"},
        {"label":"Hire a crisis lawyer, ride it out","effect":"crisis_managed"},
        {"label":"Publicly back them — they said they're innocent","effect":"disaster"},
     ]},
    {"id":"major_customer","type":"opportunity","title":"Enterprise Deal","icon":"🤝",
     "template":"{co} just got a letter of intent from a Fortune 50 company — "
                "a $12M ARR contract that would add ~30% to revenue overnight.",
     "choices":[
        {"label":"Staff up fast to deliver — hire 40 people","effect":"big_growth"},
        {"label":"Sign it, figure out delivery later","effect":"medium_growth"},
        {"label":"Pass — too much execution risk","effect":"nothing"},
     ]},
    {"id":"customer_churn","type":"crisis","title":"Client Just Walked","icon":"💨",
     "template":"{co}'s **largest customer** — 18% of ARR — terminated their contract. "
                "Their new CFO called your portfolio company 'a nice experiment that didn't work.'",
     "choices":[
        {"label":"Fly out immediately, offer a discount to stay","effect":"partial_save"},
        {"label":"Accept it and focus on new pipeline","effect":"slight_hit"},
        {"label":"Sue for breach of contract","effect":"war"},
     ]},
    {"id":"rival_bid","type":"rival","title":"Competing Bid","icon":"😤",
     "template":"**{rival}** just submitted a competing bid for {co} — $8M over your offer. "
                "Word is they're using leverage you'd never touch.",
     "choices":[
        {"label":"Walk away — you have discipline","effect":"lose_deal"},
        {"label":"Match their price, tighten terms elsewhere","effect":"win_expensive"},
        {"label":"Go lower and pitch your operational value","effect":"win_clever"},
     ]},
    {"id":"rival_email","type":"rival","title":"Interesting Email","icon":"📧",
     "template":"You get an email from **{rival}**: "
                "*'Heard you picked up {co}. Brave choice given the cap table. "
                "Let us know when you're ready to recap at a fair price.'*",
     "choices":[
        {"label":"Reply with a screenshot of your DPI","effect":"rivalry_up"},
        {"label":"Ignore it","effect":"nothing"},
        {"label":"Forward it to your LP — let them laugh too","effect":"lp_amused"},
     ]},
    {"id":"lp_call","type":"lp","title":"LP on Line 1","icon":"📞",
     "template":"**{lp}** is calling. Again. They want to know why DPI is still at 0x "
                "and whether you've 'considered your exit timeline.' The call is in 15 minutes.",
     "choices":[
        {"label":"Take the call, promise a Q3 exit","effect":"pressure_sell"},
        {"label":"Send an update deck with 'pipeline is strong'","effect":"bought_time"},
        {"label":"Have your associate take it","effect":"lp_annoyed"},
     ]},
    {"id":"lp_pullout","type":"lp","title":"LP Threatening to Withdraw","icon":"🚨",
     "template":"**{lp}** needs liquidity. Threatening to sell their stake at a 30% discount "
                "unless you can offer a partial return.",
     "choices":[
        {"label":"Orchestrate a dividend recap on one company","effect":"lp_happy_hit"},
        {"label":"Help them find a secondary buyer","effect":"lp_exits"},
        {"label":"Call their bluff","effect":"lp_furious"},
     ]},
    {"id":"unsolicited_bid","type":"opportunity","title":"Someone Wants to Buy","icon":"💸",
     "template":"A strategic buyer just made an unsolicited offer for {co} at "
                "a 35% premium to last valuation. They want an answer by Friday.",
     "choices":[
        {"label":"Sell — take the money","effect":"forced_exit"},
        {"label":"Run a full process, see if others bid","effect":"auction"},
        {"label":"Decline — you're just getting started","effect":"nothing"},
     ]},
    {"id":"ipo_buzz","type":"opportunity","title":"Bankers Are Calling","icon":"🏦",
     "template":"Goldman and Morgan Stanley are both calling about an IPO for {co}. "
                "The analyst said 'you're exactly what the market wants right now.'",
     "choices":[
        {"label":"Explore it — set up a bake-off","effect":"ipo_prep"},
        {"label":"Too early — wait another year","effect":"nothing"},
        {"label":"Take their lunch but say no","effect":"nothing"},
     ]},
    {"id":"management_fight","type":"crisis","title":"Board Meeting Gone Wrong","icon":"🥊",
     "template":"Your last board meeting for {co} ended with **{ceo}** and your operating partner "
                "not speaking. The CFO texted afterward: 'That was not great.'",
     "choices":[
        {"label":"Back the CEO","effect":"mgmt_stable"},
        {"label":"Back the OP — shake up management","effect":"ceo_gone"},
        {"label":"Mediator call this week","effect":"slow_resolution"},
     ]},
    {"id":"add_on","type":"opportunity","title":"Bolt-On Opportunity","icon":"🧩",
     "template":"{co} found a smaller competitor willing to sell for $8M. "
                "Tuck-in adds 15% revenue and a decent customer list. CEO is excited.",
     "choices":[
        {"label":"Fund it","effect":"addon_win"},
        {"label":"Pass — keep management focused","effect":"nothing"},
        {"label":"Negotiate a lower price first","effect":"addon_maybe"},
     ]},
    {"id":"rate_shock","type":"crisis","title":"Rate Shock","icon":"📉",
     "template":"The Fed raised rates 75bps. Your debt cost just went up $2M annually. "
                "Blackstone sent an email titled 'Navigating the New Normal.' You deleted it.",
     "choices":[
        {"label":"Refinance early on best company","effect":"rate_hedged"},
        {"label":"Accelerate exits before credit tightens","effect":"pressure_sell"},
        {"label":"Weather it","effect":"slight_hit"},
     ]},
    {"id":"sector_boom","type":"opportunity","title":"Your Sector Is Hot","icon":"🔥",
     "template":"{co}'s sector just got featured on the cover of Fortune. "
                "Exit multiples are up 2× from a year ago.",
     "choices":[
        {"label":"Exit now while multiples are peak","effect":"forced_exit"},
        {"label":"Hold for the wave","effect":"risky_hold"},
        {"label":"Use the hype to recruit a tier-1 CEO","effect":"ceo_upgrade"},
     ]},
]

EFFECTS = {
    "ceo_stays":        {"moic_delta":+.20, "msg":"CEO stayed. Equity vesting updated. They seem pleased."},
    "ceo_leaves_slow":  {"moic_delta":-.10, "msg":"They took it. You have 90 days."},
    "ceo_gone":         {"moic_delta":-.25, "msg":"CEO out. Search firm on retainer. Team is nervous."},
    "ceo_gone_clean":   {"moic_delta":-.20, "msg":"Terminated. Legal risk contained. Business wobbling."},
    "crisis_managed":   {"moic_delta":-.10, "msg":"Charges reduced. Optics are still your problem."},
    "disaster":         {"moic_delta":-.40, "msg":"SEC subpoenas arrived Friday afternoon."},
    "big_growth":       {"moic_delta":+.30, "msg":"Bold bet paid. Revenue +28%. CEO is insufferable."},
    "medium_growth":    {"moic_delta":+.15, "msg":"Bumpy delivery. Contract held. Client renewed last minute."},
    "nothing":          {"moic_delta": .00, "msg":"Status quo. Deck looks exactly the same as last quarter."},
    "partial_save":     {"moic_delta":-.08, "msg":"12-month extension. They're still going to leave."},
    "slight_hit":       {"moic_delta":-.12, "msg":"Revenue down 18%. Pipeline is 'robust' apparently."},
    "war":              {"moic_delta":-.30, "msg":"Litigation is expensive. Distraction is worse."},
    "lose_deal":        {"moic_delta": .00, "msg":"Deal lost. You walk out saying 'discipline.'"},
    "win_expensive":    {"moic_delta":-.05, "msg":"Won it. Paid over market. Model needs a hero exit."},
    "win_clever":       {"moic_delta":+.08, "msg":"Seller picked you over the higher bid. Reputation matters."},
    "rivalry_up":       {"moic_delta": .00, "msg":"They didn't reply. Probably furious."},
    "lp_amused":        {"lp_delta":  +5,   "msg":"LP laughed. Said 'these guys.' Good relationship."},
    "pressure_sell":    {"force_exit":True, "msg":"You committed to an exit. Now deliver."},
    "bought_time":      {"lp_delta":  -3,   "msg":"They accepted the deck. Called again 3 weeks later."},
    "lp_annoyed":       {"lp_delta": -10,   "msg":"Associate took it. LP is 63 and has been in PE since before you were born."},
    "lp_happy_hit":     {"moic_delta":-.05,"lp_delta":+10,"msg":"LP placated. Company took a small leverage hit."},
    "lp_exits":         {"lp_delta": -20,   "msg":"LP sold at 35% discount. New holder emails weekly."},
    "lp_furious":       {"lp_delta": -25,   "msg":"Called the bluff. You're personally calling every LP this Friday night."},
    "forced_exit":      {"force_exit":True, "msg":"Company going to market. Time to find out your IRR."},
    "auction":          {"moic_delta":+.12, "msg":"Four bidders showed. Extracted another 18% on price."},
    "ipo_prep":         {"moic_delta":+.08, "msg":"12-month process begins. Dress rehearsal with analysts next quarter."},
    "rate_hedged":      {"moic_delta":+.05, "msg":"Locked in 6.2% for 5 years. Feels smart already."},
    "risky_hold":       {"moic_delta":+.10, "msg":"The wave didn't come. Multiple contracted 15%."},
    "ceo_upgrade":      {"moic_delta":+.15, "msg":"Hired ex-Stripe COO. First week: restructured sales."},
    "mgmt_stable":      {"moic_delta":+.05, "msg":"OP is annoyed but professional. Board quieter."},
    "slow_resolution":  {"moic_delta":-.05, "msg":"Mediation took 6 weeks. Everyone is technically aligned."},
    "addon_win":        {"moic_delta":+.15, "msg":"Tuck-in closed. Customer cross-sell already working."},
    "addon_maybe":      {"moic_delta":+.05, "msg":"They came back 20% lower. Counter-signed same afternoon."},
}

DIFFICULTY = {
    "Easy":    {"cash":60e6,"exit_mult":9.5,"quarters":12,"lp_start":80,
                "paths":{"moic":1.5,"lp":70,"exits":3}},
    "Balanced":{"cash":50e6,"exit_mult":8.5,"quarters":12,"lp_start":65,
                "paths":{"moic":1.75,"lp":65,"exits":4}},
    "Hard":    {"cash":40e6,"exit_mult":7.5,"quarters":12,"lp_start":50,
                "paths":{"moic":2.0,"lp":60,"exits":5}},
}

# Fund II / III unlocks based on paths hit
UNLOCKS = {
    0: {"fund":"Fund II","cash_mult":1.0,"lp_bonus":0,
        "flavor":"Same terms. LPs are giving you one more shot."},
    1: {"fund":"Fund II","cash_mult":1.3,"lp_bonus":8,
        "flavor":"One path hit. LPs are interested. Modest step up."},
    2: {"fund":"Fund II","cash_mult":1.6,"lp_bonus":15,
        "flavor":"Two paths hit. Strong showing. Real upgrade."},
    3: {"fund":"Fund II","cash_mult":2.0,"lp_bonus":25,
        "flavor":"All three paths. LPs are fighting over allocation. Fund III is on the table."},
}

# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class Company:
    id: str; name: str; sector: str; ceo: str
    revenue: float; ebitda: float; margin: float; growth: float
    entry_multiple: float; entry_ev: float; entry_debt: float; entry_equity: float
    entry_quarter: int = 0; moic_modifier: float = 1.0

@dataclass
class GameState:
    screen: str = "start"
    difficulty: str = "Balanced"
    quarter_num: int = 0
    cash: float = 50e6
    firm_name: str = ""
    partner_name: str = ""
    fund_number: int = 1
    fund_cash_mult: float = 1.0   # carried over from previous fund
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
    season_shown: int = 0   # which season transition has been displayed

    @property
    def year(self): return 2024 + self.quarter_num // 4
    @property
    def quarter(self): return (self.quarter_num % 4) + 1
    @property
    def total_quarters(self): return DIFFICULTY[self.difficulty]["quarters"]
    @property
    def season(self):
        q = self.quarter_num + 1   # 1-indexed current quarter
        if q <= 4:  return 1
        if q <= 8:  return 2
        return 3
    @property
    def season_info(self): return SEASONS[self.season]

# ─────────────────────────────────────────────
# GAME LOGIC
# ─────────────────────────────────────────────

def make_deals(gs: GameState, n: int = 5) -> list:
    owned = {c.name for c in gs.companies}
    deals = []
    for _ in range(n):
        sector = random.choice(list(SECTORS))
        p = SECTORS[sector]
        rev  = np.random.uniform(*p["rev"])
        mg   = np.random.uniform(*p["margin"])
        eb   = rev * mg
        gr   = np.random.uniform(*p["growth"])
        em   = round(np.random.uniform(6.5, 9.5), 1)
        ev   = eb * em
        debt = eb * np.random.uniform(3.0, 5.0)
        eq   = max(ev - debt, ev * 0.10)
        name = random.choice(COMPANY_NAMES[sector])
        deals.append(Company(
            id=f"{name[:3]}{random.randint(100,999)}",
            name=name, sector=sector, ceo=random.choice(CEO_NAMES),
            revenue=rev, ebitda=eb, margin=mg, growth=gr,
            entry_multiple=em, entry_ev=ev, entry_debt=debt,
            entry_equity=eq, entry_quarter=gs.quarter_num,
        ))
    return deals

def calc(c: Company, gs: GameState) -> dict:
    qh = gs.quarter_num - c.entry_quarter
    yh = qh / 4.0
    si = gs.season_info
    sm = gs.sector_mods.get(c.sector, 1.0)
    # Season modifiers affect growth and exit mult
    season_exit_mod   = si["exit_mod"]
    season_growth_mod = si["growth_mod"]
    mature_yrs = max(qh - 8, 0) / 4.0
    eg = c.growth * gs.growth_mod * sm * season_growth_mod * ((1 - 0.08) ** mature_yrs)

    debt = c.entry_debt
    for yr in range(1, int(yh) + 1):
        my   = max((yr * 4 - 8) / 4, 0)
        y_eg = c.growth * gs.growth_mod * sm * season_growth_mod * ((1 - 0.08) ** my)
        yr_e = c.revenue * ((1 + y_eg) ** yr) * c.margin
        debt = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)

    rev    = c.revenue * ((1 + eg) ** yh)
    ebitda = rev * c.margin

    # Peak exit window
    if yh < 1.0:   pm = 0.88 + yh * 0.12
    elif yh <= 3.0: pm = 1.0 + (yh - 1.0) * 0.05
    else:           pm = 1.10 - (yh - 3.0) * 0.05

    cfg    = DIFFICULTY[gs.difficulty]
    em     = cfg["exit_mult"] * gs.exit_mult_mod * sm * pm * season_exit_mod
    equity = max(ebitda * em - debt, 0) * max(c.moic_modifier, 0.1)
    moic   = equity / max(c.entry_equity, 1)
    irr    = (moic ** (1 / max(yh, 0.25)) - 1) if yh > 0 else 0
    return {"revenue": rev, "ebitda": ebitda, "equity": equity,
            "moic": moic, "irr": irr, "yh": yh, "peak_mod": pm}

def blended_moic(gs: GameState) -> float:
    ti = sum(c.entry_equity for c in gs.companies) + sum(e["eq"] for e in gs.exited)
    to = sum(calc(c, gs)["equity"] for c in gs.companies) * 0.70 + sum(e["proc"] for e in gs.exited)
    return to / max(ti, 1)

def proj3(d: Company, gs: GameState) -> float:
    r3   = d.revenue * ((1 + d.growth) ** 3)
    eb3  = r3 * d.margin
    debt = d.entry_debt
    for yr in range(1, 4):
        yr_e = d.revenue * ((1 + d.growth) ** yr) * d.margin
        debt = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)
    em = DIFFICULTY[gs.difficulty]["exit_mult"] * 1.10
    return max(eb3 * em - debt, 0) / max(d.entry_equity, 1)

def check_paths(gs: GameState) -> dict:
    """Evaluate all three win paths."""
    cfg = DIFFICULTY[gs.difficulty]["paths"]
    bm  = blended_moic(gs)
    return {
        "returns": {"hit": bm >= cfg["moic"],    "target": cfg["moic"],   "actual": round(bm, 2),   "label":"💰 Returns King",   "desc":f"Hit {cfg['moic']}× portfolio MOIC"},
        "lp":      {"hit": gs.lp_satisfaction >= cfg["lp"], "target": cfg["lp"],    "actual": gs.lp_satisfaction, "label":"🤝 LP Legend",     "desc":f"Keep LPs ≥{cfg['lp']} satisfaction"},
        "exits":   {"hit": len(gs.exited) >= cfg["exits"], "target": cfg["exits"],  "actual": len(gs.exited),     "label":"🏆 Deal Maker",    "desc":f"Close {cfg['exits']}+ exits"},
    }

def sell_company(gs: GameState, idx: int) -> dict:
    c = gs.companies[idx]
    m = calc(c, gs)
    gs.cash += m["equity"]
    gs.exited.append({
        "name": c.name, "sector": c.sector, "ceo": c.ceo,
        "moic": m["moic"], "irr": m["irr"],
        "proc": m["equity"], "eq": c.entry_equity, "yh": m["yh"],
    })
    gs.companies.pop(idx)
    gs.lp_satisfaction = min(100, gs.lp_satisfaction + 8)
    gs.event_log.insert(0, f"Exited {c.name} at {m['moic']:.2f}×. LPs satisfied.")
    gs.event_log = gs.event_log[:4]
    return m

def pick_event(gs: GameState) -> dict | None:
    if not gs.companies: return None
    pool = [e for e in NARRATIVE_EVENTS if e["type"] in ("crisis","opportunity")]
    pool += [e for e in NARRATIVE_EVENTS if e["type"] == "rival"]
    if not gs.exited and gs.quarter_num > 3:
        pool += [e for e in NARRATIVE_EVENTS if e["type"] == "lp"] * 3
    if not pool: return None
    ev = random.choice(pool)
    co = random.choice(gs.companies)
    text = ev["template"]
    text = text.replace("{co}", f"**{co.name}**").replace("{ceo}", co.ceo)
    text = text.replace("{rival}", gs.rival.get("name","a rival"))
    text = text.replace("{lp}", random.choice([lp["name"] for lp in LP_NAMES]))
    return {"id":ev["id"],"type":ev["type"],"title":ev["title"],"icon":ev["icon"],
            "text":text,"choices":ev["choices"],"cid":co.id}

def apply_effect(gs: GameState, key: str, cid: str | None):
    eff = EFFECTS.get(key, EFFECTS["nothing"])
    if cid:
        for c in gs.companies:
            if c.id == cid:
                if "moic_delta" in eff:
                    c.moic_modifier = max(0.1, min(c.moic_modifier + eff["moic_delta"], 3.0))
                if eff.get("force_exit"):
                    gs.forced_exit_id = c.id
                break
    if "lp_delta" in eff:
        gs.lp_satisfaction = max(0, min(100, gs.lp_satisfaction + eff["lp_delta"]))
    gs.event_log.insert(0, eff["msg"])
    gs.event_log = gs.event_log[:4]

def advance_quarter(gs: GameState):
    prev_season = gs.season
    gs.quarter_num += 1

    # Natural LP decay when no exits
    if not gs.exited and gs.quarter_num > 3:
        gs.lp_satisfaction = max(0, gs.lp_satisfaction - 3)

    gs.deals = make_deals(gs, 5)

    if gs.quarter_num >= gs.total_quarters:
        gs.screen = "score"
        return

    # Season transition — show once per season change
    new_season = gs.season
    if new_season != prev_season and gs.season_shown < new_season:
        gs.season_shown = new_season
        si = SEASONS[new_season]
        gs.pending_event = {
            "id": f"season_{new_season}",
            "type": "season",
            "title": si["transition_title"],
            "icon": si["emoji"],
            "text": si["transition_text"],
            "choices": [{"label": "Got it. Keep moving.", "effect": "nothing"}],
            "cid": None,
        }
        return

    # Narrative event ~60%
    if random.random() < 0.60:
        ev = pick_event(gs)
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
# HELPERS
# ─────────────────────────────────────────────
def mc(v): return "c-green" if v >= 2.0 else "c-gold" if v >= 1.3 else "c-red"
def cf(v): return f"${v/1e9:.2f}B" if abs(v) >= 1e9 else f"${v/1e6:.1f}M"
def lpc(s): return "#10b981" if s >= 60 else "#f59e0b" if s >= 35 else "#ef4444"

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
        Build a PE empire. Three ways to win. No two games the same.
      </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("setup"):
        c1, c2 = st.columns(2)
        with c1: firm = st.text_input("Firm name", placeholder="e.g. Meridian Capital")
        with c2: partner = st.text_input("Your name", placeholder="e.g. Alex Chen")
        st.markdown("<br>", unsafe_allow_html=True)
        diff = st.radio("Difficulty", ["Easy","Balanced","Hard"], horizontal=True, index=1,
                        captions=["$60M · relaxed","$50M · realistic","$40M · brutal"])

        # Show the three paths for chosen difficulty
        p = DIFFICULTY[diff]["paths"]
        st.markdown(f"""
        <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;
             padding:1rem;margin:.75rem 0;">
          <div style="font-size:.78rem;color:var(--muted);margin-bottom:.5rem;font-weight:600;
               text-transform:uppercase;letter-spacing:.06em;">Three ways to win</div>
          <div style="display:flex;gap:1rem;flex-wrap:wrap;">
            <span style="font-size:.88rem;">💰 <strong>Returns King</strong> — hit {p['moic']}× MOIC</span>
            <span style="font-size:.88rem;">🤝 <strong>LP Legend</strong> — keep LPs ≥{p['lp']}</span>
            <span style="font-size:.88rem;">🏆 <strong>Deal Maker</strong> — close {p['exits']}+ exits</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.form_submit_button("Start Fund I →", use_container_width=True):
            cfg = DIFFICULTY[diff]
            gs  = GameState(
                screen="game", difficulty=diff,
                cash=cfg["cash"], lp_satisfaction=cfg["lp_start"],
                firm_name=firm.strip() or "Genesis Capital",
                partner_name=partner.strip() or "Alex",
                rival=random.choice(RIVAL_FIRMS),
            )
            gs.deals = make_deals(gs, 5)
            st.session_state.gs = gs
            st.rerun()

# ─────────────────────────────────────────────
# SCREEN: EVENT
# ─────────────────────────────────────────────
def screen_event():
    gs = G()
    ev = gs.pending_event
    css = {"crisis":"ev-crisis","opportunity":"ev-opportunity",
           "rival":"ev-rival","lp":"ev-lp","season":"ev-season"}.get(ev.get("type",""),"ev-neutral")

    st.markdown(f"""
    <div class="ev-card {css}">
      <div style="font-size:2rem;margin-bottom:.5rem;">{ev.get('icon','📋')}</div>
      <h2 style="margin:0 0 .75rem;">{ev.get('title','')}</h2>
      <p style="font-size:.95rem;color:var(--text);line-height:1.65;">{ev.get('text','')}</p>
    </div>
    """, unsafe_allow_html=True)

    choices = ev.get("choices", [])
    is_season = ev.get("type") == "season"

    if not is_season:
        st.markdown("<br><strong>What do you do?</strong>")

    cols = st.columns(max(len(choices), 1))
    for i, ch in enumerate(choices):
        with cols[i]:
            st.markdown('<div class="choice-btn">', unsafe_allow_html=True)
            if st.button(ch["label"], key=f"ch_{i}_{gs.quarter_num}", use_container_width=True):
                apply_effect(gs, ch.get("effect","nothing"), ev.get("cid"))
                if gs.forced_exit_id:
                    idx = next((j for j,c in enumerate(gs.companies) if c.id==gs.forced_exit_id), None)
                    if idx is not None: sell_company(gs, idx)
                    gs.forced_exit_id = ""
                gs.pending_event = {}
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if gs.event_log and len(gs.event_log) > 1:
        st.markdown(f"""
        <div style="margin-top:1rem;padding:.55rem .9rem;background:var(--card2);
             border-radius:10px;font-size:.82rem;color:var(--muted);">
          <strong>Last quarter:</strong> {gs.event_log[1]}
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCREEN: GAME
# ─────────────────────────────────────────────
def screen_game():
    gs = G()
    if gs.pending_event:
        screen_event()
        return

    cfg = DIFFICULTY[gs.difficulty]
    si  = gs.season_info
    bm  = blended_moic(gs)
    paths = check_paths(gs)
    paths_hit = sum(1 for p in paths.values() if p["hit"])

    # ── Header ──────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 1.2, 1.6])
    with c1:
        fn = gs.fund_number
        fund_label = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
        st.markdown(f"<h1>{gs.firm_name} <span style='font-size:1rem;color:var(--muted);font-weight:400;'>· {fund_label}</span></h1>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat"><div class="stat-val">{cf(gs.cash)}</div>
          <div class="stat-lbl">Cash</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat">
          <div class="stat-val"><span class="{si['css']}">{si['emoji']}</span> {gs.year} Q{gs.quarter}</div>
          <div class="stat-lbl">{si['name']}</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="stat">
          <div class="stat-val {mc(bm)}">{bm:.2f}×</div>
          <div class="stat-lbl">Portfolio</div></div>""", unsafe_allow_html=True)
    with c5:
        if st.button("⏭  Next Quarter", use_container_width=True, key="nq"):
            advance_quarter(gs)
            st.rerun()

    # ── Three win paths mini-bar ─────────────────────────────
    p = cfg["paths"]
    path_items = [
        ("💰", paths["returns"]["hit"], f"Returns King {bm:.2f}× / {p['moic']}×"),
        ("🤝", paths["lp"]["hit"],      f"LP Legend {gs.lp_satisfaction} / {p['lp']}"),
        ("🏆", paths["exits"]["hit"],   f"Deal Maker {len(gs.exited)} / {p['exits']} exits"),
    ]
    qtrs_left = gs.total_quarters - gs.quarter_num
    cols_path = st.columns([1,1,1,1])
    for i,(icon,hit,label) in enumerate(path_items):
        color = "#10b981" if hit else "#64748b"
        bg    = "rgba(16,185,129,.12)" if hit else "transparent"
        with cols_path[i]:
            st.markdown(f"""<div style="background:{bg};border:1px solid {color};border-radius:8px;
                 padding:.35rem .6rem;text-align:center;font-size:.75rem;color:{color};font-weight:600;">
                {icon} {label}</div>""", unsafe_allow_html=True)
    with cols_path[3]:
        st.markdown(f"""<div style="border:1px solid var(--border);border-radius:8px;
             padding:.35rem .6rem;text-align:center;font-size:.75rem;color:var(--muted);">
             ⏱ {qtrs_left} qtrs left</div>""", unsafe_allow_html=True)

    # LP bar
    lp_c = lpc(gs.lp_satisfaction)
    st.markdown(f"""
    <div style="margin:.55rem 0 .25rem;display:flex;align-items:center;gap:.6rem;">
      <span style="font-size:.72rem;color:var(--muted);white-space:nowrap;">LP Satisfaction</span>
      <div class="lp-bar" style="flex:1">
        <div class="lp-fill" style="width:{gs.lp_satisfaction}%;background:{lp_c};"></div>
      </div>
      <span style="font-size:.72rem;color:{lp_c};font-weight:700;">{gs.lp_satisfaction}/100</span>
    </div>
    """, unsafe_allow_html=True)

    if gs.lp_satisfaction < 35:
        st.error("🚨 LPs are threatening to pull out. Exit something.")
    elif gs.lp_satisfaction < 50:
        st.warning("⚠️ LPs getting restless. They want distributions.")

    if gs.event_log:
        st.markdown(f"""
        <div style="padding:.5rem .85rem;background:var(--card2);border-radius:10px;
             font-size:.81rem;color:var(--muted);margin:.3rem 0 .1rem;">
          {gs.event_log[0]}</div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Portfolio ────────────────────────────────────────────
    if gs.companies:
        full = len(gs.companies) >= MAX_PORTFOLIO
        st.markdown(f"<h2>📊 Portfolio ({len(gs.companies)}/{MAX_PORTFOLIO})"
                    + (" <span style='font-size:.8rem;color:var(--red);'>— full, sell to buy</span>" if full else "")
                    + "</h2>", unsafe_allow_html=True)
        sell_idx = None
        for i, c in enumerate(gs.companies):
            m   = calc(c, gs)
            sec = SECTORS[c.sector]
            yh  = m["yh"]
            age = f"{yh:.1f}y" if yh >= 1 else f"{int(round(yh*4))}q"
            pw  = m["peak_mod"]
            win = "🟢" if pw >= 1.08 else ("🟡" if pw >= 0.98 else "🔴")
            dmg = f' <span style="color:var(--red);font-size:.72rem;">⚠ damaged</span>' if c.moic_modifier < 0.85 else ""
            bst = f' <span style="color:var(--green);font-size:.72rem;">✨ boosted</span>' if c.moic_modifier > 1.15 else ""

            ca,cb,cc,cd,ce = st.columns([3,1.1,1.1,1.1,.9])
            with ca:
                st.markdown(f"""<div class="dcard dcard-{c.sector}">
                  <span class="fw7">{sec['emoji']} {c.name}</span>
                  <span class="c-muted" style="font-size:.73rem;margin-left:.3rem;">
                    CEO: {c.ceo} · {age} · {win}</span>{dmg}{bst}
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
            m = calc(gs.companies[sell_idx], gs)
            cname = gs.companies[sell_idx].name
            sell_company(gs, sell_idx)
            emoji = "🏆" if m["moic"] >= 2.0 else "✅" if m["moic"] >= 1.4 else "📉"
            st.success(f"{emoji} Exited **{cname}** — {m['moic']:.2f}× · {cf(m['equity'])}")
            st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Deal Flow ─────────────────────────────────────────────
    full = len(gs.companies) >= MAX_PORTFOLIO
    st.markdown("<h2>🎯 Deal Flow</h2>", unsafe_allow_html=True)
    buy_idx = None
    for i, d in enumerate(gs.deals):
        sec = SECTORS[d.sector]
        pm3 = proj3(d, gs)
        can = d.entry_equity <= gs.cash and not full

        ca,cb,cc,cd,ce = st.columns([3,1.1,1.1,1.1,.9])
        with ca:
            st.markdown(f"""<div class="dcard dcard-{d.sector}">
              <h3>{sec['emoji']} {d.name}</h3>
              <span class="c-muted" style="font-size:.73rem;">CEO: {d.ceo}</span><br>
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

    if gs.exited:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2>🏆 Exits</h2>", unsafe_allow_html=True)
        for e in reversed(gs.exited[-5:]):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.48rem .85rem;background:var(--card);border-radius:10px;margin-bottom:.28rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong>
                <span class="c-muted" style="font-size:.73rem;"> · {e['yh']:.1f}yr</span></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCREEN: SCORE
# ─────────────────────────────────────────────
def screen_score():
    gs    = G()
    cfg   = DIFFICULTY[gs.difficulty]
    bm    = blended_moic(gs)
    paths = check_paths(gs)
    n_hit = sum(1 for p in paths.values() if p["hit"])
    unlock = UNLOCKS[n_hit]
    fn    = gs.fund_number

    # Grade based on paths hit, not raw number
    grade_map  = {3:("S","#f59e0b"), 2:("A","#10b981"), 1:("B","#3b82f6"), 0:("C","#ef4444")}
    grade, gc  = grade_map[n_hit]

    realized   = sum(e["proc"] for e in gs.exited)

    # LP closing quote
    lp_quotes = {
        range(70,101): "LPs are asking about Fund II before you've even closed this one. Block your calendar.",
        range(45,70):  "LPs are satisfied. One asked if you're 'considering expanding the strategy.'",
        range(25,45):  "LPs are polite but distant. Hartley Family Office CC'd their attorney on the last email.",
        range(0,25):   "Westfield Endowment investment committee wants a meeting. On a Saturday.",
    }
    lp_quote = next((v for r,v in lp_quotes.items() if gs.lp_satisfaction in r), "")

    # Score header
    fund_label = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    st.markdown(f"""
    <div class="score-box">
      <div style="font-size:.8rem;color:var(--muted);margin-bottom:.25rem;">{gs.firm_name} · {fund_label} Complete</div>
      <div style="font-size:3.5rem;font-weight:900;color:{gc};">{grade}</div>
      <h1 style="margin:.4rem 0;">{n_hit}/3 paths hit</h1>
      <p style="margin-bottom:1.25rem;font-size:.9rem;">{lp_quote}</p>
      <div style="display:flex;justify-content:space-around;margin:.75rem 0;">
        <div class="stat"><div class="stat-val" style="color:{gc};">{bm:.2f}×</div>
          <div class="stat-lbl">MOIC</div></div>
        <div class="stat"><div class="stat-val">{len(gs.exited)}</div>
          <div class="stat-lbl">Exits</div></div>
        <div class="stat"><div class="stat-val">{cf(realized)}</div>
          <div class="stat-lbl">Realized</div></div>
        <div class="stat"><div class="stat-val" style="color:{lpc(gs.lp_satisfaction)};">{gs.lp_satisfaction}</div>
          <div class="stat-lbl">LP Score</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Paths breakdown
    st.markdown("<h2 style='text-align:center;'>Win Paths</h2>", unsafe_allow_html=True)
    for key, p in paths.items():
        css = "path-hit" if p["hit"] else "path-miss"
        tick = "✅" if p["hit"] else "◻️"
        st.markdown(f"""
        <div class="{css}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="fw7">{tick} {p['label']}</span>
            <span class="c-muted" style="font-size:.82rem;">{p['desc']}</span>
            <span class="fw7" style="color:{'var(--green)' if p['hit'] else 'var(--muted)'};">
              {p['actual']} {'✓' if p['hit'] else f"/ {p['target']}"}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # Fund II unlock card
    next_cash = DIFFICULTY[gs.difficulty]["cash"] * unlock["cash_mult"] * gs.fund_cash_mult
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="unlock-card">
      <div style="font-size:.72rem;color:var(--gold);font-weight:700;text-transform:uppercase;
           letter-spacing:.07em;margin-bottom:.4rem;">{'🔓 Unlocked' if fn < 3 else '🏆 Endgame'}</div>
      <h2 style="margin:0;color:var(--gold);">
        {unlock['fund']} — {cf(next_cash)} capital</h2>
      <p style="font-size:.88rem;margin:.5rem 0 0;">{unlock['flavor']}</p>
    </div>""", unsafe_allow_html=True)

    if gs.exited:
        st.markdown("<h2 style='text-align:center;margin-top:1.25rem;'>Deal Recap</h2>",
                    unsafe_allow_html=True)
        for e in sorted(gs.exited, key=lambda x: -x["moic"]):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:.55rem .9rem;
                 background:var(--card);border-radius:10px;margin-bottom:.3rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong>
                <span class="c-muted" style="font-size:.73rem;"> (CEO: {e['ceo']})</span></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        next_label = f"Start {unlock['fund']} →" if fn < 3 else "🔄 New Fund"
        if st.button(next_label, use_container_width=True):
            if fn < 3:
                # Carry over unlocks into the next fund
                new_gs = GameState(
                    screen="game",
                    difficulty=gs.difficulty,
                    cash=next_cash,
                    lp_satisfaction=min(100, DIFFICULTY[gs.difficulty]["lp_start"] + unlock["lp_bonus"]),
                    firm_name=gs.firm_name,
                    partner_name=gs.partner_name,
                    fund_number=fn + 1,
                    fund_cash_mult=unlock["cash_mult"] * gs.fund_cash_mult,
                    fund_lp_bonus=gs.fund_lp_bonus + unlock["lp_bonus"],
                    rival=gs.rival,   # same rival carries over
                )
                new_gs.deals = make_deals(new_gs, 5)
                st.session_state.gs = new_gs
            else:
                del st.session_state["gs"]
            st.rerun()
    with c3:
        if st.button("🔄 New Game", use_container_width=True):
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
