"""
CarryForge v11.0
================
- CRASH FIX: AttributeError sound_queue missing from old sessions → G() migration
- API FIX: st.components.v1.html → st.iframe (Streamlit 1.58)
- API FIX: use_container_width removed (CSS handles full-width)
- LAYOUT: Desktop shows ALL sections in one scroll (no tabs).
          Mobile keeps BitLife bottom nav + single-section focus.
- SOUND: window.parent injection still works; iframe height=1 (not 0)
"""

import streamlit as st
import numpy as np
import random
from dataclasses import dataclass, field

st.set_page_config(page_title="CarryForge", page_icon="💼",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────
# CSS  — v12 design: Space Grotesk · Neon Vault
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@700&display=swap');

:root {
  /* surfaces */
  --bg:   #060810;
  --s1:   #0c1020;
  --s2:   #121828;
  --s3:   #1a2235;
  /* accents */
  --lime: #4ade80;
  --gold: #fbbf24;
  --red:  #f87171;
  --blue: #60a5fa;
  --pur:  #a78bfa;
  --pink: #f472b6;
  --teal: #34d399;
  /* meta */
  --border:     rgba(255,255,255,.055);
  --border-lit: rgba(255,255,255,.13);
  --text:  #e2e8f0;
  --muted: #64748b;
  --dim:   #374151;
  /* sector gradients (bg overlays) */
  --saas-glow:   rgba(96,165,250,.08);
  --hw-glow:     rgba(167,139,250,.08);
  --health-glow: rgba(244,114,182,.08);
  --fin-glow:    rgba(52,211,153,.08);
}

*, *::before, *::after {
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

html,body,.stApp { background: var(--bg) !important; color: var(--text); }
#MainMenu,footer,header { visibility:hidden; }

/* layout */
.block-container { padding:.85rem 1.1rem 5.5rem; max-width:980px; margin:0 auto; }
@media (min-width:900px){
  .block-container { padding:1.25rem 2.5rem 2.5rem !important; max-width:1340px !important; }
  #_cf_nav { display:none !important; }
}
@media (max-width:899px){
  .desktop-section          { display:none !important; }
  .desktop-section.cf-active{ display:block !important; }
}

div[data-testid="stTextInput"] { display:none !important; }

/* ── typography ── */
h1 { font-size:1.55rem; font-weight:800; margin:0; letter-spacing:-.02em; }
h2 { font-size:1.05rem; font-weight:700; margin:.9rem 0 .45rem; letter-spacing:-.01em; }
h3 { font-size:.92rem;  font-weight:700; margin:0; }
hr { border-color: var(--border); margin:.75rem 0; }

/* ── primary button ── */
.stButton > button {
  background: linear-gradient(135deg, var(--lime), #22c55e) !important;
  color: #052e16 !important;
  border: none !important;
  border-radius: 999px;
  font-weight: 800 !important;
  font-size: .85rem !important;
  letter-spacing: .01em;
  padding: .6rem 1.4rem !important;
  width: 100%;
  transition: transform .12s, box-shadow .12s, opacity .12s;
  box-shadow: 0 0 0 0 rgba(74,222,128,0);
  position: relative; overflow: hidden;
}
.stButton > button::after {
  content:''; position:absolute; top:0; left:-75%;
  width:50%; height:100%;
  background: linear-gradient(90deg,transparent,rgba(255,255,255,.28),transparent);
  transition: left .5s ease;
}
.stButton > button:hover { transform:translateY(-2px); box-shadow:0 4px 22px rgba(74,222,128,.35); }
.stButton > button:hover::after { left:140%; }
.stButton > button:disabled {
  background: var(--s2) !important;
  color: var(--muted) !important;
  box-shadow: none !important;
  transform: none !important;
}

/* ── choice buttons (event options) ── */
.choice-btn > div > div > button {
  background: var(--s2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-lit) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
  font-weight: 600 !important;
  text-align: left !important;
}
.choice-btn > div > div > button:hover {
  border-color: var(--lime) !important;
  color: var(--lime) !important;
  transform: none !important;
}

/* ── stat block ── */
.num {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -.03em;
  font-feature-settings: "tnum";
}
.num-sm {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1.2rem;
  font-weight: 700;
  font-feature-settings: "tnum";
}
.lbl {
  font-size: .62rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-top: .2rem;
}

/* ── pill / stat card ── */
.pill-card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1rem 1.25rem;
  text-align: center;
}

/* ── deal / portfolio card ── */
.card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1rem 1.1rem;
  margin-bottom: .5rem;
  transition: border-color .2s;
}
.card:hover { border-color: var(--border-lit); }
.card-saas   { background: linear-gradient(135deg,var(--saas-glow),var(--s1)  80%); }
.card-hw     { background: linear-gradient(135deg,var(--hw-glow),  var(--s1)  80%); }
.card-health { background: linear-gradient(135deg,var(--health-glow),var(--s1) 80%); }
.card-fin    { background: linear-gradient(135deg,var(--fin-glow),  var(--s1)  80%); }

.sector-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 5px;
  vertical-align: middle;
}

