"""
CarryForge v10.0
================
- Sound: injects Web Audio API into window.parent (fixes height=0 iframe silence)
- Nav:   fixed BitLife-style bottom bar via window.parent injection +
         React input bridge for tab state changes
- Layout: 5 tabs (Home / Deals / Portfolio / Events / Fund), each focused
"""

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import random
from dataclasses import dataclass, field

st.set_page_config(page_title="CarryForge", page_icon="💼",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
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
  /* room for bottom nav */
  .block-container{padding:.9rem 1rem 5.5rem;max-width:960px;margin:0 auto;}

  h1{font-size:1.6rem;font-weight:800;margin:0;}
  h2{font-size:1.1rem;font-weight:700;margin:.75rem 0 .4rem;}
  h3{font-size:.92rem;font-weight:600;margin:0;}

  /* hide the tab-bus input */
  div[data-testid="stTextInput"]{display:none!important;}

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

  hr{border-color:var(--border);margin:.6rem 0;}

  .stat{text-align:center;}
  .stat-val{font-size:1.2rem;font-weight:800;color:var(--text);line-height:1.2;}
  .stat-lbl{font-size:.6rem;font-weight:600;color:var(--muted);text-transform:uppercase;
             letter-spacing:.07em;margin-top:.1rem;}

  .dcard{background:var(--card);border:1px solid var(--border);
         border-left:3px solid transparent;border-radius:12px;
         padding:.8rem .95rem;margin-bottom:.4rem;}
  .dcard-SaaS{border-left-color:var(--blue);}
  .dcard-Hardware{border-left-color:var(--purple);}
  .dcard-Healthcare{border-left-color:var(--pink);}
  .dcard-Fintech{border-left-color:var(--teal);}

  .tag{display:inline-block;background:var(--card2);border:1px solid var(--border);
       border-radius:5px;padding:.15rem .42rem;font-size:.7rem;font-weight:600;
       color:var(--muted);margin:2px;}
  .tag span{color:var(--text);}
  .tag-hot{background:rgba(245,158,11,.12);border-color:var(--gold);color:var(--gold);}
  .tag-risky{background:rgba(239,68,68,.1);border-color:var(--red);color:var(--red);}

  .path-chip{border-radius:7px;padding:.28rem .6rem;font-size:.7rem;font-weight:700;
             border:1px solid;display:inline-block;margin:2px;}
  .path-hit{background:rgba(16,185,129,.12);border-color:var(--green);color:var(--green);}
  .path-miss{background:var(--card2);border-color:var(--border);color:var(--muted);}
  .path-ahead{background:rgba(16,185,129,.07);border-color:rgba(16,185,129,.3);color:#6ee7b7;}
  .path-behind{background:rgba(239,68,68,.07);border-color:rgba(239,68,68,.3);color:#fca5a5;}

  .lp-wrap{display:flex;align-items:center;gap:.5rem;margin:.35rem 0;}
  .lp-track{flex:1;height:14px;background:var(--card2);border-radius:999px;overflow:hidden;}
  .lp-fill{height:14px;border-radius:999px;transition:width .4s ease;}

  .ev-card{background:var(--card);border:1px solid;border-radius:14px;
           padding:1rem 1.1rem;margin:.4rem 0;}
  .ev-crisis{border-color:#ef4444;background:rgba(239,68,68,.06);}
  .ev-opportunity{border-color:#10b981;background:rgba(16,185,129,.06);}
  .ev-rival{border-color:#8b5cf6;background:rgba(139,92,246,.06);}
  .ev-lp{border-color:#f59e0b;background:rgba(245,158,11,.06);}
  .ev-season{border-color:#3b82f6;background:rgba(59,130,246,.08);}

  .choice-btn button{
    background:var(--card2)!important;border:1px solid var(--border)!important;
    color:var(--text)!important;box-shadow:none!important;
  }
  .choice-btn button:hover{border-color:var(--green)!important;color:var(--green)!important;
    transform:none!important;}

  .score-box{background:var(--card);border:1px solid var(--border);border-radius:18px;
             padding:1.6rem;text-align:center;max-width:480px;margin:.8rem auto;}
  .unlock-card{background:var(--card);border:1px solid rgba(245,158,11,.35);
               border-radius:14px;padding:1rem;margin:.5rem 0;text-align:center;}
  .path-result-hit{background:rgba(16,185,129,.12);border:1px solid var(--green);
               border-radius:10px;padding:.5rem .85rem;margin:.22rem 0;}
  .path-result-miss{background:var(--card2);border:1px solid var(--border);
               border-radius:10px;padding:.5rem .85rem;margin:.22rem 0;opacity:.5;}

  .s1{color:#10b981;font-weight:700;} .s2{color:#f59e0b;font-weight:700;} .s3{color:#ef4444;font-weight:700;}
  .hint{background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.25);
        border-radius:10px;padding:.6rem .85rem;font-size:.83rem;color:#93c5fd;margin:.45rem 0;}
  .log-line{padding:.38rem .75rem;background:var(--card2);border-radius:8px;
            font-size:.79rem;color:var(--muted);margin:.18rem 0;}

  .c-green{color:var(--green)!important;font-weight:700;}
  .c-gold{color:var(--gold)!important;font-weight:700;}
  .c-red{color:var(--red)!important;font-weight:700;}
  .c-muted{color:var(--muted)!important;}
  .fw7{font-weight:700;}

  @media(max-width:640px){
    .block-container{padding:.65rem .65rem 5.5rem;}
    .stat-val{font-size:1rem;}
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
        st.session_state.gs=GameState()
    return st.session_state.gs

def get_tab() -> str:
    return st.session_state.get("tab","home")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def mc(v): return "c-green" if v>=2.0 else "c-gold" if v>=1.3 else "c-red"
def cf(v): return f"${v/1e9:.2f}B" if abs(v)>=1e9 else f"${v/1e6:.1f}M"
def lpc(s): return "#10b981" if s>=60 else "#f59e0b" if s>=35 else "#ef4444"
def hdot(m): return "🟢" if m>=1.10 else ("🔴" if m<=0.85 else "🟡")

# ─────────────────────────────────────────────
# SOUND + BOTTOM NAV  (injected into window.parent)
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

def flush_sounds(gs:GameState, extra:str=""):
    """Play queued sounds by injecting audio engine into window.parent."""
    snds = list(gs.sound_queue)
    if extra: snds.append(extra)
    gs.sound_queue = []
    calls = "".join(f"window._cfPlay('{s}');" for s in snds)
    if not calls: return
    # height=50 ensures the iframe is active and scripts execute
    components.html(f"""
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
    <div style="height:1px;background:transparent;"></div>
    """, height=50, scrolling=False)


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

    components.html(f"""
    <script>
    (function() {{
      var TABS = {nav_items_js};
      var active = "{active_js}";
      var hasBadge = {badge_js};

      // Helper: trigger a React-controlled input change in the parent frame
      function setParentInput(newVal) {{
        var inputs = window.parent.document.querySelectorAll('input[data-testid="stTextInput-Input"]');
        if (!inputs.length) {{
          inputs = window.parent.document.querySelectorAll('input[type="text"]');
        }}
        var inp = inputs[0];
        if (!inp) return;
        var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, newVal);
        inp.dispatchEvent(new window.parent.Event('input', {{bubbles: true}}));
      }}

      // Remove stale nav if it exists and active tab changed
      var existing = window.parent.document.getElementById('_cf_nav');
      if (existing) {{
        var cur = existing.getAttribute('data-active');
        if (cur === active) return;   // no change needed, skip re-render
        existing.remove();
      }}

      // Build nav bar
      var nav = window.parent.document.createElement('div');
      nav.id = '_cf_nav';
      nav.setAttribute('data-active', active);

      var style = `
        position: fixed;
        bottom: 0; left: 0; right: 0;
        background: #0d1223;
        border-top: 1px solid rgba(255,255,255,.1);
        display: flex;
        z-index: 99999;
        padding: 6px 0 max(8px, env(safe-area-inset-bottom));
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      `;
      nav.style.cssText = style;

      TABS.forEach(function(tab) {{
        var key = tab[0], icon = tab[1], label = tab[2];
        var isActive = (key === active);
        var item = window.parent.document.createElement('button');
        item.setAttribute('data-tab', key);
        item.innerHTML = '<span style="font-size:1.3rem;display:block;line-height:1;">'
          + icon
          + (key==='events' && hasBadge ? '<sup style="font-size:.5rem;color:#ef4444;vertical-align:super;">●</sup>' : '')
          + '</span>'
          + '<span style="font-size:.58rem;display:block;margin-top:2px;font-weight:' + (isActive?'700':'500') + ';">'
          + label
          + '</span>';

        item.style.cssText = [
          'flex:1',
          'background:none',
          'border:none',
          'color:' + (isActive ? '#10b981' : '#64748b'),
          'cursor:pointer',
          'padding:4px 2px',
          'transition:color .2s',
          'outline:none',
          '-webkit-tap-highlight-color:transparent',
        ].join(';');

        item.addEventListener('click', function() {{
          setParentInput(key);
        }});

        nav.appendChild(item);
      }});

      window.parent.document.body.appendChild(nav);
    }})();
    </script>
    <div style="height:1px;background:transparent;"></div>
    """, height=50, scrolling=False)


# ─────────────────────────────────────────────
# SHARED HEADER (always shown in game)
# ─────────────────────────────────────────────
def render_header(gs:GameState):
    si = gs.season_info
    bm = blended_moic(gs)
    fn = gs.fund_number
    fl = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    qtrs_l = gs.total_quarters - gs.quarter_num

    c1, c2, c3, c4 = st.columns([2.5, 1.1, 1.1, 1.6])
    with c1:
        st.markdown(f"<h1>{gs.firm_name} <span style='font-size:.85rem;color:var(--muted);font-weight:400'>· {fl}</span></h1>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat"><div class="stat-val">{cf(gs.cash)}</div>
          <div class="stat-lbl">Cash</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat">
          <div class="stat-val"><span class="{si['css']}">{si['emoji']}</span> {gs.year} Q{gs.quarter}</div>
          <div class="stat-lbl">{si['name']}</div></div>""", unsafe_allow_html=True)
    with c4:
        if st.button(f"⏭ Next Q ({qtrs_l})", use_container_width=True, key="nq"):
            advance_quarter(gs); st.rerun()

    lp_c = lpc(gs.lp_satisfaction)
    lp_em = "😊" if gs.lp_satisfaction>=70 else ("😐" if gs.lp_satisfaction>=45 else "😡")
    st.markdown(f"""
    <div class="lp-wrap">
      <span style="font-size:.68rem;color:var(--muted);white-space:nowrap;">{lp_em} LPs</span>
      <div class="lp-track"><div class="lp-fill" style="width:{gs.lp_satisfaction}%;background:{lp_c};"></div></div>
      <span style="font-size:.7rem;color:{lp_c};font-weight:700;">{gs.lp_satisfaction}/100</span>
    </div>""", unsafe_allow_html=True)

    if gs.lp_satisfaction < 35:   st.error("🚨 LPs threatening to pull. Exit something now.")
    elif gs.lp_satisfaction < 50: st.warning("⚠️ LPs getting restless.")

    paths = check_paths(gs)
    chips = []
    for p in paths.values():
        if p["hit"]: cls = "path-hit"
        elif p["pace"] == "ahead": cls = "path-ahead"
        elif p["pace"] == "behind": cls = "path-behind"
        else: cls = "path-miss"
        tick = "✅" if p["hit"] else ("📈" if p["pace"]=="ahead" else "⚠️")
        chips.append(f'<span class="path-chip {cls}">{tick} {p["label"]}: {p["actual"]}/{p["target"]}</span>')
    st.markdown(" ".join(chips), unsafe_allow_html=True)

    if gs.event_log:
        st.markdown(f'<div class="log-line">{gs.event_log[0]}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TAB: HOME
# ─────────────────────────────────────────────
def tab_home(gs:GameState):
    st.markdown("<hr>", unsafe_allow_html=True)
    bm = blended_moic(gs)
    paths = check_paths(gs)
    n_hit = sum(1 for p in paths.values() if p["hit"])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="stat" style="background:var(--card);border-radius:12px;padding:.9rem;">
          <div class="stat-val {mc(bm)}">{bm:.2f}×</div>
          <div class="stat-lbl">Blended MOIC</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat" style="background:var(--card);border-radius:12px;padding:.9rem;">
          <div class="stat-val">{len(gs.exited)}</div>
          <div class="stat-lbl">Exits</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat" style="background:var(--card);border-radius:12px;padding:.9rem;">
          <div class="stat-val" style="color:{'#10b981' if n_hit>0 else '#64748b'};">{n_hit}/3</div>
          <div class="stat-lbl">Paths Hit</div></div>""", unsafe_allow_html=True)

    if not gs.companies and gs.quarter_num == 0:
        st.markdown("""<div class="hint">👋 <strong>Welcome!</strong> Go to <strong>Deals</strong> tab to buy your first company.
          Hit <strong>Next Q</strong> to advance time. Sell when returns look good.</div>""", unsafe_allow_html=True)

    if gs.companies:
        st.markdown("<h2>📊 Portfolio Summary</h2>", unsafe_allow_html=True)
        for c in gs.companies:
            m = calc(c, gs)
            sec = SECTORS[c.sector]
            yh = m["yh"]; age = f"{yh:.1f}y" if yh>=1 else f"{int(round(yh*4))}q"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.5rem .85rem;background:var(--card);border-radius:9px;margin-bottom:.28rem;">
              <span>{sec['emoji']} <strong>{c.name}</strong>
                <span class="c-muted" style="font-size:.7rem;"> · {age}</span></span>
              <span class="{mc(m['moic'])}">{m['moic']:.2f}×</span>
              <span class="c-muted">{m['irr']*100:.0f}% IRR</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB: DEALS
# ─────────────────────────────────────────────
def tab_deals(gs:GameState):
    full = len(gs.companies) >= MAX_PORTFOLIO
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<h2>🎯 Deal Flow</h2>" +
                (" <span style='font-size:.78rem;color:var(--red)'>Portfolio full — sell first</span>" if full else ""),
                unsafe_allow_html=True)
    buy_idx = None
    for i, d in enumerate(gs.deals):
        sec = SECTORS[d.sector]
        p3 = proj3(d, gs)
        can = d.entry_equity <= gs.cash and not full
        tier_tag = '<span class="tag tag-hot">🔥 Hot</span>' if d.tier=="hot" else \
                   ('<span class="tag tag-risky">⚠ Risky</span>' if d.tier=="risky" else "")
        lev = d.entry_debt / max(d.ebitda, 1)

        ca, cb, cc = st.columns([3, 1.6, 1])
        with ca:
            st.markdown(f"""<div class="dcard dcard-{d.sector}">
              <h3>{sec['emoji']} {d.name} {tier_tag}</h3>
              <span class="c-muted" style="font-size:.7rem;">CEO: {d.ceo}</span><br>
              <span class="tag">{d.sector}</span>
              <span class="tag">In: <span>{d.entry_multiple:.1f}×</span></span>
              <span class="tag">Growth: <span>{d.growth*100:.0f}%</span></span>
              <span class="tag">Margin: <span>{d.margin*100:.0f}%</span></span>
              <span class="tag">Lev: <span>{lev:.1f}×</span></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div style="display:flex;gap:.5rem;align-items:center;height:100%;padding:.35rem 0;">
              <div class="stat"><div class="stat-val">{cf(d.entry_equity)}</div>
                <div class="stat-lbl">Equity</div></div>
              <div class="stat"><div class="stat-val {mc(p3)}">{p3:.1f}×</div>
                <div class="stat-lbl">Est 3yr</div></div>
            </div>""", unsafe_allow_html=True)
        with cc:
            lbl = "Buy" if can else ("Full" if full else "💸")
            if st.button(lbl, key=f"buy_{i}_{gs.quarter_num}", use_container_width=True, disabled=not can):
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
    full = len(gs.companies) >= MAX_PORTFOLIO
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<h2>📊 Portfolio ({len(gs.companies)}/{MAX_PORTFOLIO})</h2>", unsafe_allow_html=True)

    if not gs.companies:
        st.info("No portfolio companies yet — go to Deals to invest.")
        return

    sell_idx = None
    for i, c in enumerate(gs.companies):
        m = calc(c, gs)
        sec = SECTORS[c.sector]
        yh = m["yh"]; age = f"{yh:.1f}y" if yh>=1 else f"{int(round(yh*4))}q"
        hd = hdot(c.moic_modifier)
        dmg = ' <span style="color:var(--red);font-size:.7rem;"> ⚠ hit</span>' if c.moic_modifier<0.85 else ""
        bst = ' <span style="color:var(--green);font-size:.7rem;"> ✨ boosted</span>' if c.moic_modifier>1.15 else ""

        ca, cb, cc = st.columns([3, 1.6, 1])
        with ca:
            st.markdown(f"""<div class="dcard dcard-{c.sector}">
              <span class="fw7">{sec['emoji']} {c.name}</span>
              <span class="c-muted" style="font-size:.7rem;margin-left:.3rem;">
                {hd} {c.sector} · {c.ceo} · {age}</span>{dmg}{bst}<br>
              <span class="tag">{cf(m['revenue'])} rev</span>
              <span class="tag">Lev: <span>{m['debt']/max(m['ebitda'],1):.1f}×</span></span>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div style="display:flex;gap:.5rem;align-items:center;height:100%;padding:.35rem 0;">
              <div class="stat"><div class="stat-val {mc(m['moic'])}">{m['moic']:.2f}×</div>
                <div class="stat-lbl">MOIC</div></div>
              <div class="stat"><div class="stat-val">{m['irr']*100:.0f}%</div>
                <div class="stat-lbl">IRR</div></div>
            </div>""", unsafe_allow_html=True)
        with cc:
            if st.button("Sell", key=f"sell_{i}_{gs.quarter_num}", use_container_width=True):
                sell_idx = i

    if sell_idx is not None:
        m = calc(gs.companies[sell_idx], gs)
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
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h2>📣 Events & History</h2>", unsafe_allow_html=True)
    if gs.event_log:
        for msg in gs.event_log:
            st.markdown(f'<div class="log-line">• {msg}</div>', unsafe_allow_html=True)
    else:
        st.info("No events yet.")
    if gs.exited:
        st.markdown("<h2>🏆 Exits</h2>", unsafe_allow_html=True)
        for e in reversed(gs.exited):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:.45rem .8rem;background:var(--card);border-radius:9px;margin-bottom:.25rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong>
                <span class="c-muted" style="font-size:.7rem;"> · {e['yh']:.1f}yr</span></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB: FUND
# ─────────────────────────────────────────────
def tab_fund(gs:GameState):
    st.markdown("<hr>", unsafe_allow_html=True)
    cfg = DIFFICULTY[gs.difficulty]
    paths = check_paths(gs)
    fn = gs.fund_number
    fl = f"Fund {'I' if fn==1 else 'II' if fn==2 else 'III'}"
    unlock = UNLOCKS[sum(1 for p in paths.values() if p["hit"])]
    next_cash = cfg["cash"] * unlock["cash_mult"] * gs.fund_cash_mult

    st.markdown(f"<h2>💰 {fl} · {gs.firm_name}</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Raised", cf(cfg["cash"] * gs.fund_cash_mult))
    c2.metric("Deployed", cf(cfg["cash"] * gs.fund_cash_mult - gs.cash))
    c3.metric("Realized", cf(sum(e["proc"] for e in gs.exited)))

    st.markdown("<h2>Win Paths</h2>", unsafe_allow_html=True)
    for p in paths.values():
        pct = min(p["actual"] / max(p["target"], 1), 1.0)
        bar_w = int(pct * 100)
        color = "#10b981" if p["hit"] else ("#f59e0b" if pct > 0.6 else "#64748b")
        tick = "✅" if p["hit"] else ""
        st.markdown(f"""
        <div style="margin:.4rem 0;">
          <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:.2rem;">
            <span>{tick} {p['label']}</span>
            <span style="color:{color};">{p['actual']} / {p['target']}</span>
          </div>
          <div style="background:var(--card2);border-radius:999px;height:8px;overflow:hidden;">
            <div style="width:{bar_w}%;height:8px;background:{color};border-radius:999px;transition:width .4s;"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""<div class="unlock-card">
      <div style="font-size:.68rem;color:var(--gold);font-weight:700;text-transform:uppercase;
           letter-spacing:.07em;margin-bottom:.3rem;">🔓 On Track For</div>
      <h2 style="margin:0;color:var(--gold);">{unlock['fund']} — {cf(next_cash)}</h2>
      <p style="font-size:.83rem;margin:.35rem 0 0;">{unlock['flavor']}</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("<h2>LPs</h2>", unsafe_allow_html=True)
    for lp_name in LP_NAMES:
        lp_happy = gs.lp_satisfaction >= 60
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:.45rem .8rem;
             background:var(--card);border-radius:9px;margin-bottom:.25rem;">
          <span>{lp_name}</span>
          <span style="color:{'#10b981' if lp_happy else '#f59e0b'};">
            {'Satisfied' if lp_happy else 'Restless'}</span>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# EVENT SCREEN (interrupts any tab)
# ─────────────────────────────────────────────
def screen_event(gs:GameState):
    ev = gs.pending_event
    css = {"crisis":"ev-crisis","opportunity":"ev-opportunity",
           "rival":"ev-rival","lp":"ev-lp","season":"ev-season"}.get(ev.get("type",""),"")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ev-card {css}">
      <div style="font-size:1.7rem;margin-bottom:.35rem;">{ev.get('icon','📋')}</div>
      <h2 style="margin:0 0 .55rem;">{ev.get('title','')}</h2>
      <p style="font-size:.91rem;color:var(--text);line-height:1.6;">{ev.get('text','')}</p>
    </div>""", unsafe_allow_html=True)

    choices = ev.get("choices", [])
    if ev.get("type") != "season":
        st.markdown("<p style='font-size:.83rem;color:var(--muted);margin:.5rem 0 .25rem;'>What do you do?</p>",
                    unsafe_allow_html=True)

    cols = st.columns(max(len(choices), 1))
    for i, ch in enumerate(choices):
        with cols[i]:
            st.markdown('<div class="choice-btn">', unsafe_allow_html=True)
            if st.button(ch["label"], key=f"ch_{i}_{gs.quarter_num}", use_container_width=True):
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
    <div style="text-align:center;padding:2rem 0 1.25rem;">
      <div style="font-size:46px;margin-bottom:.6rem;">💼</div>
      <h1 style="font-size:2.4rem;background:linear-gradient(135deg,#10b981,#f59e0b);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;">
        CarryForge
      </h1>
      <p style="color:#64748b;margin:.4rem 0 1.1rem;">Buy companies. Grow them. Exit for profit.</p>
    </div>""", unsafe_allow_html=True)

    with st.form("setup"):
        c1, c2 = st.columns(2)
        with c1: firm=st.text_input("Firm name",placeholder=random.choice(FIRM_DEFAULTS))
        with c2: partner=st.text_input("Your name",placeholder="e.g. Alex Chen")
        diff=st.radio("Difficulty",["Easy","Balanced","Hard"],horizontal=True,index=1,
                      captions=["$60M · relaxed","$50M · realistic","$40M · brutal"])
        p=DIFFICULTY[diff]["paths"]
        st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);
             border-radius:11px;padding:.8rem 1rem;margin:.55rem 0;">
          <div style="font-size:.68rem;color:var(--muted);margin-bottom:.4rem;font-weight:700;
               text-transform:uppercase;letter-spacing:.06em;">Three ways to win (hit any one)</div>
          <div style="display:flex;gap:1rem;flex-wrap:wrap;font-size:.83rem;">
            <span>💰 Hit {p['moic']}× MOIC</span>
            <span>🤝 Keep LPs ≥{p['lp']}</span>
            <span>🏆 {p['exits']} exits</span>
          </div></div>""", unsafe_allow_html=True)
        if st.form_submit_button("Start Fund I →", use_container_width=True):
            ph=random.choice(FIRM_DEFAULTS); cfg=DIFFICULTY[diff]
            gs=GameState(screen="game",difficulty=diff,cash=cfg["cash"],
                lp_satisfaction=cfg["lp_start"],
                firm_name=firm.strip() or ph,
                partner_name=partner.strip() or "Alex",
                rival=random.choice(RIVAL_FIRMS))
            gs.deals=make_deals(gs,5)
            st.session_state.gs=gs
            st.session_state.tab="home"
            st.session_state["score_sound_played"]=False
            st.rerun()


def screen_game():
    gs = G()

    # ── Tab bus: hidden text input that JS nav writes to ──────
    current_tab_raw = st.text_input("_tab", value=get_tab(), key="tab_input",
                                     label_visibility="collapsed")
    if current_tab_raw != get_tab():
        st.session_state["tab"] = current_tab_raw
        st.rerun()

    active_tab = get_tab()

    # ── Flush sounds first so they play ASAP after action ─────
    flush_sounds(gs)

    # ── Shared header ─────────────────────────────────────────
    render_header(gs)

    # ── Event interrupt ───────────────────────────────────────
    if gs.pending_event:
        screen_event(gs)
    else:
        # ── Tab content ───────────────────────────────────────
        if   active_tab == "home":      tab_home(gs)
        elif active_tab == "deals":     tab_deals(gs)
        elif active_tab == "portfolio": tab_portfolio(gs)
        elif active_tab == "events":    tab_events(gs)
        elif active_tab == "fund":      tab_fund(gs)

    # ── Bottom nav injection ──────────────────────────────────
    has_event = bool(gs.pending_event)
    inject_bottom_nav(active_tab, has_event=has_event)


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
    <div class="score-box">
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:.2rem;">{gs.firm_name} · {fl} Complete</div>
      <div style="font-size:3rem;font-weight:900;color:{gc};">{grade}</div>
      <h1 style="margin:.3rem 0;">{n_hit}/3 paths hit</h1>
      <p style="font-size:.86rem;margin-bottom:1rem;">{lp_quote}</p>
      <div style="display:flex;justify-content:space-around;margin:.5rem 0 1.1rem;">
        <div class="stat"><div class="stat-val" style="color:{gc};">{bm:.2f}×</div><div class="stat-lbl">MOIC</div></div>
        <div class="stat"><div class="stat-val">{len(gs.exited)}</div><div class="stat-lbl">Exits</div></div>
        <div class="stat"><div class="stat-val">{cf(realized)}</div><div class="stat-lbl">Realized</div></div>
        <div class="stat"><div class="stat-val" style="color:{lpc(gs.lp_satisfaction)};">{gs.lp_satisfaction}</div>
          <div class="stat-lbl">LPs</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    _, c2, c3 = st.columns([1,1,1])
    with c2:
        nl=f"Start {unlock['fund']} →" if fn<3 else "🔄 New Fund"
        if st.button(nl, use_container_width=True, key="fn"):
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
        if st.button("🔄 New Game", use_container_width=True, key="ng"):
            st.session_state["score_sound_played"]=False
            del st.session_state["gs"]; st.rerun()

    st.markdown("<h2 style='text-align:center;margin-top:1rem;'>Win Paths</h2>", unsafe_allow_html=True)
    for p in paths.values():
        css="path-result-hit" if p["hit"] else "path-result-miss"
        st.markdown(f"""<div class="{css}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="fw7">{'✅' if p['hit'] else '◻️'} {p['label']}</span>
            <span class="fw7" style="color:{'var(--green)' if p['hit'] else 'var(--muted)'};">
              {p['actual']} {'✓' if p['hit'] else f'/ {p["target"]}'}</span>
          </div></div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="unlock-card" style="margin-top:1rem;">
      <div style="font-size:.66rem;color:var(--gold);font-weight:700;text-transform:uppercase;
           letter-spacing:.07em;margin-bottom:.3rem;">{'🔓 Unlocked' if fn<3 else '🏆 Endgame'}</div>
      <h2 style="margin:0;color:var(--gold);">{unlock['fund']} — {cf(next_cash)}</h2>
      <p style="font-size:.83rem;margin:.35rem 0 0;">{unlock['flavor']}</p>
    </div>""", unsafe_allow_html=True)

    if gs.exited:
        st.markdown("<h2 style='text-align:center;margin-top:1rem;'>Deal Recap</h2>", unsafe_allow_html=True)
        for e in sorted(gs.exited,key=lambda x:-x["moic"]):
            st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:.48rem .8rem;
                 background:var(--card);border-radius:9px;margin-bottom:.25rem;">
              <span>{SECTORS[e['sector']]['emoji']} <strong>{e['name']}</strong></span>
              <span class="{mc(e['moic'])}">{e['moic']:.2f}×</span>
              <span class="c-muted">{e['irr']*100:.0f}% IRR · {cf(e['proc'])}</span>
            </div>""", unsafe_allow_html=True)


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
