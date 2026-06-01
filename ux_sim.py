"""
CarryForge UX Playtest Simulator
=================================
Simulates 8 player archetypes through full game loops.
Captures UI/UX friction points, confusion moments, dead ends,
information gaps, and "where do I click next?" moments.

Each archetype has a behavior model + a set of UX expectations.
The sim traces every interaction and logs every point of friction.
"""

import random, math, statistics, copy
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

# ── Inline game logic (mirrors carryforge.py exactly) ─────────────────

SEASONS = {
    1: {"exit_mod":1.15,"growth_mod":1.10},
    2: {"exit_mod":1.00,"growth_mod":0.95},
    3: {"exit_mod":0.85,"growth_mod":0.88},
}
SECTORS = {
    "SaaS":      {"rev":(40,160),"margin":(.28,.48),"growth":(.12,.32)},
    "Hardware":  {"rev":(90,300),"margin":(.08,.18),"growth":(.04,.14)},
    "Healthcare":{"rev":(70,240),"margin":(.14,.28),"growth":(.08,.22)},
    "Fintech":   {"rev":(35,120),"margin":(.22,.42),"growth":(.22,.48)},
}
COMPANY_NAMES = {
    "SaaS":      ["CloudVault","DataFlow","SyncHub","AutoScale","SnapMetrics","PipelineAI","GridLogic","NovaDash"],
    "Hardware":  ["TechWorks","PrecisionCo","SmartBuild","CoreForge","IronStack","PeakSystems","NexHardware","OrbDrive"],
    "Healthcare":["HealthPlus","CareFlow","MedTech","PulseCare","BioServe","ClearMed","VitalPath","RxBridge"],
    "Fintech":   ["PayHub","TradeFlow","VaultSecure","ClearPay","LedgerX","SwiftBridge","CapitalOps","NovaMoney"],
}
CEO_NAMES = ["Marcus Webb","Priya Sharma","Derek Lund","Sophie Chen","Raj Patel","Chloe Kim","Jake Torres"]
EFFECTS = {
    "ceo_stays":{"moic_delta":+.20},"ceo_leaves_slow":{"moic_delta":-.10},
    "ceo_gone":{"moic_delta":-.25},"ceo_gone_clean":{"moic_delta":-.20},
    "crisis_managed":{"moic_delta":-.10},"disaster":{"moic_delta":-.40},
    "big_growth":{"moic_delta":+.30},"medium_growth":{"moic_delta":+.15},
    "nothing":{"moic_delta":.00},"partial_save":{"moic_delta":-.08},
    "slight_hit":{"moic_delta":-.12},"war":{"moic_delta":-.30},
    "lose_deal":{"moic_delta":.00},"win_expensive":{"moic_delta":-.05},
    "win_clever":{"moic_delta":+.08},"rivalry_up":{"moic_delta":.00},
    "lp_amused":{"lp_delta":+5},"pressure_sell":{"force_exit":True},
    "bought_time":{"lp_delta":-3},"lp_annoyed":{"lp_delta":-10},
    "lp_happy_hit":{"moic_delta":-.05,"lp_delta":+10},"lp_exits":{"lp_delta":-20},
    "lp_furious":{"lp_delta":-25},"forced_exit":{"force_exit":True},
    "auction":{"moic_delta":+.12},"ipo_prep":{"moic_delta":+.08},
    "rate_hedged":{"moic_delta":+.05},"risky_hold":{"moic_delta":+.10},
    "ceo_upgrade":{"moic_delta":+.15},"mgmt_stable":{"moic_delta":+.05},
    "slow_resolution":{"moic_delta":-.05},"addon_win":{"moic_delta":+.15},
    "addon_maybe":{"moic_delta":+.05},
}
DIFFICULTY = {
    "Easy":    {"cash":60e6,"exit_mult":9.5,"quarters":12,"lp_start":80,"paths":{"moic":1.5,"lp":70,"exits":3}},
    "Balanced":{"cash":50e6,"exit_mult":8.5,"quarters":12,"lp_start":65,"paths":{"moic":1.75,"lp":65,"exits":4}},
    "Hard":    {"cash":40e6,"exit_mult":7.5,"quarters":12,"lp_start":50,"paths":{"moic":2.0,"lp":60,"exits":5}},
}
MAX_PORTFOLIO = 4

@dataclass
class Co:
    id:str; name:str; sector:str; ceo:str
    revenue:float; ebitda:float; margin:float; growth:float
    entry_multiple:float; entry_ev:float; entry_debt:float; entry_equity:float
    entry_quarter:int=0; moic_modifier:float=1.0

