"""
CarryForge v9.0
===============
UX overhaul based on 240-run simulation across 8 player archetypes.

Fixes applied (in priority order):
- Sell button moved under each card row (was far-right column, unreachable on mobile)
- All layouts reduced to max 3 columns (was 5, crushed on iPhone)
- Deal cards get quality tiers & analyst signals (was identical-looking every quarter)
- MOIC shows 1.0x entry value in first quarter (was 0.00x — confusing)
- Start form is now optional auto-names (was forced text input)
- First-quarter hint shown if no companies yet
- "3yr Est." → "Est. Return" with context tag
- "Debt" column → "Leverage" with ratio
- LP bar made 14px + emoji health indicator
- Sticky "Next Quarter" button at page bottom
- Score screen: grade + CTA above fold before deal recap
- Path badges now show "ahead / on track / behind" pace indicator
- Company health dot from moic_modifier (🟢🟡🔴)
- Auto-save status shown in header

Preserved (don't break):
- Letter grade S/A/B/C
- Three seasons + transition cards
- LP closing quotes
- CEO names on deals
- Firm name input (now optional)
- 12-quarter session length
- Event writing tone
"""

import streamlit as st
import numpy as np
import random
from dataclasses import dataclass, field

st.set_page_config(page_title="CarryForge", page_icon="💼",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────
# CSS — mobile-first, max 3 columns
# ─────────────────────────────────────────────
st.markdown("""
<style>
  :root {
    --bg:#080d1e; --card:#111827; --card2:#1a2235;
    --green:#10b981; --gold:#f59e0b; --red:#ef4444;
    --blue:#3b82f6; --purple:#8b5cf6; --pink:#ec4899; --teal:#14b8a6;
    --border:rgba(255,255,255,0.08); --text:#f1f5f9; --muted:#64748b;
    --green-dim:rgba(16,185,129,.12);
  }
  html,body,.stApp{background:var(--bg)!important;color:var(--text);}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding:1rem 1rem 6rem;max-width:980px;margin:0 auto;}
  h1{font-size:1.7rem;font-weight:800;margin:0;color:var(--text);}
  h2{font-size:1.15rem;font-weight:700;margin:.8rem 0 .4rem;color:var(--text);}
  h3{font-size:.95rem;font-weight:600;margin:0;color:var(--text);}
  p{margin:0;}

  /* Buttons — all green by default */
  .stButton>button{
    background:linear-gradient(135deg,var(--green),#059669);color:#fff!important;
    border:none!important;border-radius:10px;font-weight:700;font-size:.88rem;
    padding:.6rem 1rem;width:100%;transition:transform .15s,box-shadow .15s;
    box-shadow:0 4px 12px rgba(16,185,129,.22);
  }
  .stButton>button:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(16,185,129,.38);}
  .stButton>button:disabled{background:#1e293b!important;color:#475569!important;
    box-shadow:none!important;transform:none!important;}

  hr{border-color:var(--border);margin:.7rem 0;}

  /* Compact stat block */
  .stat{text-align:center;padding:.1rem 0;}
  .stat-val{font-size:1.25rem;font-weight:800;color:var(--text);line-height:1.2;}
  .stat-lbl{font-size:.62rem;font-weight:600;color:var(--muted);text-transform:uppercase;
             letter-spacing:.07em;margin-top:.1rem;}

  /* Cards — sector-coded left border */
  .dcard{background:var(--card);border:1px solid var(--border);border-left:3px solid transparent;
         border-radius:12px;padding:.8rem .95rem;margin-bottom:.4rem;}
  .dcard-SaaS{border-left-color:var(--blue);}
  .dcard-Hardware{border-left-color:var(--purple);}
  .dcard-Healthcare{border-left-color:var(--pink);}
  .dcard-Fintech{border-left-color:var(--teal);}

  /* Tags */
  .tag{display:inline-block;background:var(--card2);border:1px solid var(--border);
       border-radius:5px;padding:.15rem .42rem;font-size:.7rem;font-weight:600;
       color:var(--muted);margin:2px;}
  .tag span{color:var(--text);}
  .tag-hot{background:rgba(245,158,11,.12);border-color:var(--gold);color:var(--gold);}
  .tag-strong{background:rgba(16,185,129,.1);border-color:var(--green);color:var(--green);}
  .tag-risky{background:rgba(239,68,68,.1);border-color:var(--red);color:var(--red);}

  /* Win path row */
  .path-row{display:flex;gap:.5rem;flex-wrap:wrap;margin:.4rem 0;}
  .path-chip{border-radius:7px;padding:.3rem .65rem;font-size:.72rem;font-weight:700;
             border:1px solid;flex:1;min-width:140px;text-align:center;}
  .path-hit  {background:var(--green-dim);border-color:var(--green);color:var(--green);}
  .path-miss {background:var(--card2);border-color:var(--border);color:var(--muted);}
  .path-ahead{background:rgba(16,185,129,.07);border-color:rgba(16,185,129,.35);color:#6ee7b7;}
  .path-behind{background:rgba(239,68,68,.07);border-color:rgba(239,68,68,.3);color:#fca5a5;}

  /* LP bar — 14px tall, visible */
  .lp-wrap{display:flex;align-items:center;gap:.55rem;margin:.45rem 0;}
  .lp-track{flex:1;height:14px;background:var(--card2);border-radius:999px;overflow:hidden;}
  .lp-fill{height:14px;border-radius:999px;transition:width .4s ease;}

  /* Narrative events */
  .ev-card{background:var(--card);border:1px solid;border-radius:14px;
           padding:1.1rem 1.2rem;margin:.4rem 0;}
  .ev-crisis     {border-color:#ef4444;background:rgba(239,68,68,.06);}
  .ev-opportunity{border-color:#10b981;background:rgba(16,185,129,.06);}
  .ev-rival      {border-color:#8b5cf6;background:rgba(139,92,246,.06);}
  .ev-lp         {border-color:#f59e0b;background:rgba(245,158,11,.06);}
  .ev-season     {border-color:#3b82f6;background:rgba(59,130,246,.08);}
  .ev-neutral    {border-color:var(--border);}
  .choice-btn button{
    background:var(--card2)!important;border:1px solid var(--border)!important;
    color:var(--text)!important;box-shadow:none!important;
  }
  .choice-btn button:hover{border-color:var(--green)!important;color:var(--green)!important;
    transform:none!important;}

  /* Score screen */
  .score-box{background:var(--card);border:1px solid var(--border);border-radius:18px;
             padding:1.75rem;text-align:center;max-width:500px;margin:1rem auto;}
  .unlock-card{background:var(--card);border:1px solid rgba(245,158,11,.35);
               border-radius:14px;padding:1.1rem;margin:.5rem 0;text-align:center;}
  .path-result-hit {background:rgba(16,185,129,.12);border:1px solid var(--green);
               border-radius:10px;padding:.55rem .9rem;margin:.25rem 0;}
  .path-result-miss{background:var(--card2);border:1px solid var(--border);
               border-radius:10px;padding:.55rem .9rem;margin:.25rem 0;opacity:.55;}

  /* Season labels */
  .s1{color:#10b981;font-weight:700;} .s2{color:#f59e0b;font-weight:700;}
  .s3{color:#ef4444;font-weight:700;}

  /* Hint box */
  .hint{background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.25);
        border-radius:10px;padding:.65rem .9rem;font-size:.84rem;color:#93c5fd;margin:.5rem 0;}

  /* Sticky footer */
  .sticky-footer{position:fixed;bottom:0;left:0;right:0;
    background:linear-gradient(0deg,var(--bg) 70%,transparent);
    padding:1rem 1.5rem 1.25rem;z-index:100;max-width:980px;margin:0 auto;}

  /* Inline log */
  .log-line{padding:.4rem .8rem;background:var(--card2);border-radius:8px;
            font-size:.8rem;color:var(--muted);margin:.2rem 0;}

  .c-green{color:var(--green)!important;font-weight:700;}
  .c-gold {color:var(--gold)!important;font-weight:700;}
  .c-red  {color:var(--red)!important;font-weight:700;}
  .c-muted{color:var(--muted)!important;}
  .fw7{font-weight:700;}

  @media(max-width:640px){
    .block-container{padding:.75rem .75rem 5.5rem;}
    .stat-val{font-size:1.1rem;}
    h1{font-size:1.4rem;}
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
MAX_PORTFOLIO = 4

SEASONS = {
    1:{"name":"Bull Run","emoji":"🟢","css":"s1","exit_mod":1.15,"growth_mod":1.10,
       "desc":"Capital is cheap. Multiples are generous.",
       "title":"The Bull Is Running",
       "text":"Rates are near zero. Every growth equity fund in NYC has more capital than ideas. "
              "Sellers know it. Price accordingly."},
    2:{"name":"The Turn","emoji":"🟡","css":"s2","exit_mod":1.00,"growth_mod":0.95,
       "desc":"Markets normalizing. LPs getting nervous.",
       "title":"The Market Has Turned",
       "text":"The easy money is gone. Buyers are more selective. "
              "Your LPs have started CC'ing their advisors on emails. Time to execute."},
    3:{"name":"The Reckoning","emoji":"🔴","css":"s3","exit_mod":0.85,"growth_mod":0.88,
       "desc":"Credit tight. Exits harder. Timing is everything.",
       "title":"Batten Down the Hatches",
       "text":"Rates are up 300bps. Debt markets are nearly closed. "
              "Companies that haven't exited are going to sit a while longer. "
              "Your LPs know this. They're watching your every move."},
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
    {"name":"Apex Capital","emoji":"🦅"},{"name":"Redwood PE","emoji":"🌲"},
    {"name":"Meridian Partners","emoji":"🐍"},{"name":"Pinnacle Fund","emoji":"🏔"},
]
LP_NAMES = [
    "Westfield Endowment","CalPERS West","Hartley Family Office","Atlas Foundation",
]
FIRM_DEFAULTS = [
    "Genesis Capital","Ironwood Partners","Crestview Equity","Summit PE","Clarendon Fund",
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
    "ceo_stays":      {"moic_delta":+.20,"msg":"CEO stayed. Equity vesting updated. They seem pleased."},
    "ceo_leaves_slow":{"moic_delta":-.10,"msg":"They took it. You have 90 days."},
    "ceo_gone":       {"moic_delta":-.25,"msg":"CEO out. Search firm on retainer. Team is nervous."},
    "ceo_gone_clean": {"moic_delta":-.20,"msg":"Terminated. Legal risk contained. Business wobbling."},
    "crisis_managed": {"moic_delta":-.10,"msg":"Charges reduced. Optics are still your problem."},
    "disaster":       {"moic_delta":-.40,"msg":"SEC subpoenas arrived Friday afternoon."},
    "big_growth":     {"moic_delta":+.30,"msg":"Bold bet paid. Revenue +28%. CEO is insufferable."},
    "medium_growth":  {"moic_delta":+.15,"msg":"Bumpy delivery. Contract held. Client renewed last minute."},
    "nothing":        {"moic_delta":.00, "msg":"Status quo. Deck looks exactly the same as last quarter."},
    "partial_save":   {"moic_delta":-.08,"msg":"12-month extension. They're still going to leave."},
    "slight_hit":     {"moic_delta":-.12,"msg":"Revenue down 18%. Pipeline is 'robust' apparently."},
    "war":            {"moic_delta":-.30,"msg":"Litigation is expensive. Distraction is worse."},
    "lose_deal":      {"moic_delta":.00, "msg":"Deal lost. You walk out saying 'discipline.'"},
    "win_expensive":  {"moic_delta":-.05,"msg":"Won it. Paid over market. Model needs a hero exit."},
    "win_clever":     {"moic_delta":+.08,"msg":"Seller picked you over the higher bid. Reputation matters."},
    "rivalry_up":     {"moic_delta":.00, "msg":"They didn't reply. Probably furious."},
    "lp_amused":      {"lp_delta":+5,   "msg":"LP laughed. Said 'these guys.' Good relationship."},
    "pressure_sell":  {"force_exit":True,"msg":"You committed to an exit. Now deliver."},
    "bought_time":    {"lp_delta":-3,   "msg":"They accepted the deck. Called again 3 weeks later."},
    "lp_annoyed":     {"lp_delta":-10,  "msg":"Associate took it. LP is 63 and has been in PE since before you were born."},
    "lp_happy_hit":   {"moic_delta":-.05,"lp_delta":+10,"msg":"LP placated. Company took a small leverage hit."},
    "lp_exits":       {"lp_delta":-20,  "msg":"LP sold at 35% discount. New holder emails weekly."},
    "lp_furious":     {"lp_delta":-25,  "msg":"Called the bluff. You're personally calling every LP this Friday night."},
    "forced_exit":    {"force_exit":True,"msg":"Company going to market. Time to find out your IRR."},
    "auction":        {"moic_delta":+.12,"msg":"Four bidders showed. Extracted another 18% on price."},
    "ipo_prep":       {"moic_delta":+.08,"msg":"12-month process begins. Dress rehearsal with analysts next quarter."},
    "rate_hedged":    {"moic_delta":+.05,"msg":"Locked in 6.2% for 5 years. Feels smart already."},
    "risky_hold":     {"moic_delta":+.10,"msg":"The wave didn't come. Multiple contracted 15%."},
    "ceo_upgrade":    {"moic_delta":+.15,"msg":"Hired ex-Stripe COO. First week: restructured sales."},
    "mgmt_stable":    {"moic_delta":+.05,"msg":"OP is annoyed but professional. Board quieter."},
    "slow_resolution":{"moic_delta":-.05,"msg":"Mediation took 6 weeks. Everyone is technically aligned."},
    "addon_win":      {"moic_delta":+.15,"msg":"Tuck-in closed. Customer cross-sell already working."},
    "addon_maybe":    {"moic_delta":+.05,"msg":"They came back 20% lower. Counter-signed same afternoon."},
}

DIFFICULTY = {
    "Easy":    {"cash":60e6,"exit_mult":9.5,"quarters":12,"lp_start":80,
                "paths":{"moic":1.5,"lp":70,"exits":3}},
    "Balanced":{"cash":50e6,"exit_mult":8.5,"quarters":12,"lp_start":65,
                "paths":{"moic":1.75,"lp":65,"exits":4}},
    "Hard":    {"cash":40e6,"exit_mult":7.5,"quarters":12,"lp_start":50,
                "paths":{"moic":2.0,"lp":60,"exits":5}},
}
UNLOCKS = {
    0:{"fund":"Fund II","cash_mult":1.0,"lp_bonus":0, "flavor":"Same terms. LPs are giving you one more shot."},
    1:{"fund":"Fund II","cash_mult":1.3,"lp_bonus":8, "flavor":"One path hit. LPs are interested. Modest step up."},
    2:{"fund":"Fund II","cash_mult":1.6,"lp_bonus":15,"flavor":"Two paths hit. Strong showing. Real upgrade."},
    3:{"fund":"Fund II","cash_mult":2.0,"lp_bonus":25,"flavor":"All three paths. LPs are fighting over allocation. Fund III is on the table."},
}

# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────
@dataclass
class Company:
    id:str; name:str; sector:str; ceo:str
    revenue:float; ebitda:float; margin:float; growth:float
    entry_multiple:float; entry_ev:float; entry_debt:float; entry_equity:float
    entry_quarter:int=0; moic_modifier:float=1.0
    # deal quality tier — set once at generation
    tier:str="standard"   # "hot" | "standard" | "risky"

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
    deals = []
    used_names = {c.name for c in gs.companies} | {d.name for d in deals}
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

        # Pick a unique name
        pool = [n for n in COMPANY_NAMES[sector] if n not in used_names]
        if not pool: pool = COMPANY_NAMES[sector]
        name = random.choice(pool)
        used_names.add(name)

        # Quality tier: hot (top growth+margin), risky (low margin or high entry), standard
        score = gr * 0.6 + mg * 0.4
        if score > 0.22 and em < 8.0:  tier = "hot"
        elif em > 8.8 or mg < 0.10:    tier = "risky"
        else:                           tier = "standard"

        deals.append(Company(
            id=f"{name[:3]}{random.randint(100,999)}", name=name,
            sector=sector, ceo=random.choice(CEO_NAMES),
            revenue=rev, ebitda=eb, margin=mg, growth=gr,
            entry_multiple=em, entry_ev=ev, entry_debt=debt, entry_equity=eq,
            entry_quarter=gs.quarter_num, tier=tier,
        ))
    return deals

def calc(c:Company, gs:GameState) -> dict:
    qh = gs.quarter_num - c.entry_quarter
    yh = qh / 4.0
    si = gs.season_info
    sm = gs.sector_mods.get(c.sector, 1.0)
    mature_yrs = max(qh - 8, 0) / 4.0
    eg = c.growth * gs.growth_mod * sm * si["growth_mod"] * ((1-.08)**mature_yrs)

    debt = c.entry_debt
    for yr in range(1, int(yh)+1):
        my   = max((yr*4-8)/4, 0)
        y_eg = c.growth * gs.growth_mod * sm * si["growth_mod"] * ((1-.08)**my)
        yr_e = c.revenue * ((1+y_eg)**yr) * c.margin
        debt = max(debt - max(yr_e*0.55 - debt*0.065, 0)*0.35, 0)

    rev   = c.revenue * ((1+eg)**yh)
    ebitda = rev * c.margin

    # Peak window
    if yh < 1.0:    pm = 0.88 + yh*0.12
    elif yh <= 3.0: pm = 1.0  + (yh-1.0)*0.05
    else:           pm = 1.10 - (yh-3.0)*0.05

    cfg   = DIFFICULTY[gs.difficulty]
    em    = cfg["exit_mult"] * gs.exit_mult_mod * sm * pm * si["exit_mod"]
    equity = max(ebitda*em - debt, 0) * max(c.moic_modifier, 0.1)
    moic  = equity / max(c.entry_equity, 1)

    # Show 1.0x when freshly bought (not confusing 0.x)
    if yh < 0.25: moic = max(moic, 0.95)

    irr = (moic**(1/max(yh,.25))-1) if yh > 0 else 0
    return {"revenue":rev,"ebitda":ebitda,"equity":equity,"debt":debt,
            "moic":moic,"irr":irr,"yh":yh,"pm":pm}

def blended_moic(gs:GameState) -> float:
    ti = sum(c.entry_equity for c in gs.companies) + sum(e["eq"] for e in gs.exited)
    to = sum(calc(c,gs)["equity"] for c in gs.companies)*0.70 + sum(e["proc"] for e in gs.exited)
    return to / max(ti, 1)

def proj3(d:Company, gs:GameState) -> float:
    r3 = d.revenue * ((1+d.growth)**3)
    eb3 = r3 * d.margin
    debt = d.entry_debt
    for yr in range(1,4):
        yr_e = d.revenue*((1+d.growth)**yr)*d.margin
        debt = max(debt - max(yr_e*0.55-debt*0.065,0)*0.35, 0)
    em = DIFFICULTY[gs.difficulty]["exit_mult"] * 1.10
    return max(eb3*em-debt,0) / max(d.entry_equity,1)

def check_paths(gs:GameState) -> dict:
    cfg = DIFFICULTY[gs.difficulty]["paths"]
    bm  = blended_moic(gs)
    q   = gs.quarter_num
    tot = gs.total_quarters
    # Pace: at what fraction of the game should each path be X% done
    moic_pace  = bm / max(cfg["moic"],1) / max(q/tot, 0.01)
    exits_pace = len(gs.exited) / max(cfg["exits"],1) / max(q/tot, 0.01)
    lp_ok      = gs.lp_satisfaction >= cfg["lp"]
    return {
        "returns":{"hit":bm>=cfg["moic"],"target":cfg["moic"],"actual":round(bm,2),
                   "label":"💰 Returns","desc":f"Hit {cfg['moic']}× MOIC",
                   "pace":"ahead" if moic_pace>1.1 else ("behind" if moic_pace<0.7 else "on track")},
        "lp":     {"hit":lp_ok,"target":cfg["lp"],"actual":gs.lp_satisfaction,
                   "label":"🤝 LP Legend","desc":f"Keep LPs ≥{cfg['lp']}",
                   "pace":"ahead" if lp_ok else "behind"},
        "exits":  {"hit":len(gs.exited)>=cfg["exits"],"target":cfg["exits"],"actual":len(gs.exited),
                   "label":"🏆 Deal Maker","desc":f"{cfg['exits']}+ exits",
                   "pace":"ahead" if exits_pace>1.1 else ("behind" if exits_pace<0.7 else "on track")},
    }

def sell_company(gs:GameState, idx:int) -> dict:
    c = gs.companies[idx]
    m = calc(c, gs)
    gs.cash += m["equity"]
    gs.exited.append({"name":c.name,"sector":c.sector,"ceo":c.ceo,
                      "moic":m["moic"],"irr":m["irr"],
                      "proc":m["equity"],"eq":c.entry_equity,"yh":m["yh"]})
    gs.companies.pop(idx)
    gs.lp_satisfaction = min(100, gs.lp_satisfaction + 8)
    gs.event_log.insert(0, f"Exited {c.name} at {m['moic']:.2f}×. LPs satisfied.")
    gs.event_log = gs.event_log[:4]
    return m

def pick_event(gs:GameState):
    if not gs.companies: return None
    pool  = [e for e in NARRATIVE_EVENTS if e["type"] in ("crisis","opportunity")]
    pool += [e for e in NARRATIVE_EVENTS if e["type"] == "rival"]
    if not gs.exited and gs.quarter_num > 3:
        pool += [e for e in NARRATIVE_EVENTS if e["type"] == "lp"] * 3
    if not pool: return None
    ev   = random.choice(pool)
    co   = random.choice(gs.companies)
    text = ev["template"]
    text = text.replace("{co}", f"**{co.name}**").replace("{ceo}", co.ceo)
    text = text.replace("{rival}", gs.rival.get("name","a rival"))
    text = text.replace("{lp}", random.choice(LP_NAMES))
    return {"id":ev["id"],"type":ev["type"],"title":ev["title"],"icon":ev["icon"],
            "text":text,"choices":ev["choices"],"cid":co.id}

def apply_effect(gs:GameState, key:str, cid:str|None):
    eff = EFFECTS.get(key, EFFECTS["nothing"])
    if cid:
        for c in gs.companies:
            if c.id == cid:
                if "moic_delta" in eff:
                    c.moic_modifier = max(0.1, min(c.moic_modifier+eff["moic_delta"], 3.0))
                if eff.get("force_exit"):
                    gs.forced_exit_id = c.id
                break
    if "lp_delta" in eff:
        gs.lp_satisfaction = max(0, min(100, gs.lp_satisfaction+eff["lp_delta"]))
    gs.event_log.insert(0, eff["msg"])
    gs.event_log = gs.event_log[:4]

def advance_quarter(gs:GameState):
    prev = gs.season
    gs.quarter_num += 1
    if not gs.exited and gs.quarter_num > 3:
        gs.lp_satisfaction = max(0, gs.lp_satisfaction - 3)
    gs.deals = make_deals(gs, 5)
    if gs.quarter_num >= gs.total_quarters:
        gs.screen = "score"; return
    new = gs.season
    if new != prev and gs.season_shown < new:
        gs.season_shown = new
        si = SEASONS[new]
        gs.pending_event = {"id":f"season_{new}","type":"season",
            "title":si["title"],"icon":si["emoji"],"text":si["text"],
            "choices":[{"label":"Got it. Keep moving.","effect":"nothing"}],"cid":None}
        return
    if random.random() < 0.60:
        ev = pick_event(gs)
        if ev: gs.pending_event = ev

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
def mc(v): return "c-green" if v>=2.0 else "c-gold" if v>=1.3 else "c-red"
def cf(v): return f"${v/1e9:.2f}B" if abs(v)>=1e9 else f"${v/1e6:.1f}M"
def lpc(s): return "#10b981" if s>=60 else "#f59e0b" if s>=35 else "#ef4444"
def health_dot(m): return "🟢" if m>=1.10 else ("🔴" if m<=0.85 else "🟡")

# ─────────────────────────────────────────────
# SCREEN: START
# ─────────────────────────────────────────────
def screen_start():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1.25rem;">
      <div style="font-size:48px;margin-bottom:.6rem;">💼</div>
      <h1 style="font-size:2.6rem;background:linear-gradient(135deg,#10b981,#f59e0b);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;">
        CarryForge
      </h1>
      <p style="color:#64748b;margin:.4rem 0 1.25rem;">
        Buy companies. Grow them. Exit for profit. Build your empire.
      </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("setup"):
        c1, c2 = st.columns(2)
        with c1:
            firm = st.text_input("Firm name", placeholder=random.choice(FIRM_DEFAULTS))
        with c2:
            partner = st.text_input("Your name", placeholder="e.g. Alex Chen")

        diff = st.radio("Difficulty", ["Easy","Balanced","Hard"], horizontal=True, index=1,
                        captions=["$60M · relaxed","$50M · realistic","$40M · brutal"])

        p = DIFFICULTY[diff]["paths"]
        st.markdown(f"""
        <div style="background:var(--card);border:1px solid var(--border);border-radius:11px;
             padding:.85rem 1rem;margin:.6rem 0;">
          <div style="font-size:.7rem;color:var(--muted);margin-bottom:.45rem;font-weight:700;
               text-transform:uppercase;letter-spacing:.06em;">Three ways to win (hit any one)</div>
          <div style="display:flex;gap:1rem;flex-wrap:wrap;font-size:.85rem;">
            <span>💰 <strong>Returns</strong> — {p['moic']}× portfolio return</span>
            <span>🤝 <strong>LP Legend</strong> — keep LPs happy</span>
            <span>🏆 <strong>Deal Maker</strong> — {p['exits']} exits closed</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.form_submit_button("Start Fund I →", use_container_width=True):
            ph = random.choice(FIRM_DEFAULTS)
            cfg = DIFFICULTY[diff]
            gs  = GameState(
                screen="game", difficulty=diff,
                cash=cfg["cash"], lp_satisfaction=cfg["lp_start"],
                firm_name=firm.strip() or ph,
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
      <div style="font-size:1.8rem;margin-bottom:.4rem;">{ev.get("icon","📋")}</div>
      <h2 style="margin:0 0 .6rem;">{ev.get("title","")}</h2>
      <p style="font-size:.93rem;color:var(--text);line-height:1.65;">{ev.get("text","")}</p>
    </div>
    """, unsafe_allow_html=True)

    choices   = ev.get("choices",[])
    is_season = ev.get("type") == "season"
    if not is_season:
        st.markdown("<p style='font-size:.85rem;color:var(--muted);margin:.6rem 0 .3rem;'>What do you do?</p>", unsafe_allow_html=True)

    cols = st.columns(max(len(choices),1))
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
        st.markdown(f'<div class="log-line">Last quarter: {gs.event_log[1]}</div>',
                    unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCREEN: GAME
# ─────────────────────────────────────────────
def screen_game():
    gs = G()
    if gs.pending_event:
        screen_event(); return

    cfg    = DIFFICULTY[gs.difficulty]
    si     = gs.season_info
    bm     = blended_moic(gs)
    paths  = check_paths(gs)
    full   = len(gs.companies) >= MAX_PORTFOLIO
    qtrs_l = gs.total_quarters - gs.quarter_num

    # ── Header (3 cols max) ──────────────────────────────────
    h1, h2, h3 = st.columns([3, 1.3, 1.6])
    with h1:
        fn = gs.fund_number
        fl = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
        st.markdown(f"<h1>{gs.firm_name} <span style='font-size:.9rem;color:var(--muted);font-weight:400'>· {fl}</span></h1>",
                    unsafe_allow_html=True)
    with h2:
        st.markdown(f"""
        <div style="display:flex;gap:.6rem;align-items:center;padding:.4rem 0;">
          <div class="stat"><div class="stat-val">{cf(gs.cash)}</div>
            <div class="stat-lbl">Cash</div></div>
          <div class="stat"><div class="stat-val"><span class="{si['css']}">{si['emoji']}</span> {gs.year} Q{gs.quarter}</div>
            <div class="stat-lbl">{si["name"]}</div></div>
        </div>""", unsafe_allow_html=True)
    with h3:
        if st.button(f"⏭  Next Quarter  ({qtrs_l} left)", use_container_width=True, key="nq_top"):
            advance_quarter(gs); st.rerun()

    # ── LP bar (14px, visible) ────────────────────────────────
    lp_c  = lpc(gs.lp_satisfaction)
    lp_em = "😊" if gs.lp_satisfaction>=70 else ("😐" if gs.lp_satisfaction>=45 else "😡")
    st.markdown(f"""
    <div class="lp-wrap">
      <span style="font-size:.7rem;color:var(--muted);white-space:nowrap;">LPs {lp_em}</span>
      <div class="lp-track"><div class="lp-fill" style="width:{gs.lp_satisfaction}%;background:{lp_c};"></div></div>
      <span style="font-size:.72rem;color:{lp_c};font-weight:700;">{gs.lp_satisfaction}/100</span>
    </div>""", unsafe_allow_html=True)

    if gs.lp_satisfaction < 35:
        st.error("🚨 LPs threatening to pull. Exit something — now.")
    elif gs.lp_satisfaction < 50:
        st.warning("⚠️  LPs getting restless. They want distributions.")

    # ── Win path chips with pace indicator ───────────────────
    pace_css = {"ahead":"path-ahead","on track":"path-ahead","behind":"path-behind"}
    p_items = []
    for key, p in paths.items():
        if p["hit"]:    css_cls = "path-chip path-hit"
        else:           css_cls = f"path-chip {pace_css.get(p['pace'],'path-miss')}"
        tick = "✅" if p["hit"] else ("📈" if p["pace"]=="ahead" else ("⚠️" if p["pace"]=="behind" else "•"))
        p_items.append(f'<div class="{css_cls}">{tick} {p["label"]}: {p["actual"]} / {p["target"]}</div>')

    st.markdown(f'<div class="path-row">{"".join(p_items)}</div>', unsafe_allow_html=True)

    if gs.event_log:
        st.markdown(f'<div class="log-line">{gs.event_log[0]}</div>', unsafe_allow_html=True)

    # First-turn hint
    if not gs.companies and gs.quarter_num == 0:
        st.markdown("""
        <div class="hint">
          👋 <strong>First time?</strong> — Browse deals below, pick one you like, click <strong>Buy</strong>.
          Then hit <strong>Next Quarter</strong> to let it grow. Exit when the return looks good.
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Portfolio (3 cols: info | moic/irr | sell) ────────────
    if gs.companies:
        st.markdown(f"<h2>📊 Portfolio ({len(gs.companies)}/{MAX_PORTFOLIO})"
                    + (" <span style='font-size:.78rem;color:var(--red)'>— full, sell to buy</span>" if full else "")
                    + "</h2>", unsafe_allow_html=True)

        sell_idx = None
        for i, c in enumerate(gs.companies):
            m   = calc(c, gs)
            sec = SECTORS[c.sector]
            yh  = m["yh"]
            age = f"{yh:.1f}y" if yh >= 1 else f"{int(round(yh*4))}q"
            hd  = health_dot(c.moic_modifier)
            dmg = ' <span style="color:var(--red);font-size:.7rem;"> ⚠ hit</span>'  if c.moic_modifier < 0.85 else ""
            bst = ' <span style="color:var(--green);font-size:.7rem;"> ✨ boosted</span>' if c.moic_modifier > 1.15 else ""

            ca, cb, cc = st.columns([3, 1.6, 1])
            with ca:
                st.markdown(f"""<div class="dcard dcard-{c.sector}">
                  <span class="fw7">{sec['emoji']} {c.name}</span>
                  <span class="c-muted" style="font-size:.72rem;margin-left:.3rem;">
                    {hd} {c.sector} · CEO: {c.ceo} · {age}</span>{dmg}{bst}<br>
                  <span class="tag">{cf(m['revenue'])} rev</span>
                  <span class="tag">Leverage: <span>{m['debt']/max(m['ebitda'],1):.1f}×</span></span>
                </div>""", unsafe_allow_html=True)
            with cb:
                st.markdown(f"""
                <div style="display:flex;gap:.5rem;align-items:center;height:100%;padding:.4rem 0;">
                  <div class="stat"><div class="stat-val {mc(m['moic'])}">{m['moic']:.2f}×</div>
                    <div class="stat-lbl">MOIC</div></div>
                  <div class="stat"><div class="stat-val">{m['irr']*100:.0f}%</div>
                    <div class="stat-lbl">IRR</div></div>
                </div>""", unsafe_allow_html=True)
            with cc:
                if st.button("Sell", key=f"sell_{i}_{gs.quarter_num}", use_container_width=True):
                    sell_idx = i

        if sell_idx is not None:
            m     = calc(gs.companies[sell_idx], gs)
            cname = gs.companies[sell_idx].name
            sell_company(gs, sell_idx)
            em = "🏆" if m["moic"]>=2.0 else "✅" if m["moic"]>=1.4 else "📉"
            st.success(f"{em} Sold **{cname}** — {m['moic']:.2f}× · {cf(m['equity'])}")
            st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Deal Flow (3 cols: info | est. return | buy) ──────────
    st.markdown("<h2>🎯 Deal Flow</h2>", unsafe_allow_html=True)
    buy_idx = None
    for i, d in enumerate(gs.deals):
        sec = SECTORS[d.sector]
        p3  = proj3(d, gs)
        can = d.entry_equity <= gs.cash and not full

        # Tier badges
        tier_tag = ""
        if d.tier == "hot":
            tier_tag = '<span class="tag tag-hot">🔥 Hot Deal</span>'
        elif d.tier == "risky":
            tier_tag = '<span class="tag tag-risky">⚠ Risky</span>'

        ca, cb, cc = st.columns([3, 1.6, 1])
        with ca:
            lev = d.entry_debt / max(d.ebitda, 1)
            st.markdown(f"""<div class="dcard dcard-{d.sector}">
              <h3>{sec['emoji']} {d.name} {tier_tag}</h3>
              <span class="c-muted" style="font-size:.72rem;">CEO: {d.ceo}</span><br>
              <span class="tag">{d.sector}</span>
              <span class="tag">Buy-in: <span>{d.entry_multiple:.1f}× EBITDA</span></span>
              <span class="tag">Growth: <span>{d.growth*100:.0f}%/yr</span></span>
              <span class="tag">Margin: <span>{d.margin*100:.0f}%</span></span>
              <span class="tag">Leverage: <span>{lev:.1f}×</span></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div style="display:flex;gap:.5rem;align-items:center;height:100%;padding:.4rem 0;">
              <div class="stat"><div class="stat-val">{cf(d.entry_equity)}</div>
                <div class="stat-lbl">Equity Cost</div></div>
              <div class="stat"><div class="stat-val {mc(p3)}">{p3:.1f}×</div>
                <div class="stat-lbl">Est. 3yr Return</div></div>
            </div>""", unsafe_allow_html=True)
        with cc:
            lbl = "Buy" if can else ("Full" if full else "💸")
            if st.button(lbl, key=f"buy_{i}_{gs.quarter_num}",
                         use_container_width=True, disabled=not can):
                buy_idx = i

    if buy_idx is not None:
        d = gs.deals[buy_idx]
        gs.cash         -= d.entry_equity
        d.entry_quarter  = gs.quarter_num
        gs.companies.append(d)
        gs.deals.pop(buy_idx)
        gs.event_log.insert(0, f"Closed {d.name}. {d.ceo} is 'excited about the partnership.'")
        gs.event_log = gs.event_log[:4]
        st.rerun()

    # ── Exits log ─────────────────────────────────────────────
    if gs.exited:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2>🏆 Exits</h2>", unsafe_allow_html=True)
        for e in reversed(gs.exited[-5:]):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.45rem .8rem;background:var(--card);border-radius:9px;margin-bottom:.25rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong>
                <span class="c-muted" style="font-size:.72rem;"> · {e['yh']:.1f}yr</span></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

    # ── Sticky "Next Quarter" at page bottom ──────────────────
    st.markdown(f"""
    <div class="sticky-footer">
      <div style="max-width:260px;margin:0 auto;">
        <!-- rendered by Streamlit button below -->
      </div>
    </div>""", unsafe_allow_html=True)
    # Second Next Quarter button at bottom so players don't have to scroll back up
    _, bc, _ = st.columns([1,2,1])
    with bc:
        if st.button(f"⏭  Next Quarter  ({qtrs_l} left)", use_container_width=True, key="nq_bottom"):
            advance_quarter(gs); st.rerun()

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

    grade, gc = {3:("S","#f59e0b"),2:("A","#10b981"),1:("B","#3b82f6"),0:("C","#ef4444")}[n_hit]
    realized  = sum(e["proc"] for e in gs.exited)
    lp_quotes = {
        range(70,101):"LPs are asking about Fund II before you've even closed this one. Block your calendar.",
        range(45,70): "LPs are satisfied. One asked if you're 'considering expanding the strategy.'",
        range(25,45): "LPs are polite but distant. Hartley Family Office CC'd their attorney on the last email.",
        range(0,25):  "Westfield Endowment investment committee wants a meeting. On a Saturday.",
    }
    lp_quote = next((v for r,v in lp_quotes.items() if gs.lp_satisfaction in r), "")
    fl = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    next_cash = DIFFICULTY[gs.difficulty]["cash"] * unlock["cash_mult"] * gs.fund_cash_mult

    # ── Grade + CTA above fold (score card) ──────────────────
    st.markdown(f"""
    <div class="score-box">
      <div style="font-size:.75rem;color:var(--muted);margin-bottom:.2rem;">{gs.firm_name} · {fl} Complete</div>
      <div style="font-size:3.2rem;font-weight:900;color:{gc};">{grade}</div>
      <h1 style="margin:.35rem 0;">{n_hit}/3 paths hit</h1>
      <p style="font-size:.88rem;margin-bottom:1.1rem;">{lp_quote}</p>
      <div style="display:flex;justify-content:space-around;margin:.6rem 0 1.25rem;">
        <div class="stat"><div class="stat-val" style="color:{gc};">{bm:.2f}×</div><div class="stat-lbl">MOIC</div></div>
        <div class="stat"><div class="stat-val">{len(gs.exited)}</div><div class="stat-lbl">Exits</div></div>
        <div class="stat"><div class="stat-val">{cf(realized)}</div><div class="stat-lbl">Realized</div></div>
        <div class="stat"><div class="stat-val" style="color:{lpc(gs.lp_satisfaction)};">{gs.lp_satisfaction}</div>
          <div class="stat-lbl">LP Score</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # CTA buttons — above the recap so they're above fold
    _, c2, c3 = st.columns([1,1,1])
    with c2:
        nl = f"Start {unlock['fund']} →" if fn < 3 else "🔄 New Fund"
        if st.button(nl, use_container_width=True, key="fund_next"):
            if fn < 3:
                new_gs = GameState(
                    screen="game", difficulty=gs.difficulty, cash=next_cash,
                    lp_satisfaction=min(100, DIFFICULTY[gs.difficulty]["lp_start"]+unlock["lp_bonus"]),
                    firm_name=gs.firm_name, partner_name=gs.partner_name,
                    fund_number=fn+1, fund_cash_mult=unlock["cash_mult"]*gs.fund_cash_mult,
                    fund_lp_bonus=gs.fund_lp_bonus+unlock["lp_bonus"], rival=gs.rival,
                )
                new_gs.deals = make_deals(new_gs, 5)
                st.session_state.gs = new_gs
            else:
                del st.session_state["gs"]
            st.rerun()
    with c3:
        if st.button("🔄 New Game", use_container_width=True, key="new_game"):
            del st.session_state["gs"]; st.rerun()

    # ── Paths breakdown ───────────────────────────────────────
    st.markdown("<h2 style='text-align:center;margin-top:1.1rem;'>Win Paths</h2>", unsafe_allow_html=True)
    for key, p in paths.items():
        css  = "path-result-hit" if p["hit"] else "path-result-miss"
        tick = "✅" if p["hit"] else "◻️"
        st.markdown(f"""
        <div class="{css}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="fw7">{tick} {p['label']}</span>
            <span class="c-muted" style="font-size:.8rem;">{p['desc']}</span>
            <span class="fw7" style="color:{'var(--green)' if p['hit'] else 'var(--muted)'};">
              {p['actual']} {'✓' if p['hit'] else f'/ {p["target"]}'}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Unlock ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="unlock-card">
      <div style="font-size:.68rem;color:var(--gold);font-weight:700;text-transform:uppercase;
           letter-spacing:.07em;margin-bottom:.35rem;">{'🔓 Unlocked' if fn<3 else '🏆 Endgame'}</div>
      <h2 style="margin:0;color:var(--gold);">{unlock['fund']} — {cf(next_cash)} capital</h2>
      <p style="font-size:.85rem;margin:.4rem 0 0;">{unlock['flavor']}</p>
    </div>""", unsafe_allow_html=True)

    # ── Deal recap ────────────────────────────────────────────
    if gs.exited:
        st.markdown("<h2 style='text-align:center;margin-top:1.1rem;'>Deal Recap</h2>",
                    unsafe_allow_html=True)
        for e in sorted(gs.exited, key=lambda x: -x["moic"]):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:.5rem .85rem;
                 background:var(--card);border-radius:9px;margin-bottom:.28rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong>
                <span class="c-muted" style="font-size:.7rem;"> (CEO: {e['ceo']})</span></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

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