/* ── chip / tag ── */
.chip {
  display: inline-block;
  background: var(--s2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: .2rem .65rem;
  font-size: .7rem;
  font-weight: 600;
  color: var(--muted);
  margin: 2px;
}
.chip b { color: var(--text); font-weight: 700; }
.chip-hot   { border-color: var(--gold); color: var(--gold); background: rgba(251,191,36,.08); }
.chip-risky { border-color: var(--red);  color: var(--red);  background: rgba(248,113,113,.08); }

/* ── path chips ── */
.path-pill {
  display: inline-flex; align-items: center; gap: .3rem;
  border-radius: 999px; padding: .28rem .75rem;
  font-size: .72rem; font-weight: 700;
  border: 1px solid; margin: 2px;
}
.pp-hit    { background:rgba(74,222,128,.12); border-color:var(--lime); color:var(--lime); }
.pp-miss   { background:var(--s2);           border-color:var(--border); color:var(--muted); }
.pp-ahead  { background:rgba(74,222,128,.07); border-color:rgba(74,222,128,.3); color:#86efac; }
.pp-behind { background:rgba(248,113,113,.07);border-color:rgba(248,113,113,.3);color:#fca5a5; }

/* ── LP bar ── */
.lp-row { display:flex; align-items:center; gap:.6rem; margin:.4rem 0; }
.lp-track {
  flex:1; height:10px;
  background: linear-gradient(90deg,rgba(74,222,128,.15) 0%,rgba(251,191,36,.15) 50%,rgba(248,113,113,.15) 100%);
  border-radius:999px; overflow:hidden; position:relative;
}
.lp-fill { height:10px; border-radius:999px; transition:width .5s ease; }

/* ── event cards ── */
.ev {
  border-radius: 20px;
  padding: 1.25rem 1.4rem;
  margin: .5rem 0;
  border: 1px solid;
}
.ev-crisis      { background:rgba(248,113,113,.07); border-color:rgba(248,113,113,.3); }
.ev-opportunity { background:rgba(74,222,128,.07);  border-color:rgba(74,222,128,.3);  }
.ev-rival       { background:rgba(167,139,250,.07); border-color:rgba(167,139,250,.3); }
.ev-lp          { background:rgba(251,191,36,.07);  border-color:rgba(251,191,36,.3);  }
.ev-season      { background:rgba(96,165,250,.07);  border-color:rgba(96,165,250,.3);  }

/* ── score / unlock cards ── */
.score-card {
  background: linear-gradient(135deg,var(--s2),var(--s1));
  border: 1px solid var(--border-lit);
  border-radius: 24px;
  padding: 2rem 1.75rem;
  text-align: center;
  max-width: 520px;
  margin: .75rem auto;
}
.unlock-card {
  background: linear-gradient(135deg,rgba(251,191,36,.08),var(--s1));
  border: 1px solid rgba(251,191,36,.25);
  border-radius: 18px;
  padding: 1.1rem;
  text-align: center;
  margin: .5rem 0;
}
.path-row-hit  { background:rgba(74,222,128,.08); border:1px solid rgba(74,222,128,.3);
                 border-radius:12px; padding:.55rem 1rem; margin:.25rem 0; }
.path-row-miss { background:var(--s2); border:1px solid var(--border);
                 border-radius:12px; padding:.55rem 1rem; margin:.25rem 0; opacity:.5; }

/* ── season labels ── */
.s1c { color:#4ade80; font-weight:700; }
.s2c { color:#fbbf24; font-weight:700; }
.s3c { color:#f87171; font-weight:700; }

/* ── hint box ── */
.hint {
  background: rgba(96,165,250,.07);
  border: 1px solid rgba(96,165,250,.22);
  border-radius: 14px;
  padding: .7rem 1rem;
  font-size: .84rem;
  color: #93c5fd;
  margin: .5rem 0;
}

/* ── log line ── */
.log { padding:.4rem .85rem; background:var(--s2); border-radius:10px;
       font-size:.79rem; color:var(--muted); margin:.2rem 0; }

/* ── color helpers ── */
.g  { color:var(--lime) !important; font-weight:700; }
.go { color:var(--gold) !important; font-weight:700; }
.r  { color:var(--red)  !important; font-weight:700; }
.mu { color:var(--muted)!important; }
.b7 { font-weight:700; }

/* ── section divider ── */
.sec-head {
  display: flex; align-items: center; gap: .6rem;
  margin: 1.25rem 0 .6rem;
}
.sec-head-line {
  flex:1; height:1px;
  background: linear-gradient(90deg,var(--border),transparent);
}

@media(max-width:640px){
  .block-container{padding:.7rem .7rem 5.5rem;}
  .num{font-size:1.4rem;}
  h1{font-size:1.3rem;}
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
MAX_PORTFOLIO = 4

SEASONS = {
    1:{"name":"Bull Run","emoji":"🟢","css":"s1","exit_mod":1.15,"growth_mod":1.10,
       "title":"The Bull Is Running",
       "text":"Rates near zero. Every growth equity fund in NYC has more capital than ideas. Sellers know it."},
    2:{"name":"The Turn","emoji":"🟡","css":"s2","exit_mod":1.00,"growth_mod":0.95,
       "title":"The Market Has Turned",
       "text":"Easy money is gone. Buyers are more selective. Your LPs have started CC'ing their advisors."},
    3:{"name":"The Reckoning","emoji":"🔴","css":"s3","exit_mod":0.85,"growth_mod":0.88,
       "title":"Batten Down the Hatches",
       "text":"Rates up 300bps. Debt markets nearly closed. Companies that haven't exited are sitting a while longer."},
}
SECTORS = {
    "SaaS":      {"emoji":"💻","rev":(40,160),"margin":(.28,.48),"growth":(.12,.32)},
    "Hardware":  {"emoji":"🔧","rev":(90,300),"margin":(.08,.18),"growth":(.04,.14)},
    "Healthcare":{"emoji":"🏥","rev":(70,240),"margin":(.14,.28),"growth":(.08,.22)},
    "Fintech":   {"emoji":"💰","rev":(35,120),"margin":(.22,.42),"growth":(.22,.48)},
}
CEO_NAMES = [
    "Marcus Webb","Priya Sharma","Derek Lund","Sophie Chen","Raj Patel","Chloe Kim",
    "Jake Torres","Nadia Okafor","Ben Holt","Mei Lin","Aaron Voss","Tara Flynn",
    "Luis Reyes","Iris Park","Owen Grant","Valentina Cruz","Sam Adeyemi","Petra Novak",
]
COMPANY_NAMES = {
    "SaaS":      ["CloudVault","DataFlow","SyncHub","AutoScale","SnapMetrics","PipelineAI","GridLogic","NovaDash"],
    "Hardware":  ["TechWorks","PrecisionCo","SmartBuild","CoreForge","IronStack","PeakSystems","NexHardware","OrbDrive"],
    "Healthcare":["HealthPlus","CareFlow","MedTech","PulseCare","BioServe","ClearMed","VitalPath","RxBridge"],
    "Fintech":   ["PayHub","TradeFlow","VaultSecure","ClearPay","LedgerX","SwiftBridge","CapitalOps","NovaMoney"],
}
RIVAL_FIRMS = [
    {"name":"Apex Capital","emoji":"🦅"},{"name":"Redwood PE","emoji":"🌲"},
    {"name":"Meridian Partners","emoji":"🐍"},{"name":"Pinnacle Fund","emoji":"🏔"},
]
LP_NAMES = ["Westfield Endowment","CalPERS West","Hartley Family Office","Atlas Foundation"]
FIRM_DEFAULTS = ["Genesis Capital","Ironwood Partners","Crestview Equity","Summit PE","Clarendon Fund"]

NARRATIVE_EVENTS = [
    {"id":"ceo_offer","type":"crisis","title":"Your CEO Got Poached","icon":"😬",
     "template":"**{ceo}** — CEO of {co} — got a $2.4M offer from {rival}. Called you from their kid's school parking lot.",
     "choices":[{"label":"Counter with a 2% equity stake","effect":"ceo_stays"},
                {"label":"Match their salary, nothing else","effect":"ceo_leaves_slow"},
                {"label":"Wish them luck and start interviewing","effect":"ceo_gone"}]},
    {"id":"ceo_arrested","type":"crisis","title":"Legal Situation","icon":"🚔",
     "template":"CEO of {co}, **{ceo}**, was arrested this morning. 'Unrelated to the business,' apparently. SEC says otherwise.",
     "choices":[{"label":"Terminate immediately, full PR blackout","effect":"ceo_gone_clean"},
                {"label":"Hire a crisis lawyer, ride it out","effect":"crisis_managed"},
                {"label":"Publicly back them — they said they're innocent","effect":"disaster"}]},
    {"id":"major_customer","type":"opportunity","title":"Enterprise Deal","icon":"🤝",
     "template":"{co} got an LOI from a Fortune 50 — $12M ARR, adds ~30% revenue overnight.",
     "choices":[{"label":"Staff up fast — hire 40 people","effect":"big_growth"},
                {"label":"Sign it, figure out delivery later","effect":"medium_growth"},
                {"label":"Pass — too much execution risk","effect":"nothing"}]},
    {"id":"customer_churn","type":"crisis","title":"Client Just Walked","icon":"💨",
     "template":"{co}'s **largest customer** — 18% of ARR — terminated. Their new CFO called you 'a nice experiment.'",
     "choices":[{"label":"Fly out, offer a discount to stay","effect":"partial_save"},
                {"label":"Accept it and focus on pipeline","effect":"slight_hit"},
                {"label":"Sue for breach of contract","effect":"war"}]},
    {"id":"rival_bid","type":"rival","title":"Competing Bid","icon":"😤",
     "template":"**{rival}** submitted a competing bid for {co} — $8M over your offer. Using leverage you'd never touch.",
     "choices":[{"label":"Walk away — you have discipline","effect":"lose_deal"},
                {"label":"Match their price, tighten terms","effect":"win_expensive"},
                {"label":"Go lower, pitch your operational value","effect":"win_clever"}]},
    {"id":"rival_email","type":"rival","title":"Interesting Email","icon":"📧",
     "template":"Email from **{rival}**: *'Heard you picked up {co}. Brave choice given the cap table. Let us know when you're ready to recap.'*",
     "choices":[{"label":"Reply with a screenshot of your DPI","effect":"rivalry_up"},
                {"label":"Ignore it","effect":"nothing"},
                {"label":"Forward to your LP — let them laugh","effect":"lp_amused"}]},
    {"id":"lp_call","type":"lp","title":"LP on Line 1","icon":"📞",
     "template":"**{lp}** is calling. Again. DPI still 0x. 'Have you considered your exit timeline?' Call in 15 minutes.",
     "choices":[{"label":"Take it, promise a Q3 exit","effect":"pressure_sell"},
                {"label":"Send deck — 'pipeline is strong'","effect":"bought_time"},
                {"label":"Have your associate take it","effect":"lp_annoyed"}]},
    {"id":"lp_pullout","type":"lp","title":"LP Threatening to Withdraw","icon":"🚨",
     "template":"**{lp}** needs liquidity. Threatening to sell their stake at a 30% discount.",
     "choices":[{"label":"Orchestrate a dividend recap","effect":"lp_happy_hit"},
                {"label":"Help them find a secondary buyer","effect":"lp_exits"},
                {"label":"Call their bluff","effect":"lp_furious"}]},
    {"id":"unsolicited_bid","type":"opportunity","title":"Someone Wants to Buy","icon":"💸",
     "template":"Strategic buyer: unsolicited offer for {co} at 35% premium. Answer by Friday.",
     "choices":[{"label":"Sell — take the money","effect":"forced_exit"},
                {"label":"Run a full process, see who bids","effect":"auction"},
                {"label":"Decline — you're just getting started","effect":"nothing"}]},
    {"id":"add_on","type":"opportunity","title":"Bolt-On Opportunity","icon":"🧩",
     "template":"{co} found a smaller competitor for $8M. Tuck-in adds 15% revenue. CEO is excited.",
     "choices":[{"label":"Fund it","effect":"addon_win"},
                {"label":"Pass — keep management focused","effect":"nothing"},
                {"label":"Negotiate lower first","effect":"addon_maybe"}]},
    {"id":"rate_shock","type":"crisis","title":"Rate Shock","icon":"📉",
     "template":"Fed raised 75bps. Debt cost up $2M/year. Blackstone sent 'Navigating the New Normal.' You deleted it.",
     "choices":[{"label":"Refinance early on best company","effect":"rate_hedged"},
                {"label":"Accelerate exits","effect":"pressure_sell"},
                {"label":"Weather it","effect":"slight_hit"}]},
    {"id":"sector_boom","type":"opportunity","title":"Your Sector Is Hot","icon":"🔥",
     "template":"{co}'s sector on the cover of Fortune. Exit multiples up 2× from a year ago.",
     "choices":[{"label":"Exit now while multiples are peak","effect":"forced_exit"},
                {"label":"Hold for the wave","effect":"risky_hold"},
                {"label":"Use hype to recruit a tier-1 CEO","effect":"ceo_upgrade"}]},
]
EFFECTS = {
    "ceo_stays":{"moic_delta":+.20,"msg":"CEO stayed. Equity vesting updated. Seem pleased."},
    "ceo_leaves_slow":{"moic_delta":-.10,"msg":"They took it. 90 days."},
    "ceo_gone":{"moic_delta":-.25,"msg":"CEO out. Search firm on retainer. Team nervous."},
    "ceo_gone_clean":{"moic_delta":-.20,"msg":"Terminated. Legal risk contained. Business wobbling."},
    "crisis_managed":{"moic_delta":-.10,"msg":"Charges reduced. Optics still your problem."},
    "disaster":{"moic_delta":-.40,"msg":"SEC subpoenas arrived Friday afternoon."},
    "big_growth":{"moic_delta":+.30,"msg":"Bold bet paid. Revenue +28%. CEO is insufferable."},
    "medium_growth":{"moic_delta":+.15,"msg":"Bumpy delivery. Contract held. Client renewed last minute."},
    "nothing":{"moic_delta":.00,"msg":"Status quo. Deck identical to last quarter."},
    "partial_save":{"moic_delta":-.08,"msg":"12-month extension. They're still going to leave."},
    "slight_hit":{"moic_delta":-.12,"msg":"Revenue down 18%. Pipeline 'robust' apparently."},
    "war":{"moic_delta":-.30,"msg":"Litigation expensive. Distraction worse."},
    "lose_deal":{"moic_delta":.00,"msg":"Deal lost. You walk out saying 'discipline.'"},
    "win_expensive":{"moic_delta":-.05,"msg":"Won it. Paid over market. Model needs a hero exit."},
    "win_clever":{"moic_delta":+.08,"msg":"Seller picked you over the higher bid."},
    "rivalry_up":{"moic_delta":.00,"msg":"They didn't reply. Probably furious."},
    "lp_amused":{"lp_delta":+5,"msg":"LP laughed. Said 'these guys.' Good relationship."},
    "pressure_sell":{"force_exit":True,"msg":"You committed to an exit. Now deliver."},
    "bought_time":{"lp_delta":-3,"msg":"Accepted the deck. Called again 3 weeks later."},
    "lp_annoyed":{"lp_delta":-10,"msg":"Associate took it. LP is 63, in PE since before you were born."},
    "lp_happy_hit":{"moic_delta":-.05,"lp_delta":+10,"msg":"LP placated. Small leverage hit."},
    "lp_exits":{"lp_delta":-20,"msg":"LP sold at 35% discount. New holder emails weekly."},
    "lp_furious":{"lp_delta":-25,"msg":"Called the bluff. Personally calling every LP this Friday night."},
    "forced_exit":{"force_exit":True,"msg":"Company going to market. Time to find out your IRR."},
    "auction":{"moic_delta":+.12,"msg":"Four bidders showed. Extracted another 18%."},
    "rate_hedged":{"moic_delta":+.05,"msg":"Locked in 6.2% for 5 years."},
    "risky_hold":{"moic_delta":+.10,"msg":"Wave didn't come. Multiple contracted 15%."},
    "ceo_upgrade":{"moic_delta":+.15,"msg":"Hired ex-Stripe COO. Restructured sales week one."},
    "addon_win":{"moic_delta":+.15,"msg":"Tuck-in closed. Customer cross-sell working."},
    "addon_maybe":{"moic_delta":+.05,"msg":"They came back 20% lower. Signed same afternoon."},
}
DIFFICULTY = {
    "Easy":    {"cash":60e6,"exit_mult":9.5,"quarters":12,"lp_start":80,"paths":{"moic":1.5,"lp":70,"exits":3}},
    "Balanced":{"cash":50e6,"exit_mult":8.5,"quarters":12,"lp_start":65,"paths":{"moic":1.75,"lp":65,"exits":4}},
    "Hard":    {"cash":40e6,"exit_mult":7.5,"quarters":12,"lp_start":50,"paths":{"moic":2.0,"lp":60,"exits":5}},
}
UNLOCKS = {
    0:{"fund":"Fund II","cash_mult":1.0,"lp_bonus":0,"flavor":"Same terms. LPs giving you one more shot."},
    1:{"fund":"Fund II","cash_mult":1.3,"lp_bonus":8,"flavor":"One path hit. LPs interested. Modest step up."},
    2:{"fund":"Fund II","cash_mult":1.6,"lp_bonus":15,"flavor":"Two paths hit. Strong showing. Real upgrade."},
    3:{"fund":"Fund II","cash_mult":2.0,"lp_bonus":25,"flavor":"All three. LPs fighting over allocation. Fund III on the table."},
}

# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────
@dataclass
class Company:
    id:str; name:str; sector:str; ceo:str
    revenue:float; ebitda:float; margin:float; growth:float
    entry_multiple:float; entry_ev:float; entry_debt:float; entry_equity:float
    entry_quarter:int=0; moic_modifier:float=1.0; tier:str="standard"

@dataclass
class GameState:
    screen:str="start"; difficulty:str="Balanced"; quarter_num:int=0; cash:float=50e6
    firm_name:str=""; partner_name:str=""; fund_number:int=1
    fund_cash_mult:float=1.0; fund_lp_bonus:int=0
    companies:list=field(default_factory=list); exited:list=field(default_factory=list)
    deals:list=field(default_factory=list); pending_event:dict=field(default_factory=dict)
    event_log:list=field(default_factory=list); lp_satisfaction:int=65
    rival:dict=field(default_factory=dict); exit_mult_mod:float=1.0
    growth_mod:float=1.0; sector_mods:dict=field(default_factory=dict)
    forced_exit_id:str=""; season_shown:int=0
    sound_queue:list=field(default_factory=list)

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

# ─────────────────────────────────────────────
# GAME LOGIC
# ─────────────────────────────────────────────
def make_deals(gs:GameState, n:int=5) -> list:
    used = {c.name for c in gs.companies}
    deals = []
    for _ in range(n):
        sector = random.choice(list(SECTORS))
        p = SECTORS[sector]
        rev=np.random.uniform(*p["rev"]); mg=np.random.uniform(*p["margin"])
        eb=rev*mg; gr=np.random.uniform(*p["growth"])
        em=round(np.random.uniform(6.5,9.5),1)
        ev=eb*em; debt=eb*np.random.uniform(3.0,5.0); eq=max(ev-debt,ev*0.10)
        pool=[n for n in COMPANY_NAMES[sector] if n not in used] or COMPANY_NAMES[sector]
        name=random.choice(pool); used.add(name)
        score=gr*0.6+mg*0.4
        tier="hot" if score>0.22 and em<8.0 else ("risky" if em>8.8 or mg<0.10 else "standard")
        deals.append(Company(id=f"{name[:3]}{random.randint(100,999)}",name=name,sector=sector,
            ceo=random.choice(CEO_NAMES),revenue=rev,ebitda=eb,margin=mg,growth=gr,
            entry_multiple=em,entry_ev=ev,entry_debt=debt,entry_equity=eq,
            entry_quarter=gs.quarter_num,tier=tier))
    return deals

def calc(c:Company, gs:GameState) -> dict:
    qh=gs.quarter_num-c.entry_quarter; yh=qh/4.0
    si=gs.season_info; sm=gs.sector_mods.get(c.sector,1.0)
    mature_yrs=max(qh-8,0)/4.0
    eg=c.growth*gs.growth_mod*sm*si["growth_mod"]*((1-.08)**mature_yrs)
    debt=c.entry_debt
    for yr in range(1,int(yh)+1):
        my=max((yr*4-8)/4,0)
        y_eg=c.growth*gs.growth_mod*sm*si["growth_mod"]*((1-.08)**my)
        yr_e=c.revenue*((1+y_eg)**yr)*c.margin
        debt=max(debt-max(yr_e*0.55-debt*0.065,0)*0.35,0)
    rev=c.revenue*((1+eg)**yh); ebitda=rev*c.margin
    pm=0.88+yh*0.12 if yh<1.0 else (1.0+(yh-1.0)*0.05 if yh<=3.0 else 1.10-(yh-3.0)*0.05)
    em=DIFFICULTY[gs.difficulty]["exit_mult"]*gs.exit_mult_mod*sm*pm*si["exit_mod"]
    equity=max(ebitda*em-debt,0)*max(c.moic_modifier,.1)
    moic=max(equity/max(c.entry_equity,1), 0.95 if yh<0.25 else 0)
    irr=(moic**(1/max(yh,.25))-1) if yh>0 else 0
    return {"revenue":rev,"ebitda":ebitda,"equity":equity,"debt":debt,
            "moic":moic,"irr":irr,"yh":yh,"pm":pm}

def blended_moic(gs:GameState) -> float:
    ti=sum(c.entry_equity for c in gs.companies)+sum(e["eq"] for e in gs.exited)
    to=sum(calc(c,gs)["equity"] for c in gs.companies)*0.70+sum(e["proc"] for e in gs.exited)
    return to/max(ti,1)

def proj3(d:Company,gs:GameState) -> float:
    r3=d.revenue*((1+d.growth)**3); eb3=r3*d.margin; debt=d.entry_debt
    for yr in range(1,4):
        yr_e=d.revenue*((1+d.growth)**yr)*d.margin
        debt=max(debt-max(yr_e*0.55-debt*0.065,0)*0.35,0)
    return max(eb3*DIFFICULTY[gs.difficulty]["exit_mult"]*1.10-debt,0)/max(d.entry_equity,1)

def check_paths(gs:GameState) -> dict:
    cfg=DIFFICULTY[gs.difficulty]["paths"]; bm=blended_moic(gs)
    q=max(gs.quarter_num,1); tot=gs.total_quarters
    return {
        "returns":{"hit":bm>=cfg["moic"],"target":cfg["moic"],"actual":round(bm,2),
                   "label":"💰 Returns","desc":f"Hit {cfg['moic']}× MOIC",
                   "pace":"ahead" if bm/cfg["moic"]/(q/tot)>1.1 else ("behind" if bm/cfg["moic"]/(q/tot)<0.7 else "ok")},
        "lp":{"hit":gs.lp_satisfaction>=cfg["lp"],"target":cfg["lp"],"actual":gs.lp_satisfaction,
              "label":"🤝 LP Legend","desc":f"Keep LPs ≥{cfg['lp']}","pace":"ahead" if gs.lp_satisfaction>=cfg["lp"] else "behind"},
        "exits":{"hit":len(gs.exited)>=cfg["exits"],"target":cfg["exits"],"actual":len(gs.exited),
                 "label":"🏆 Deal Maker","desc":f"{cfg['exits']}+ exits",
                 "pace":"ahead" if len(gs.exited)/cfg["exits"]/(q/tot)>1.0 else "behind"},
    }

def sell_company(gs:GameState, idx:int) -> dict:
    c=gs.companies[idx]; m=calc(c,gs)
    gs.cash+=m["equity"]
    gs.exited.append({"name":c.name,"sector":c.sector,"ceo":c.ceo,
                      "moic":m["moic"],"irr":m["irr"],"proc":m["equity"],"eq":c.entry_equity,"yh":m["yh"]})
    gs.companies.pop(idx)
    gs.lp_satisfaction=min(100,gs.lp_satisfaction+8)
    gs.event_log.insert(0,f"Exited {c.name} at {m['moic']:.2f}×.")
    gs.event_log=gs.event_log[:6]
    return m

def pick_event(gs:GameState):
    if not gs.companies: return None
    pool=[e for e in NARRATIVE_EVENTS if e["type"] in ("crisis","opportunity")]
    pool+=[e for e in NARRATIVE_EVENTS if e["type"]=="rival"]
    if not gs.exited and gs.quarter_num>3:
        pool+=[e for e in NARRATIVE_EVENTS if e["type"]=="lp"]*3
    if not pool: return None
    ev=random.choice(pool); co=random.choice(gs.companies)
    text=ev["template"]
    text=text.replace("{co}",f"**{co.name}**").replace("{ceo}",co.ceo)
    text=text.replace("{rival}",gs.rival.get("name","a rival"))
    text=text.replace("{lp}",random.choice(LP_NAMES))
    return {"id":ev["id"],"type":ev["type"],"title":ev["title"],"icon":ev["icon"],
            "text":text,"choices":ev["choices"],"cid":co.id}

def apply_effect(gs:GameState, key:str, cid:str|None):
    eff=EFFECTS.get(key,EFFECTS["nothing"])
    if cid:
        for c in gs.companies:
            if c.id==cid:
                if "moic_delta" in eff: c.moic_modifier=max(.1,min(c.moic_modifier+eff["moic_delta"],3.0))
                if eff.get("force_exit"): gs.forced_exit_id=c.id
                break
    if "lp_delta" in eff: gs.lp_satisfaction=max(0,min(100,gs.lp_satisfaction+eff["lp_delta"]))
    gs.event_log.insert(0,eff["msg"]); gs.event_log=gs.event_log[:6]

def advance_quarter(gs:GameState):
    prev=gs.season; gs.quarter_num+=1
    gs.sound_queue.append("TICK")
    if not gs.exited and gs.quarter_num>3: gs.lp_satisfaction=max(0,gs.lp_satisfaction-3)
    gs.deals=make_deals(gs,5)
    if gs.quarter_num>=gs.total_quarters: gs.screen="score"; return
    new=gs.season
    if new!=prev and gs.season_shown<new:
        gs.season_shown=new; si=SEASONS[new]
        gs.sound_queue.append("SEASON")
        gs.pending_event={"id":f"season_{new}","type":"season","title":si["title"],
            "icon":si["emoji"],"text":si["text"],
            "choices":[{"label":"Got it. Keep moving.","effect":"nothing"}],"cid":None}
        return
    if random.random()<0.60:
        ev=pick_event(gs)
        if ev:
            gs.pending_event=ev
            gs.sound_queue.append({"crisis":"CRISIS","opportunity":"OPPORTUNITY","rival":"RIVAL","lp":"LP"}.get(ev["type"],"TICK"))

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
def G() -> GameState:
    if "gs" not in st.session_state:
        st.session_state.gs = GameState()
    gs = st.session_state.gs
    # Migrate old sessions that predate new fields
    if not hasattr(gs, "sound_queue"): gs.sound_queue = []
    if not hasattr(gs, "season_shown"): gs.season_shown = 0
    if not hasattr(gs, "forced_exit_id"): gs.forced_exit_id = ""
    return gs

def get_tab() -> str:
    return st.session_state.get("tab","home")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def mc(v):   return "g"  if v>=2.0 else "go" if v>=1.3 else "r"
def cf(v):   return f"${v/1e9:.2f}B" if abs(v)>=1e9 else f"${v/1e6:.1f}M"
def lpc(s):  return "#4ade80" if s>=60 else "#fbbf24" if s>=35 else "#f87171"
def hdot(m): return "🟢" if m>=1.10 else ("🔴" if m<=0.85 else "🟡")

SECTOR_CSS = {"SaaS":"card-saas","Hardware":"card-hw","Healthcare":"card-health","Fintech":"card-fin"}
SECTOR_DOT = {"SaaS":"#60a5fa","Hardware":"#a78bfa","Healthcare":"#f472b6","Fintech":"#34d399"}

# ─────────────────────────────────────────────
# SOUND + BOTTOM NAV
# st.iframe (Streamlit 1.58 replacement for components.html)
# Iframe JS uses window.parent to access main page AudioContext
# ─────────────────────────────────────────────
_AUDIO_JS = r"""
window._cfPlay = function(snd) {
  try {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    var ctx = new AC();
    if (ctx.state === 'suspended') ctx.resume();
    var t = ctx.currentTime;
    function tone(f, type, t0, dur, vol, detune) {
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type = type || 'sine'; o.frequency.value = f;
      if (detune) o.detune.value = detune;
      g.gain.setValueAtTime(0, t0);
      g.gain.linearRampToValueAtTime(vol || 0.22, t0 + 0.012);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      o.start(t0); o.stop(t0 + dur + 0.05);
    }
    if (snd === 'BUY') {
      tone(880,'sine',t,0.18,0.22); tone(1320,'sine',t+0.09,0.18,0.18); tone(1760,'sine',t+0.17,0.14,0.12);
    } else if (snd === 'SELL_GREAT') {
      [523,659,784,1047].forEach(function(f,i){tone(f,'sine',t+i*0.10,0.26,0.22);});
      tone(1047,'sine',t+0.45,0.35,0.16);
    } else if (snd === 'SELL_OK') {
      tone(660,'sine',t,0.18,0.22); tone(880,'sine',t+0.10,0.20,0.17);
    } else if (snd === 'SELL_BAD') {
      [400,330,260].forEach(function(f,i){tone(f,'triangle',t+i*0.12,0.22,0.16);});
    } else if (snd === 'TICK') {
      tone(700,'sine',t,0.06,0.10); tone(1000,'sine',t+0.04,0.05,0.07);
    } else if (snd === 'CRISIS') {
      tone(220,'sawtooth',t,0.14,0.16); tone(196,'sawtooth',t+0.12,0.18,0.13,-10);
    } else if (snd === 'OPPORTUNITY') {
      tone(1100,'sine',t,0.10,0.18); tone(1320,'sine',t+0.07,0.13,0.14);
    } else if (snd === 'SEASON') {
      [130,164,196,246].forEach(function(f,i){tone(f,'sine',t+i*0.08,0.55,0.13);});
    } else if (snd === 'RIVAL') {
      [500,400,320].forEach(function(f,i){tone(f,'sawtooth',t+i*0.09,0.18,0.11);});
    } else if (snd === 'LP') {
      tone(740,'square',t,0.10,0.09); tone(740,'square',t+0.18,0.10,0.09);
    } else if (snd === 'VICTORY') {
      [523,659,784,1047,784,1047,1319].forEach(function(f,i){tone(f,'sine',t+i*0.09,0.28,0.20);});
    } else if (snd === 'GRADE_C') {
      [350,300,250,230].forEach(function(f,i){tone(f,'sawtooth',t+i*0.14,0.25,0.13);});
    }
    setTimeout(function(){try{ctx.close();}catch(e){}}, 2600);
  } catch(e) {}
};
"""

def flush_sounds(gs: GameState, extra: str = ""):
    """Play queued sounds via st.iframe (Streamlit 1.58 API)."""
    snds = list(getattr(gs, "sound_queue", []))
    if extra: snds.append(extra)
    gs.sound_queue = []
    if not snds: return
    # Build calls string — run in parent frame via window.parent
    calls = "".join(f"window.parent._cfPlay('{s}');" for s in snds)
    import base64, random as _r
    html = f"""
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
    """
    b64 = base64.b64encode(html.encode()).decode()
    st.iframe(f"data:text/html;base64,{b64}", height=1, scrolling=False)


def inject_bottom_nav(active_tab:str, has_event:bool=False):
    """Inject a persistent BitLife-style bottom nav bar into window.parent."""
    tabs = [
        ("home",      "🏠", "Home"),
        ("deals",     "🎯", "Deals"),
        ("portfolio", "📊", "Portfolio"),
        ("events",    "📣", "Events"),
        ("fund",      "💰", "Fund"),
    ]
    nav_items_js = str([(k, i, l) for k,i,l in tabs])
    active_js = active_tab
    badge_js = "true" if has_event else "false"

    import base64, random as _r
    html = f"""
    <script>
    (function() {{
      var TABS = {nav_items_js};
      var active = "{active_js}";
      var hasBadge = {badge_js};

      // Only show on mobile (≥900px = desktop, nav hidden by CSS already,
      // but skip injection entirely to avoid unnecessary DOM work)
      if (window.parent.innerWidth >= 900) {{
        var old = window.parent.document.getElementById('_cf_nav');
        if (old) old.remove();
        return;
      }}

      function setParentInput(newVal) {{
        var inp = window.parent.document.querySelector('input[data-testid="stTextInput-Input"]')
                  || window.parent.document.querySelector('input[type="text"]');
        if (!inp) return;
        var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
        setter.call(inp, newVal);
        inp.dispatchEvent(new window.parent.Event('input',{{bubbles:true}}));
      }}

      // Scroll to section anchor
      function scrollTo(key) {{
        var el = window.parent.document.querySelector('[data-cf-section="' + key + '"]');
        if (el) el.scrollIntoView({{behavior:'smooth', block:'start'}});
      }}

      var existing = window.parent.document.getElementById('_cf_nav');
      if (existing) {{
        if (existing.getAttribute('data-active') === active) return;
        existing.remove();
      }}

      var nav = window.parent.document.createElement('div');
      nav.id = '_cf_nav';
      nav.setAttribute('data-active', active);
      nav.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#060810;'
        + 'border-top:1px solid rgba(255,255,255,.08);display:flex;z-index:99999;'
        + 'padding:8px 0 max(10px,env(safe-area-inset-bottom));'
        + 'font-family:"Space Grotesk",-apple-system,BlinkMacSystemFont,sans-serif;'
        + 'backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);';

      TABS.forEach(function(tab) {{
        var key=tab[0], icon=tab[1], label=tab[2], isActive=(key===active);
        var item = window.parent.document.createElement('button');
        item.innerHTML = '<span style="font-size:1.3rem;display:block;line-height:1;">'
          + icon + (key==='events'&&hasBadge?'<sup style="font-size:.5rem;color:#ef4444">●</sup>':'')
          + '</span><span style="font-size:.58rem;display:block;margin-top:2px;font-weight:'
          + (isActive?'700':'500') + ';">' + label + '</span>';
        item.style.cssText = 'flex:1;background:none;border:none;cursor:pointer;padding:6px 2px;'
          + 'color:' + (isActive?'#4ade80':'#64748b') + ';outline:none;'
          + '-webkit-tap-highlight-color:transparent;transition:color .18s;';
        item.addEventListener('click', function() {{
          scrollTo(key);
          setParentInput(key);
        }});
        nav.appendChild(item);
      }});
      window.parent.document.body.appendChild(nav);
    }})();
    </script>
    <div style="width:1px;height:1px;opacity:0"><!-- {_r.random()} --></div>
    """
    b64 = base64.b64encode(html.encode()).decode()
    st.iframe(f"data:text/html;base64,{b64}", height=1, scrolling=False)


# ─────────────────────────────────────────────
# SHARED HEADER (always shown in game)
# ─────────────────────────────────────────────
def render_header(gs:GameState):
    si  = gs.season_info
    bm  = blended_moic(gs)
    fn  = gs.fund_number
    fl  = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    qtl = gs.total_quarters - gs.quarter_num
    sc  = {"s1":"s1c","s2":"s2c","s3":"s3c"}[si["css"]]

    c1, c2, c3, c4 = st.columns([3, 1.1, 1.2, 1.5])
    with c1:
        st.markdown(
            f"<h1 style='letter-spacing:-.025em'>{gs.firm_name}"
            f"<span style='font-size:.78rem;color:var(--muted);font-weight:500;margin-left:.5rem'>· {fl}</span></h1>",
            unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style="text-align:center">
          <div class="num-sm">{cf(gs.cash)}</div>
          <div class="lbl">Cash</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="text-align:center">
          <div class="num-sm"><span class="{sc}">{si['emoji']}</span> {gs.year} Q{gs.quarter}</div>
          <div class="lbl">{si['name']}</div></div>""", unsafe_allow_html=True)
    with c4:
        if st.button(f"⏭  Next Quarter  ({qtl})", key="nq"):
            advance_quarter(gs); st.rerun()

    # LP bar
    lp_c = lpc(gs.lp_satisfaction)
    lp_w = gs.lp_satisfaction
    lp_em = "😊" if lp_w>=70 else ("😐" if lp_w>=45 else "😡")
    st.markdown(f"""
    <div class="lp-row">
      <span style="font-size:.68rem;color:var(--muted);white-space:nowrap">{lp_em} LPs</span>
      <div class="lp-track">
        <div class="lp-fill" style="width:{lp_w}%;background:{lp_c};box-shadow:0 0 8px {lp_c}55;"></div>
      </div>
      <span style="font-size:.7rem;color:{lp_c};font-weight:700;">{lp_w}/100</span>
    </div>""", unsafe_allow_html=True)

    if lp_w < 35:   st.error("🚨 LPs threatening to pull out. Exit something now.")
    elif lp_w < 50: st.warning("⚠️ LPs getting restless. They want returns.")

    # Path pills
    paths = check_paths(gs)
    pills = []
    for p in paths.values():
        if p["hit"]:              css = "pp-hit"
        elif p["pace"]=="ahead":  css = "pp-ahead"
        elif p["pace"]=="behind": css = "pp-behind"
        else:                     css = "pp-miss"
        icon = "✓" if p["hit"] else ("↑" if p["pace"]=="ahead" else "↓")
        pills.append(f'<span class="path-pill {css}">{icon} {p["label"]} {p["actual"]}/{p["target"]}</span>')
    st.markdown("<div style='margin:.35rem 0'>" + " ".join(pills) + "</div>", unsafe_allow_html=True)

    if gs.event_log:
        st.markdown(f'<div class="log">{gs.event_log[0]}</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TAB: HOME
# ─────────────────────────────────────────────
def tab_home(gs:GameState):
    bm    = blended_moic(gs)
    paths = check_paths(gs)
    n_hit = sum(1 for p in paths.values() if p["hit"])
    realized = sum(e["proc"] for e in gs.exited)
    moic_col = mc(bm)

    # big 3 numbers
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl, col_cls in [
        (c1, f"{bm:.2f}×",           "Portfolio MOIC",  moic_col),
        (c2, cf(gs.cash),             "Cash Available",  ""),
        (c3, str(len(gs.exited)),     "Companies Exited",""),
        (c4, f"{n_hit}/3",            "Paths Hit",       "g" if n_hit>0 else "mu"),
    ]:
        with col:
            st.markdown(f"""<div class="pill-card">
              <div class="num {col_cls}">{val}</div>
              <div class="lbl">{lbl}</div></div>""", unsafe_allow_html=True)

    if not gs.companies and gs.quarter_num == 0:
        st.markdown("""<div class="hint" style="margin-top:.75rem">
          👋 <strong>Head to Deals</strong> to buy your first company.
          Hit <strong>Next Quarter</strong> to grow it. Sell when the return looks good.</div>""",
          unsafe_allow_html=True)

    if gs.companies:
        st.markdown("""<div class="sec-head">
          <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">Portfolio</span>
          <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)
        for c in gs.companies:
            m   = calc(c, gs)
            sec = SECTORS[c.sector]
            yh  = m["yh"]; age = f"{yh:.1f}y" if yh>=1 else f"{int(round(yh*4))}q"
            dot = SECTOR_DOT[c.sector]
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.6rem 1rem;background:var(--s1);border:1px solid var(--border);
                 border-radius:14px;margin-bottom:.35rem;">
              <span>
                <span class="sector-dot" style="background:{dot}"></span>
                <strong>{c.name}</strong>
                <span class="mu" style="font-size:.72rem"> · {c.sector} · {age}</span>
              </span>
              <div style="display:flex;gap:1.2rem;align-items:center">
                <span class="num-sm {mc(m['moic'])}">{m['moic']:.2f}×</span>
                <span class="mu" style="font-size:.78rem">{m['irr']*100:.0f}% IRR</span>
              </div>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB: DEALS
# ─────────────────────────────────────────────
def tab_deals(gs:GameState):
    full = len(gs.companies) >= MAX_PORTFOLIO

    st.markdown(f"""<div class="sec-head">
      <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">Deal Flow</span>
      {"<span style='font-size:.75rem;color:var(--red);font-weight:600'>· Portfolio full — sell first</span>" if full else ""}
      <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)

    buy_idx = None
    for i, d in enumerate(gs.deals):
        sec = SECTORS[d.sector]
        p3  = proj3(d, gs)
        can = d.entry_equity <= gs.cash and not full
        lev = d.entry_debt / max(d.ebitda, 1)
        ccss = SECTOR_CSS[d.sector]
        dot  = SECTOR_DOT[d.sector]
        tier_chip = f'<span class="chip chip-hot">🔥 Hot</span>' if d.tier=="hot" else \
                    (f'<span class="chip chip-risky">⚠ Risk</span>' if d.tier=="risky" else "")

        ca, cb, cc = st.columns([3.2, 1.8, 1])
        with ca:
            st.markdown(f"""<div class="card {ccss}">
              <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem">
                <span class="sector-dot" style="background:{dot};width:10px;height:10px"></span>
                <h3>{d.name}</h3>
                {tier_chip}
              </div>
              <div style="font-size:.74rem;color:var(--muted);margin-bottom:.45rem">CEO: {d.ceo}</div>
              <span class="chip">{d.sector}</span>
              <span class="chip">Enter <b>{d.entry_multiple:.1f}×</b></span>
              <span class="chip">Growth <b>{d.growth*100:.0f}%</b></span>
              <span class="chip">Margin <b>{d.margin*100:.0f}%</b></span>
              <span class="chip">Lev <b>{lev:.1f}×</b></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div style="display:flex;gap:.6rem;align-items:center;height:100%;padding:.4rem 0">
              <div style="text-align:center">
                <div class="num-sm">{cf(d.entry_equity)}</div>
                <div class="lbl">Equity Cost</div>
              </div>
              <div style="width:1px;height:32px;background:var(--border)"></div>
              <div style="text-align:center">
                <div class="num-sm {mc(p3)}">{p3:.1f}×</div>
                <div class="lbl">Est 3yr</div>
              </div>
            </div>""", unsafe_allow_html=True)
        with cc:
            lbl = "Buy" if can else ("Full" if full else "💸")
            if st.button(lbl, key=f"buy_{i}_{gs.quarter_num}", disabled=not can):
                buy_idx = i

    if buy_idx is not None:
        d = gs.deals[buy_idx]
        gs.cash -= d.entry_equity; d.entry_quarter = gs.quarter_num
        gs.companies.append(d); gs.deals.pop(buy_idx)
        gs.event_log.insert(0, f"Closed {d.name}. {d.ceo} is 'excited about the partnership.'")
        gs.event_log = gs.event_log[:6]
        gs.sound_queue.append("BUY")
        st.rerun()

# ─────────────────────────────────────────────
# TAB: PORTFOLIO
# ─────────────────────────────────────────────
def tab_portfolio(gs:GameState):
    st.markdown(f"""<div class="sec-head">
      <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">
        Portfolio ({len(gs.companies)}/{MAX_PORTFOLIO})</span>
      <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)

    if not gs.companies:
        st.markdown('<div class="hint">No holdings yet — go to Deals to invest.</div>', unsafe_allow_html=True)
        return

    sell_idx = None
    for i, c in enumerate(gs.companies):
        m    = calc(c, gs)
        sec  = SECTORS[c.sector]
        yh   = m["yh"]; age = f"{yh:.1f}y" if yh>=1 else f"{int(round(yh*4))}q"
        ccss = SECTOR_CSS[c.sector]
        dot  = SECTOR_DOT[c.sector]
        status = (' <span style="color:var(--red);font-size:.72rem">⚠ damaged</span>' if c.moic_modifier<0.85
                  else (' <span style="color:var(--lime);font-size:.72rem">✨ boosted</span>' if c.moic_modifier>1.15 else ""))

        ca, cb, cc = st.columns([3.2, 1.8, 1])
        with ca:
            st.markdown(f"""<div class="card {ccss}">
              <div style="display:flex;align-items:center;gap:.45rem;margin-bottom:.3rem">
                <span class="sector-dot" style="background:{dot};width:10px;height:10px"></span>
                <span style="font-weight:700">{c.name}</span>
                <span style="font-size:.72rem;color:var(--muted)">{c.sector} · {c.ceo} · {age}</span>
                {status}
              </div>
              <span class="chip">{cf(m['revenue'])} rev</span>
              <span class="chip">Lev <b>{m['debt']/max(m['ebitda'],1):.1f}×</b></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div style="display:flex;gap:.6rem;align-items:center;height:100%;padding:.4rem 0">
              <div style="text-align:center">
                <div class="num-sm {mc(m['moic'])}">{m['moic']:.2f}×</div>
                <div class="lbl">MOIC</div>
              </div>
              <div style="width:1px;height:32px;background:var(--border)"></div>
              <div style="text-align:center">
                <div class="num-sm">{m['irr']*100:.0f}%</div>
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
        gs.sound_queue.append("SELL_GREAT" if m["moic"]>=2.0 else ("SELL_OK" if m["moic"]>=1.3 else "SELL_BAD"))
        em = "🏆" if m["moic"]>=2.0 else "✅" if m["moic"]>=1.4 else "📉"
        st.success(f"{em} Sold **{cname}** — {m['moic']:.2f}× · {cf(m['equity'])}")
        st.rerun()

# ─────────────────────────────────────────────
# TAB: EVENTS
# ─────────────────────────────────────────────
def tab_events(gs:GameState):
    st.markdown("""<div class="sec-head">
      <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">Events</span>
      <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)

    if gs.event_log:
        for msg in gs.event_log:
            st.markdown(f'<div class="log">• {msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="hint">No events yet this fund.</div>', unsafe_allow_html=True)

    if gs.exited:
        st.markdown("""<div class="sec-head" style="margin-top:1rem">
          <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">Exit History</span>
          <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)
        for e in reversed(gs.exited):
            dot = SECTOR_DOT[e['sector']]
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.65rem 1rem;background:var(--s1);border:1px solid var(--border);
                 border-radius:14px;margin-bottom:.35rem;">
              <span>
                <span class="sector-dot" style="background:{dot}"></span>
                <strong>{e['name']}</strong>
                <span class="mu" style="font-size:.72rem"> · {e['yh']:.1f}yr</span>
              </span>
              <span class="num-sm {mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="mu" style="font-size:.78rem">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB: FUND
# ─────────────────────────────────────────────
def tab_fund(gs:GameState):
    cfg    = DIFFICULTY[gs.difficulty]
    paths  = check_paths(gs)
    fn     = gs.fund_number
    fl     = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    unlock = UNLOCKS[sum(1 for p in paths.values() if p["hit"])]
    next_cash = cfg["cash"] * unlock["cash_mult"] * gs.fund_cash_mult
    raised = cfg["cash"] * gs.fund_cash_mult
    realized = sum(e["proc"] for e in gs.exited)

    st.markdown(f"""<div class="sec-head">
      <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">{fl}</span>
      <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    for col,v,l in [(c1,cf(raised),"Raised"),(c2,cf(raised-gs.cash),"Deployed"),(c3,cf(realized),"Realized")]:
        with col:
            st.markdown(f'<div class="pill-card"><div class="num-sm">{v}</div><div class="lbl">{l}</div></div>',
                        unsafe_allow_html=True)

    st.markdown("""<div class="sec-head" style="margin-top:1rem">
      <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">Win Paths</span>
      <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)
    for p in paths.values():
        pct   = min(p["actual"] / max(p["target"], 1), 1.0)
        bar_w = int(pct * 100)
        col   = "#4ade80" if p["hit"] else ("#fbbf24" if pct>0.6 else "#374151")
        tick  = "✓ " if p["hit"] else ""
        st.markdown(f"""
        <div style="margin:.45rem 0">
          <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:.3rem">
            <span>{tick}<strong>{p['label']}</strong></span>
            <span style="color:{col};font-weight:700">{p['actual']} / {p['target']}</span>
          </div>
          <div style="background:var(--s3);border-radius:999px;height:6px;overflow:hidden">
            <div style="width:{bar_w}%;height:6px;background:{col};border-radius:999px;
                 box-shadow:0 0 6px {col}88;transition:width .4s"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="unlock-card" style="margin-top:1rem">
      <div style="font-size:.66rem;color:var(--gold);font-weight:700;text-transform:uppercase;
           letter-spacing:.08em;margin-bottom:.35rem">🔓 On Track For</div>
      <div class="num-sm" style="color:var(--gold)">{unlock['fund']} — {cf(next_cash)}</div>
      <div style="font-size:.82rem;color:var(--muted);margin:.35rem 0 0">{unlock['flavor']}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="sec-head" style="margin-top:1rem">
      <span style="font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">LPs</span>
      <div class="sec-head-line"></div></div>""", unsafe_allow_html=True)
    for lp_name in LP_NAMES:
        ok = gs.lp_satisfaction >= 60
        col = "#4ade80" if ok else "#fbbf24"
        lbl = "Satisfied" if ok else "Restless"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
             padding:.6rem 1rem;background:var(--s1);border:1px solid var(--border);
             border-radius:14px;margin-bottom:.35rem">
          <span style="font-weight:600">{lp_name}</span>
          <span style="color:{col};font-size:.8rem;font-weight:700">{lbl}</span>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# EVENT SCREEN (interrupts any tab)
# ─────────────────────────────────────────────
def screen_event(gs:GameState):
    ev  = gs.pending_event
    css = {"crisis":"ev-crisis","opportunity":"ev-opportunity",
           "rival":"ev-rival","lp":"ev-lp","season":"ev-season"}.get(ev.get("type",""),"ev-season")

    st.markdown(f"""
    <div class="ev {css}">
      <div style="font-size:2rem;margin-bottom:.5rem">{ev.get('icon','📋')}</div>
      <h2 style="margin:0 0 .6rem;font-size:1.15rem">{ev.get('title','')}</h2>
      <p style="font-size:.9rem;color:var(--text);line-height:1.65">{ev.get('text','')}</p>
    </div>""", unsafe_allow_html=True)

    choices = ev.get("choices", [])
    if ev.get("type") != "season":
        st.markdown("<p style='font-size:.78rem;color:var(--muted);margin:.55rem 0 .3rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em'>What do you do?</p>",
                    unsafe_allow_html=True)

    cols = st.columns(max(len(choices), 1))
    for i, ch in enumerate(choices):
        with cols[i]:
            st.markdown('<div class="choice-btn">', unsafe_allow_html=True)
            if st.button(ch["label"], key=f"ch_{i}_{gs.quarter_num}"):
                apply_effect(gs, ch.get("effect","nothing"), ev.get("cid"))
                if gs.forced_exit_id:
                    idx=next((j for j,c in enumerate(gs.companies) if c.id==gs.forced_exit_id),None)
                    if idx is not None: sell_company(gs, idx)
                    gs.forced_exit_id=""
                gs.pending_event={}
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SCREENS
# ─────────────────────────────────────────────
def screen_start():
    st.markdown("""
    <div style="text-align:center;padding:2.5rem 0 1.5rem">
      <div style="font-size:3.2rem;margin-bottom:.75rem;filter:drop-shadow(0 0 24px rgba(74,222,128,.4))">💼</div>
      <h1 style="font-size:3rem;font-weight:800;letter-spacing:-.04em;
          background:linear-gradient(135deg,#4ade80 0%,#a78bfa 55%,#fbbf24 100%);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        CarryForge
      </h1>
      <p style="color:var(--muted);font-size:.95rem;margin:.55rem 0 1.75rem;font-weight:500">
        Build your PE empire · Three ways to win · No two games the same
      </p>
    </div>""", unsafe_allow_html=True)

    with st.form("setup"):
        c1, c2 = st.columns(2)
        with c1: firm    = st.text_input("Firm name",   placeholder=random.choice(FIRM_DEFAULTS))
        with c2: partner = st.text_input("Your name",   placeholder="e.g. Alex Chen")

        diff = st.radio("Difficulty", ["Easy","Balanced","Hard"], horizontal=True, index=1,
                        captions=["$60M · relaxed","$50M · realistic","$40M · brutal"])
        p = DIFFICULTY[diff]["paths"]
        st.markdown(f"""
        <div style="background:var(--s1);border:1px solid var(--border-lit);border-radius:16px;
             padding:1rem 1.2rem;margin:.7rem 0">
          <div style="font-size:.65rem;color:var(--muted);margin-bottom:.5rem;font-weight:700;
               text-transform:uppercase;letter-spacing:.1em">Three ways to win — hit any one</div>
          <div style="display:flex;gap:1.1rem;flex-wrap:wrap;font-size:.85rem;font-weight:600">
            <span style="color:var(--lime)">💰 {p['moic']}× MOIC</span>
            <span style="color:var(--teal)">🤝 LPs ≥{p['lp']}</span>
            <span style="color:var(--gold)">🏆 {p['exits']} exits</span>
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
            st.session_state.tab = "home"
            st.session_state["score_sound_played"] = False
            st.rerun()


def screen_game():
    gs = G()

    # Tab bus: hidden text input JS nav writes to (mobile only)
    current_tab_raw = st.text_input("_tab", value=get_tab(), key="tab_input",
                                     label_visibility="collapsed")
    if current_tab_raw != get_tab():
        st.session_state["tab"] = current_tab_raw
        st.rerun()

    active_tab = get_tab()
    flush_sounds(gs)
    render_header(gs)

    if gs.pending_event:
        screen_event(gs)
        inject_bottom_nav(active_tab, has_event=True)
        return

    # ── Section helper: adds anchor + CSS class for show/hide on mobile ──
    def section(key, label_fn):
        """Wrap a section so CSS can show/hide it on mobile based on active tab."""
        active_cls = "cf-active" if key == active_tab else ""
        st.markdown(
            f'<div data-cf-section="{key}" class="desktop-section {active_cls}" '
            f'style="scroll-margin-top:64px"></div>',
            unsafe_allow_html=True
        )
        label_fn(gs)

    # ── Desktop: all sections visible; Mobile: only active section ──────
    section("home",      tab_home)
    section("deals",     tab_deals)
    section("portfolio", tab_portfolio)
    section("events",    tab_events)
    section("fund",      tab_fund)

    inject_bottom_nav(active_tab, has_event=False)


def screen_score():
    gs=G()
    if not st.session_state.get("score_sound_played"):
        st.session_state["score_sound_played"]=True
        n=sum(1 for p in check_paths(gs).values() if p["hit"])
        gs.sound_queue.append("VICTORY" if n>=1 else "GRADE_C")
    flush_sounds(gs)

    paths=check_paths(gs); n_hit=sum(1 for p in paths.values() if p["hit"])
    unlock=UNLOCKS[n_hit]; fn=gs.fund_number
    bm=blended_moic(gs); realized=sum(e["proc"] for e in gs.exited)
    grade,gc={3:("S","#f59e0b"),2:("A","#10b981"),1:("B","#3b82f6"),0:("C","#ef4444")}[n_hit]
    lp_quotes={
        range(70,101):"LPs asking about Fund II before you've closed this one.",
        range(45,70): "LPs satisfied. One asked if you're 'considering expanding the strategy.'",
        range(25,45): "LPs polite but distant. Hartley CC'd their attorney on the last email.",
        range(0,25):  "Westfield wants a meeting. On a Saturday.",
    }
    lp_quote=next((v for r,v in lp_quotes.items() if gs.lp_satisfaction in r),"")
    fl=f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    next_cash=DIFFICULTY[gs.difficulty]["cash"]*unlock["cash_mult"]*gs.fund_cash_mult

    st.markdown(f"""
    <div class="score-card">
      <div style="font-size:.7rem;color:var(--muted);margin-bottom:.25rem;font-weight:600;
           text-transform:uppercase;letter-spacing:.08em">{gs.firm_name} · {fl}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:5rem;font-weight:900;
           color:{gc};line-height:1;text-shadow:0 0 40px {gc}66">{grade}</div>
      <div style="font-size:1.1rem;font-weight:700;margin:.4rem 0 .2rem">{n_hit}/3 paths hit</div>
      <p style="font-size:.88rem;color:var(--muted);margin-bottom:1.5rem;max-width:360px;
         margin-left:auto;margin-right:auto">{lp_quote}</p>
      <div style="display:flex;justify-content:space-around;gap:.5rem;flex-wrap:wrap">
        <div><div class="num" style="color:{gc}">{bm:.2f}×</div><div class="lbl">MOIC</div></div>
        <div><div class="num">{len(gs.exited)}</div><div class="lbl">Exits</div></div>
        <div><div class="num">{cf(realized)}</div><div class="lbl">Realized</div></div>
        <div><div class="num" style="color:{lpc(gs.lp_satisfaction)}">{gs.lp_satisfaction}</div>
          <div class="lbl">LP Score</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    _, c2, c3 = st.columns([1,1,1])
    with c2:
        nl=f"Start {unlock['fund']} →" if fn<3 else "🔄 New Fund"
        if st.button(nl, key="fn"):
            st.session_state["score_sound_played"]=False
            if fn<3:
                ng=GameState(screen="game",difficulty=gs.difficulty,cash=next_cash,
                    lp_satisfaction=min(100,DIFFICULTY[gs.difficulty]["lp_start"]+unlock["lp_bonus"]),
                    firm_name=gs.firm_name,partner_name=gs.partner_name,
                    fund_number=fn+1,fund_cash_mult=unlock["cash_mult"]*gs.fund_cash_mult,
                    fund_lp_bonus=gs.fund_lp_bonus+unlock["lp_bonus"],rival=gs.rival)
                ng.deals=make_deals(ng,5)
                st.session_state.gs=ng
                st.session_state.tab="home"
            else:
                del st.session_state["gs"]
            st.rerun()
    with c3:
        if st.button("🔄 New Game", key="ng"):
            st.session_state["score_sound_played"]=False
            del st.session_state["gs"]; st.rerun()

    st.markdown("<h2 style='text-align:center;margin-top:1.1rem;font-size:.9rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em'>Win Paths</h2>",
                unsafe_allow_html=True)
    for p in paths.values():
        css = "path-row-hit" if p["hit"] else "path-row-miss"
        col = "#4ade80" if p["hit"] else "var(--muted)"
        st.markdown(f"""<div class="{css}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-weight:700">{'✓ ' if p['hit'] else ''}{p['label']}</span>
            <span style="color:{col};font-weight:700;font-family:'JetBrains Mono',monospace">
              {p['actual']} {'✓' if p['hit'] else f'/ {p["target"]}'}</span>
          </div></div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="unlock-card" style="margin-top:1rem">
      <div style="font-size:.65rem;color:var(--gold);font-weight:700;text-transform:uppercase;
           letter-spacing:.1em;margin-bottom:.4rem">{'🔓 Unlocked' if fn<3 else '🏆 Endgame'}</div>
      <div style="font-size:1.1rem;font-weight:800;color:var(--gold)">{unlock['fund']} · {cf(next_cash)}</div>
      <div style="font-size:.82rem;color:var(--muted);margin:.4rem 0 0">{unlock['flavor']}</div>
    </div>""", unsafe_allow_html=True)

    if gs.exited:
        st.markdown("<div style='margin-top:1.1rem'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;font-size:.9rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em'>Deal Recap</h2>",
                    unsafe_allow_html=True)
        for e in sorted(gs.exited, key=lambda x: -x["moic"]):
            dot = SECTOR_DOT[e['sector']]
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.6rem 1rem;background:var(--s1);border:1px solid var(--border);
                 border-radius:14px;margin-bottom:.3rem">
              <span>
                <span class="sector-dot" style="background:{dot}"></span>
                <strong>{e['name']}</strong>
              </span>
              <span class="num-sm {mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="mu" style="font-size:.78rem">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
def main():
    gs=G()
    if   gs.screen=="start": screen_start()
    elif gs.screen=="game":  screen_game()
    elif gs.screen=="score": screen_score()

if __name__=="__main__":
    main()