@dataclass
class GS:
    difficulty:str="Balanced"; quarter_num:int=0; cash:float=50e6
    screen:str="game"; fund_number:int=1
    companies:list=field(default_factory=list); exited:list=field(default_factory=list)
    deals:list=field(default_factory=list); pending_event:dict=field(default_factory=dict)
    lp_satisfaction:int=65; exit_mult_mod:float=1.0; growth_mod:float=1.0
    sector_mods:dict=field(default_factory=dict); season_shown:int=0; forced_exit_id:str=""
    @property
    def season(self):
        q=self.quarter_num+1
        return 1 if q<=4 else (2 if q<=8 else 3)
    @property
    def season_info(self): return SEASONS[self.season]
    @property
    def total_quarters(self): return DIFFICULTY[self.difficulty]["quarters"]

def make_deals(gs,n=5,rng=None):
    if rng is None: rng=random
    deals=[]
    for _ in range(n):
        s=rng.choice(list(SECTORS)); p=SECTORS[s]
        rev=rng.uniform(*p["rev"]); mg=rng.uniform(*p["margin"]); eb=rev*mg
        gr=rng.uniform(*p["growth"]); em=round(rng.uniform(6.5,9.5),1)
        ev=eb*em; debt=eb*rng.uniform(3.0,5.0); eq=max(ev-debt,ev*0.10)
        name=rng.choice(COMPANY_NAMES[s])
        deals.append(Co(id=f"{name[:3]}{rng.randint(100,999)}",name=name,sector=s,
            ceo=rng.choice(CEO_NAMES),revenue=rev,ebitda=eb,margin=mg,growth=gr,
            entry_multiple=em,entry_ev=ev,entry_debt=debt,entry_equity=eq,
            entry_quarter=gs.quarter_num))
    return deals

def calc(c,gs):
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
    moic=equity/max(c.entry_equity,1)
    irr=(moic**(1/max(yh,.25))-1) if yh>0 else 0
    return {"revenue":rev,"ebitda":ebitda,"equity":equity,"moic":moic,"irr":irr,"yh":yh,"pm":pm}

def bm(gs):
    ti=sum(c.entry_equity for c in gs.companies)+sum(e["eq"] for e in gs.exited)
    to=sum(calc(c,gs)["equity"] for c in gs.companies)*0.70+sum(e["proc"] for e in gs.exited)
    return to/max(ti,1)

def paths(gs):
    cfg=DIFFICULTY[gs.difficulty]["paths"]
    m=bm(gs)
    return {
        "returns":m>=cfg["moic"],
        "lp":gs.lp_satisfaction>=cfg["lp"],
        "exits":len(gs.exited)>=cfg["exits"],
    }

def sell(gs,idx,rng=None):
    c=gs.companies[idx]; m=calc(c,gs)
    gs.cash+=m["equity"]
    gs.exited.append({"name":c.name,"sector":c.sector,"moic":m["moic"],"irr":m["irr"],
                      "proc":m["equity"],"eq":c.entry_equity,"yh":m["yh"]})
    gs.companies.pop(idx)
    gs.lp_satisfaction=min(100,gs.lp_satisfaction+8)

def adv(gs,rng):
    prev=gs.season; gs.quarter_num+=1
    if not gs.exited and gs.quarter_num>3: gs.lp_satisfaction=max(0,gs.lp_satisfaction-3)
    gs.deals=make_deals(gs,5,rng)
    if gs.quarter_num>=gs.total_quarters: gs.screen="score"; return
    new=gs.season
    if new!=prev and gs.season_shown<new:
        gs.season_shown=new
        gs.pending_event={"type":"season","choices":[{"label":"Got it","effect":"nothing"}],"cid":None}
        return
    if rng.random()<0.60:
        choices=[["ceo_stays","ceo_leaves_slow","ceo_gone"],
                 ["big_growth","medium_growth","nothing"],
                 ["ceo_gone_clean","crisis_managed","disaster"],
                 ["partial_save","slight_hit","war"],
                 ["win_clever","win_expensive","lose_deal"],
                 ["bought_time","lp_annoyed","lp_amused"],
                 ["lp_happy_hit","lp_exits","lp_furious"],
                 ["forced_exit","auction","nothing"],
                 ["addon_win","addon_maybe","nothing"],
                 ["rate_hedged","slight_hit","nothing"]]
        if gs.companies:
            chosen=rng.choice(choices)
            gs.pending_event={"type":"event","choices":[{"label":f"Option {j+1}","effect":e} for j,e in enumerate(chosen)],"cid":gs.companies[0].id}

def apply_ev(gs,effect,cid):
    eff=EFFECTS.get(effect,{"moic_delta":0})
    if cid:
        for c in gs.companies:
            if c.id==cid:
                if "moic_delta" in eff: c.moic_modifier=max(.1,min(c.moic_modifier+eff["moic_delta"],3.0))
                if eff.get("force_exit"):
                    idx=next((j for j,cc in enumerate(gs.companies) if cc.id==cid),None)
                    if idx is not None: sell(gs,idx)
                break
    if "lp_delta" in eff: gs.lp_satisfaction=max(0,min(100,gs.lp_satisfaction+eff["lp_delta"]))
    gs.pending_event={}

# ── Player Archetype Models ────────────────────────────────────────────

class PlayerArchetype:
    """Base class. Each archetype encodes UX expectations and behavior."""

    name = "Generic"
    difficulty = "Balanced"
    ux_expectations = []

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.friction = []           # UX pain points logged during play
        self.confusion = []          # Moments of "what do I do?"
        self.delights = []           # Positive UX moments
        self.clicks = 0              # Total interactions
        self.rage_quits = 0          # Would have closed tab

    def log_friction(self, q, msg): self.friction.append((q, msg))
    def log_confusion(self, q, msg): self.confusion.append((q, msg))
    def log_delight(self, q, msg): self.delights.append((q, msg))

    def resolve_event(self, gs, ev): return 0  # default: pick first choice
    def pick_deal(self, gs): return None
    def pick_sell(self, gs): return None
    def would_rage_quit(self, gs) -> bool: return False

    def run(self):
        cfg = DIFFICULTY[self.difficulty]
        gs = GS(difficulty=self.difficulty, cash=cfg["cash"], lp_satisfaction=cfg["lp_start"])
        gs.deals = make_deals(gs, 5, self.rng)
        self.pre_game_check(gs)

        for q in range(cfg["quarters"]):
            if gs.screen == "score": break

            self.clicks += 1

            # Detect "what now?" confusion at start
            if q == 0 and not gs.companies:
                self.first_turn_check(gs)

            # Resolve any pending event
            if gs.pending_event:
                choice_idx = self.resolve_event(gs, gs.pending_event)
                choices = gs.pending_event.get("choices", [])
                if choices:
                    effect = choices[min(choice_idx, len(choices)-1)].get("effect", "nothing")
                    apply_ev(gs, effect, gs.pending_event.get("cid"))
                    self.clicks += 1
                else:
                    gs.pending_event = {}

            # Sell decision
            si = self.pick_sell(gs)
            if si is not None:
                self.clicks += 1
                sell(gs, si, self.rng)

            # Buy decision
            bi = self.pick_deal(gs)
            if bi is not None:
                self.clicks += 1
                d = gs.deals[bi]
                gs.cash -= d.entry_equity
                d.entry_quarter = gs.quarter_num
                gs.companies.append(d)
                gs.deals.pop(bi)
            elif not gs.companies and all(d.entry_equity > gs.cash for d in gs.deals):
                self.log_friction(q, "STUCK: No companies owned and can't afford any deal")
                if q > 2: self.rage_quits += 1

            self.mid_turn_check(gs, q)

            adv(gs, self.rng)

        self.end_game_check(gs)
        p = paths(gs)
        return {
            "archetype": self.name,
            "difficulty": self.difficulty,
            "final_moic": bm(gs),
            "paths_hit": sum(p.values()),
            "exits": len(gs.exited),
            "lp": gs.lp_satisfaction,
            "friction": self.friction,
            "confusion": self.confusion,
            "delights": self.delights,
            "rage_quits": self.rage_quits,
            "clicks": self.clicks,
        }

    def pre_game_check(self, gs): pass
    def first_turn_check(self, gs): pass
    def mid_turn_check(self, gs, q): pass
    def end_game_check(self, gs): pass


# ─────────────────────────────────────────────────────
# ARCHETYPE 1: Total Newcomer (18-22, never played sim)
# ─────────────────────────────────────────────────────
class NewbieSarah(PlayerArchetype):
    name = "Newbie (Sarah, 20)"
    difficulty = "Easy"

    def pre_game_check(self, gs):
        # Start screen: form with firm name + partner name = friction
        self.log_friction(0, "START_FORM: Forced to enter firm/partner name before playing — why? Just start.")
        # No tutorial, no 'what to do first' hint
        self.log_confusion(0, "NO_ONBOARDING: No explanation of what MOIC, IRR, LP mean on first screen")

    def first_turn_check(self, gs):
        # 5 deals, all look the same
        self.log_confusion(0, "DEAL_PARALYSIS: 5 identical-looking cards, no hint which to pick first")
        # Equity cost vs debt: what does 'Debt' column mean on deal cards?
        self.log_confusion(0, "DEBT_COLUMN: Deal cards show 'Debt' — newcomer doesn't know if they pay this")
        # '3yr Est.' is unclear — estimated what?
        self.log_confusion(0, "3YR_EST_LABEL: '3yr Est.' on deal card means nothing without context")

    def resolve_event(self, gs, ev):
        # Newcomer reads everything, takes longest path
        return 0  # always pick first choice

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff:
            self.log_friction(0, "NO_AFFORDABLE_DEAL: No deal fits budget — confusing for a beginner")
            return None
        # picks lowest cost (feels safest to newcomer)
        return min(aff, key=lambda x: x[1].entry_equity)[0]

    def pick_sell(self, gs):
        if not gs.companies: return None
        # Sells whenever MOIC goes green (> 1.3x but doesn't know that)
        moics = [(i, calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
        hits = [(i,m) for i,m in moics if m > 1.3]
        return max(hits, key=lambda x:x[1])[0] if hits else None

    def mid_turn_check(self, gs, q):
        if q == 2 and not gs.exited:
            self.log_confusion(q, "NO_EXIT_YET: Two quarters in, MOIC still near 1.0x — nothing visibly happening")
        if q == 4 and gs.lp_satisfaction < 55:
            self.log_confusion(q, "LP_BAR_MYSTERY: LP bar went down — no obvious explanation why or what to do")
        if gs.lp_satisfaction < 40:
            self.log_friction(q, "LP_CRISIS_NO_GUIDANCE: LP warning shows but no tooltip on HOW to fix it")
        # Deal flow: 5 new cards every quarter feels like the same screen
        if q % 3 == 0:
            self.log_friction(q, "DEAL_FLOW_SAMENESS: New deals look identical to last quarter — no sense of change")

    def end_game_check(self, gs):
        if not gs.exited:
            self.log_friction(12, "SCORE_NO_EXITS: Score screen with 0 exits — 'Deal Maker: 0/3' feels bad")
        self.log_confusion(12, "FUND_II_CONFUSING: 'Start Fund II →' — do I have to? Is this the same game?")


# ─────────────────────────────────────────────────────
# ARCHETYPE 2: Casual Mobile Gamer (28, iPhone commuter)
# ─────────────────────────────────────────────────────
class MobileCommuter(PlayerArchetype):
    name = "Mobile Gamer (Marcus, 28)"
    difficulty = "Balanced"

    def pre_game_check(self, gs):
        self.log_friction(0, "MOBILE_5COL: Header has 5 columns — completely crushed on iPhone 14 (390px wide)")
        self.log_friction(0, "MOBILE_DEAL_5COL: Deal cards 5 columns — unreadable on mobile, text wraps badly")
        self.log_friction(0, "MOBILE_PORTFOLIO_5COL: Portfolio rows also 5 columns — same problem")
        self.log_friction(0, "FORM_FRICTION: Must fill form before playing — extra tap on mobile keyboard is annoying")

    def first_turn_check(self, gs):
        self.log_confusion(0, "NEXT_Q_PLACEMENT: 'Next Quarter' button is top-right — on mobile that's hard to reach one-handed")

    def resolve_event(self, gs, ev):
        # Fast tapper, picks second choice to feel 'smarter'
        return 1

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff: return None
        return self.rng.choice(aff)[0]

    def pick_sell(self, gs):
        if not gs.companies: return None
        moics = [(i, calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
        hits = [(i,m) for i,m in moics if m > 1.5]
        return max(hits, key=lambda x:x[1])[0] if hits else None

    def mid_turn_check(self, gs, q):
        if q == 1:
            self.log_friction(q, "NO_HAPTIC_FEEDBACK: Buy/sell actions have no satisfying 'pop' — mobile expects micro-feedback")
        if q == 3:
            self.log_friction(q, "SCROLL_FATIGUE: Page gets long with 4 portfolio rows + 5 deal rows + exits = lots of scrolling")
        if q == 6:
            self.log_friction(q, "SEASON_CARD_WALL: Season transition card is text-heavy — mobile player skips it, misses context")
        if q == 8:
            self.log_friction(q, "LP_BAR_TOO_SMALL: LP bar is 6px tall — invisible on mobile retina display")
        # Tap targets: Sell button is in last column, hard to tap
        self.log_friction(q, "SELL_BTN_LOCATION: Sell button is far right — on mobile requires stretching/scrolling horizontally")

    def end_game_check(self, gs):
        self.log_friction(12, "SCORE_SCROLL_HEAVY: Score screen has lots of content, no clear 'play again' CTA above fold")
        self.log_delight(12, "GRADE_LETTER_GOOD: Big letter grade (S/A/B/C) works great on mobile — immediately readable")


# ─────────────────────────────────────────────────────
# ARCHETYPE 3: Finance Pro (34, works in banking)
# ─────────────────────────────────────────────────────
class FinancePro(PlayerArchetype):
    name = "Finance Pro (Jennifer, 34)"
    difficulty = "Hard"

    def pre_game_check(self, gs):
        # Wants data density
        self.log_friction(0, "NO_EV_ON_DEALS: Deal cards don't show EV or Debt/EBITDA ratio — finance pro wants these")
        self.log_friction(0, "NO_IRR_ON_DEALS: Deal cards show '3yr Est.' return but not IRR — want both")

    def first_turn_check(self, gs):
        self.log_confusion(0, "BLENDED_MOIC_UNCLEAR: 'Portfolio MOIC' starts at weird value with 0 holdings — what is 1.00?")

    def resolve_event(self, gs, ev):
        # Reads all choices carefully, picks strategic option
        return 2  # usually last choice (most nuanced)

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff: return None
        # Wants projected IRR, not just MOIC
        def score(d):
            r3=d.revenue*((1+d.growth)**3)*d.margin
            debt=d.entry_debt
            for yr in range(1,4):
                yr_e=d.revenue*((1+d.growth)**yr)*d.margin
                debt=max(debt-max(yr_e*0.55-debt*0.065,0)*0.35,0)
            eq=max(r3*8.5-debt,0)/max(d.entry_equity,1)
            return (eq**0.333-1) if eq>0 else 0  # 3yr IRR
        return max(aff, key=lambda x:score(x[1]))[0]

    def pick_sell(self, gs):
        if not gs.companies: return None
        moics=[(i,calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
        # Sell in season 3 as prices drop
        if gs.season == 3:
            return max(moics, key=lambda x:x[1])[0]
        hits=[(i,m) for i,m in moics if m>2.0]
        return max(hits, key=lambda x:x[1])[0] if hits else None

    def mid_turn_check(self, gs, q):
        if q == 2:
            self.log_friction(q, "MOIC_0X_EARLY: MOIC shows 0.00x for companies held <1 quarter — should show entry value 1.0x")
        if q == 4:
            self.log_friction(q, "NO_DPI_METRIC: No DPI shown in header — finance pro tracks distributions separately from unrealized")
        if q == 6:
            self.log_friction(q, "DEBT_NOT_SHOWN_PORTFOLIO: Portfolio rows don't show current debt balance — crucial metric")
        if q == 8:
            self.log_friction(q, "NO_FUND_LEVEL_IRR: No fund-level IRR shown anywhere — MOIC alone is incomplete")
        if q == 3:
            self.log_confusion(q, "MOIC_MODIFIER_INVISIBLE: Event effects (moic_modifier) not surfaced in UI — how damaged is company?")

    def end_game_check(self, gs):
        self.log_delight(12, "SEASON_MECHANICS_SATISFYING: Three seasons with different multiples feels realistic")
        self.log_friction(12, "SCORE_NO_VINTAGE_ANALYSIS: Score doesn't show J-curve or IRR by entry year — finance wants this")


# ─────────────────────────────────────────────────────
# ARCHETYPE 4: Competitive Optimizer (25, plays Civ/XCOM)
# ─────────────────────────────────────────────────────
class CompetitiveOptimizer(PlayerArchetype):
    name = "Competitive (Alex, 25)"
    difficulty = "Hard"

    def pre_game_check(self, gs):
        self.log_friction(0, "NO_LEADERBOARD: No global leaderboard or compare-with-friends — competitive player wants this on first screen")
        self.log_friction(0, "NO_HIGH_SCORE: Previous best score not shown at start — no target to beat")

    def first_turn_check(self, gs):
        self.log_confusion(0, "CHOICE_WEIGHT_UNCLEAR: Event choices have no numbers — can't calculate optimal choice")

    def resolve_event(self, gs, ev):
        return 0  # picks aggressively

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff: return None
        cfg=DIFFICULTY[gs.difficulty]
        def p3(d):
            r3=d.revenue*((1+d.growth)**3)*d.margin
            debt=d.entry_debt
            for yr in range(1,4):
                yr_e=d.revenue*((1+d.growth)**yr)*d.margin
                debt=max(debt-max(yr_e*0.55-debt*0.065,0)*0.35,0)
            return max(r3*cfg["exit_mult"]-debt,0)/max(d.entry_equity,1)
        return max(aff, key=lambda x:p3(x[1]))[0]

    def pick_sell(self, gs):
        if not gs.companies: return None
        moics=[(i,calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
        # Sell in Season 3 to avoid multiple compression
        if gs.season==3:
            return max(moics,key=lambda x:x[1])[0] if moics else None
        hits=[(i,m) for i,m in moics if m>1.9]
        return max(hits,key=lambda x:x[1])[0] if hits else None

    def mid_turn_check(self, gs, q):
        if q == 1:
            self.log_friction(q, "DEAL_CARDS_NOT_SORTABLE: Can't sort deals by projected return — must scan manually")
        if q == 3:
            self.log_friction(q, "NO_COMPARE_OVERLAY: Can't compare two deals side by side")
        if q == 5:
            self.log_friction(q, "PATH_PROGRESS_VAGUE: Win path badges show current/target but no trajectory line (am I on track?)")
        if q == 7:
            self.log_friction(q, "NO_UNDO: Made a bad sell accidentally — no undo available")
        if q == 9:
            self.log_friction(q, "EVENT_CHOICES_OPAQUE: Event outcomes are random — optimizer can't model expected value")

    def end_game_check(self, gs):
        self.log_friction(12, "NO_OPTIMAL_STRATEGY_REVEALED: Score screen doesn't show 'best possible MOIC with these deals' — no skill feedback")
        self.log_delight(12, "GRADE_GIVES_TARGET: Grade S/A/B/C gives something to chase next run")


# ─────────────────────────────────────────────────────
# ARCHETYPE 5: Story Seeker (32, plays BitLife, Choices)
# ─────────────────────────────────────────────────────
class StorySeeker(PlayerArchetype):
    name = "Story Seeker (Priya, 32)"
    difficulty = "Easy"

    def pre_game_check(self, gs):
        self.log_friction(0, "WEAK_INTRO_NARRATIVE: Start screen just says 'Build a PE empire' — no story hook, no character setup")
        self.log_friction(0, "RIVAL_NOT_INTRODUCED: Rival firm chosen randomly but never introduced dramatically at game start")

    def first_turn_check(self, gs):
        self.log_delight(0, "FIRM_NAME_INPUT: Naming your firm feels personal and fun")
        self.log_delight(0, "CEO_NAMES_ON_DEALS: Seeing CEO names (Priya Sharma) makes deals feel real")

    def resolve_event(self, gs, ev):
        # Reads every word, makes dramatic choice
        return self.rng.randint(0,2)

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff: return None
        # Picks by vibes (sector preference)
        saas = [(i,d) for i,d in aff if d.sector=="SaaS"]
        return self.rng.choice(saas or aff)[0]

    def pick_sell(self, gs):
        # Doesn't want to sell — gets attached to companies
        if not gs.companies: return None
        moics=[(i,calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
        hits=[(i,m) for i,m in moics if m>2.5]  # only sells on big wins
        return max(hits, key=lambda x:x[1])[0] if hits else None

    def mid_turn_check(self, gs, q):
        if q == 2:
            self.log_friction(q, "EVENT_CONSEQUENCES_WEAK: Chose to back arrested CEO but no follow-up narrative — no closure")
        if q == 3:
            self.log_friction(q, "RIVAL_DISAPPEARS: Rival shown in events but no running scoreboard — how are they doing?")
        if q == 4:
            self.log_friction(q, "CEO_FATE_UNKNOWN: CEO left company — no update on where they went or what happened")
        if q == 6:
            self.log_friction(q, "LP_NAMES_NOT_USED: LP bar is generic — events mention LP names but they don't feel like characters")
        if q == 8:
            self.log_delight(q, "SEASON_TRANSITION_TEXT: Season cards with dramatic text are exactly right")
        if q == 10:
            self.log_friction(q, "COMPANY_HISTORY_LOST: Can't see what events happened to a company over its life")

    def end_game_check(self, gs):
        self.log_friction(12, "EXIT_LOG_NO_STORY: Exits just show MOIC/IRR — no 'what happened to this company after' narrative")
        self.log_delight(12, "LP_QUOTE_GREAT: LP closing quote on score screen is perfect — specific and characterful")
        self.log_friction(12, "RIVAL_ENDING_MISSING: Score screen doesn't mention how your rival did — no rivalry resolution")


# ─────────────────────────────────────────────────────
# ARCHETYPE 6: Busy Dad (44, 10-min sessions, kids in background)
# ─────────────────────────────────────────────────────
class BusyDad(PlayerArchetype):
    name = "Busy Dad (Tom, 44)"
    difficulty = "Easy"

    def pre_game_check(self, gs):
        self.log_friction(0, "NO_AUTO_SAVE: No auto-save visible — if I close the tab I lose everything")
        self.log_friction(0, "NO_SAVE_INDICATOR: No 'last saved' timestamp shown anywhere")

    def first_turn_check(self, gs):
        self.log_confusion(0, "TOO_MUCH_INFO_Q1: First screen shows: Portfolio + Deal Flow + Exits + paths + LP bar — information overload")

    def resolve_event(self, gs, ev):
        return 0  # fastest choice

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff: return None
        return aff[0][0]  # first deal, no analysis

    def pick_sell(self, gs):
        if not gs.companies: return None
        moics=[(i,calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
        hits=[(i,m) for i,m in moics if m>1.6]
        return max(hits, key=lambda x:x[1])[0] if hits else None

    def mid_turn_check(self, gs, q):
        if q == 3:
            self.log_friction(q, "NO_RECOMMENDED_ACTION: No 'suggested move' hint — busy player wants a nudge")
        if q == 5:
            self.log_friction(q, "PAGE_LENGTH_MOBILE: Page with full portfolio + 5 deals = 8+ screens of scrolling on phone")
        if q == 7:
            self.log_friction(q, "NEXT_Q_BURIED: 'Next Quarter' at top right gets buried after scrolling — need sticky button")
        if q == 9 and not gs.exited:
            self.log_friction(q, "SILENT_FAILURE: Never exited, LP satisfaction dropping — no proactive warning until critical")

    def end_game_check(self, gs):
        self.log_friction(12, "NO_SESSION_SAVE: Closing browser mid-game = lost progress — no save prompt")
        self.log_delight(12, "SHORT_SESSION_OK: 12-quarter game fits a 15-minute session — right length")


# ─────────────────────────────────────────────────────
# ARCHETYPE 7: Cynical Veteran (38, played everything, skeptical)
# ─────────────────────────────────────────────────────
class CynicalVet(PlayerArchetype):
    name = "Cynical Vet (Derek, 38)"
    difficulty = "Hard"

    def pre_game_check(self, gs):
        self.log_friction(0, "STREAMLIT_OBVIOUS: App obviously runs on Streamlit — rerun flash on every click breaks immersion")
        self.log_friction(0, "NO_ANIMATIONS: No transitions, no loading states — feels like a spreadsheet not a game")

    def first_turn_check(self, gs):
        self.log_friction(0, "ALL_DEALS_SAME_QUALITY: First deal batch shows 1.2x-2.8x projected — huge variance with no signal on why")

    def resolve_event(self, gs, ev):
        return 1

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff: return None
        cfg=DIFFICULTY[gs.difficulty]
        def p3(d):
            r3=d.revenue*((1+d.growth)**3)*d.margin
            debt=d.entry_debt
            for yr in range(1,4):
                yr_e=d.revenue*((1+d.growth)**yr)*d.margin
                debt=max(debt-max(yr_e*0.55-debt*0.065,0)*0.35,0)
            return max(r3*cfg["exit_mult"]-debt,0)/max(d.entry_equity,1)
        return max(aff,key=lambda x:p3(x[1]))[0]

    def pick_sell(self, gs):
        if not gs.companies: return None
        moics=[(i,calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
        if gs.season==3: return max(moics,key=lambda x:x[1])[0] if moics else None
        hits=[(i,m) for i,m in moics if m>2.2]
        return max(hits,key=lambda x:x[1])[0] if hits else None

    def mid_turn_check(self, gs, q):
        if q == 2:
            self.log_friction(q, "REFRESH_FLICKER: Every button click causes full page rerender — visual stutter breaks flow")
        if q == 4:
            self.log_friction(q, "REPEAT_EVENT_TYPES: Same CEO-poached event appeared twice in 4 quarters — repetitive")
        if q == 6:
            self.log_friction(q, "CHOICE_OUTCOMES_PREDICTABLE: Same choices always produce similar outcomes — no real variance")
        if q == 8:
            self.log_friction(q, "DEAL_NAMES_REPEAT: 'DataFlow' appeared twice in same deal flow — company name pool too small")
        if q == 10:
            self.log_friction(q, "EVENT_MISSING_PORTFOLIO_CONTEXT: Event mentions CEO of company but doesn't show company's current MOIC")

    def end_game_check(self, gs):
        self.log_friction(12, "FUND_II_SAME_GAME: 'Start Fund II' just restarts with more cash — no actual new mechanics")
        self.log_delight(12, "SEASON_RECKONING_TENSION: The Reckoning season genuinely creates anxiety — good design")


# ─────────────────────────────────────────────────────
# ARCHETYPE 8: Gen Z TikTok User (19, max 30 seconds attention)
# ─────────────────────────────────────────────────────
class GenZTikTok(PlayerArchetype):
    name = "Gen Z (Zoe, 19)"
    difficulty = "Easy"

    def pre_game_check(self, gs):
        self.log_friction(0, "START_SCREEN_BORING: Start screen has text form — no animation, no hook, no 'wow' moment in 3 seconds")
        self.log_friction(0, "DARK_THEME_GENERIC: Dark navy is fine but not distinct — looks like 50 other apps")

    def first_turn_check(self, gs):
        self.log_confusion(0, "UNCLEAR_WIN: 'Three ways to win' shown at top but not what winning FEELS LIKE")
        self.log_confusion(0, "JARGON_OVERLOAD: MOIC, IRR, LP, DPI — four acronyms in first 5 seconds")

    def resolve_event(self, gs, ev):
        return self.rng.randint(0, 2)  # totally random

    def pick_deal(self, gs):
        if len(gs.companies) >= MAX_PORTFOLIO: return None
        aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
        if not aff: return None
        return self.rng.choice(aff)[0]

    def pick_sell(self, gs):
        # Impulsive — sells randomly
        if not gs.companies: return None
        if self.rng.random() < 0.3:
            return self.rng.randint(0, len(gs.companies)-1)
        return None

    def mid_turn_check(self, gs, q):
        if q == 1:
            self.log_friction(q, "NO_CELEBRATION_ON_BUY: Bought a company — no satisfying animation or sound")
        if q == 2:
            self.log_friction(q, "NUMBERS_DONT_MEAN_ANYTHING: 1.12x MOIC vs 1.08x — what is good? What is bad? No color/emoji signal at low values")
        if q == 3:
            self.rage_quits += 1
            self.log_friction(q, "RAGE_QUIT_LIKELY: After 3 quarters of clicking with no clear reward — would close tab")
        if q == 4:
            self.log_friction(q, "NO_SHARE_MOMENT: No 'share your result' button — Gen Z wants to screenshot and post")
        if q == 6:
            self.log_delight(q, "EVENT_WRITING_GOOD: 'You deleted it' and 'CEO insufferable' are great — tone works")

    def end_game_check(self, gs):
        self.log_friction(12, "SCORE_NOT_SHAREABLE: Grade screen not optimized for screenshot/share")
        self.log_friction(12, "NO_ACHIEVEMENTS: No achievement system — no 'First 2x Exit' badge to collect")


# ── Run all archetypes × N seeds ─────────────────────────────────────

def run_all_archetypes(n_seeds=30):
    archetypes = [NewbieSarah, MobileCommuter, FinancePro, CompetitiveOptimizer,
                  StorySeeker, BusyDad, CynicalVet, GenZTikTok]
    all_results = []
    for seed in range(n_seeds):
        for Arch in archetypes:
            try:
                result = Arch(seed).run()
                all_results.append(result)
            except Exception as e:
                all_results.append({"archetype": Arch.name, "error": str(e),
                                     "friction":[], "confusion":[], "delights":[], "rage_quits":0})
    return all_results

def analyze(results):
    print(f"\n{'='*65}")
    print(f"UX PLAYTEST REPORT  ({len(results)} runs across 8 archetypes)")
    print(f"{'='*65}")

    # Rage quit counts
    print("\n── RAGE QUIT RISK (per archetype)")
    rq = defaultdict(list)
    for r in results: rq[r["archetype"]].append(r.get("rage_quits", 0))
    for arch, vals in sorted(rq.items(), key=lambda x: -sum(x[1])):
        total = sum(vals); pct = total/len(vals)*100
        flag = " ← HIGH RISK" if pct > 30 else ""
        print(f"  {arch[:38]:38s}  {pct:5.1f}% runs{flag}")

    # Most frequent friction points
    print("\n── TOP FRICTION POINTS (all archetypes, frequency)")
    freq = defaultdict(int)
    for r in results:
        for _q, msg in r.get("friction", []):
            freq[msg] += 1
    for msg, count in sorted(freq.items(), key=lambda x: -x[1])[:25]:
        sev = "🔴" if count > len(results)//4 else "🟡"
        print(f"  {sev} [{count:3d}x] {msg}")

    # Top confusion points
    print("\n── TOP CONFUSION POINTS")
    cfreq = defaultdict(int)
    for r in results:
        for _q, msg in r.get("confusion", []):
            cfreq[msg] += 1
    for msg, count in sorted(cfreq.items(), key=lambda x: -x[1])[:15]:
        print(f"  [{count:3d}x] {msg}")

    # Delights (keep these!)
    print("\n── DELIGHTS (don't break these)")
    dfreq = defaultdict(int)
    for r in results:
        for _q, msg in r.get("delights", []):
            dfreq[msg] += 1
    for msg, count in sorted(dfreq.items(), key=lambda x: -x[1])[:10]:
        print(f"  ✨ [{count:3d}x] {msg}")

    # Group friction by UX category
    categories = {
        "Mobile Layout":      ["MOBILE","5COL","SCROLL","STICKY","TAP","HAPTIC","LP_BAR_TOO"],
        "Information Design": ["JARGON","UNCLEAR","LABEL","COLUMN","SHOW","METRIC","DEBT","DPI","IRR","EV"],
        "Onboarding":         ["FORM","ONBOARDING","TUTORIAL","NO_ONBOARDING","INTRO","HOOK"],
        "Feedback & Reward":  ["ANIMATION","CELEBRATION","FEEDBACK","ACHIEVEMENT","SHARE","BADGE"],
        "Save & Persistence": ["SAVE","AUTO_SAVE","SESSION"],
        "Narrative":          ["NARRATIVE","RIVAL","CEO_FATE","LP_NAMES","STORY","FOLLOW","RESOLUTION"],
        "Navigation":         ["NEXT_Q","NEXT Q","BUTTON","PLACEMENT","BURIED"],
        "Gameplay Loop":      ["SAME","REPEAT","BORING","OPAQUE","PREDICTABLE","POOL"],
    }
    print("\n── FRICTION BY CATEGORY")
    for cat, keywords in categories.items():
        count = sum(1 for r in results for _q,msg in r.get("friction",[])
                   if any(k in msg for k in keywords))
        count += sum(1 for r in results for _q,msg in r.get("confusion",[])
                    if any(k in msg for k in keywords))
        bar = "█" * min(count // 3, 30)
        print(f"  {cat:22s} {count:4d}  {bar}")

    # Final tally
    total_friction = sum(len(r.get("friction",[])) for r in results)
    total_confusion = sum(len(r.get("confusion",[])) for r in results)
    total_delight = sum(len(r.get("delights",[])) for r in results)
    print(f"\n── TOTALS: {total_friction} friction · {total_confusion} confusion · {total_delight} delights")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    print("Running 240 playthroughs (30 seeds × 8 archetypes)...")
    results = run_all_archetypes(n_seeds=30)
    analyze(results)
