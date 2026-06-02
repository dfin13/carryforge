"""
CarryForge Full Audit Simulator
================================
Runs hundreds of playthroughs across every player archetype and difficulty.
Reports: bugs, balance issues, dead-ends, UX friction, design gaps, and
specific improvement opportunities — ranked by impact.
"""

import random, math, statistics, sys
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

# ── Inline game logic (mirrors carryforge.py) ─────────────────────────────

SECTORS = {
    "SaaS":       {"abbr":"SW","rev":(40,180),"margin":(.28,.50),"growth":(.12,.38)},
    "Hardware":   {"abbr":"HW","rev":(90,320),"margin":(.08,.20),"growth":(.04,.16)},
    "Healthcare": {"abbr":"HC","rev":(70,260),"margin":(.14,.30),"growth":(.08,.24)},
    "Fintech":    {"abbr":"FT","rev":(35,130),"margin":(.22,.45),"growth":(.22,.50)},
    "Logistics":  {"abbr":"LG","rev":(100,400),"margin":(.06,.14),"growth":(.05,.14)},
    "Media":      {"abbr":"MD","rev":(30,110),"margin":(.15,.32),"growth":(.10,.30)},
    "Industrial": {"abbr":"IN","rev":(120,380),"margin":(.08,.16),"growth":(.04,.12)},
    "Consumer":   {"abbr":"CS","rev":(60,220),"margin":(.10,.22),"growth":(.06,.18)},
}
SEASONS = {
    1:{"exit_mod":1.15,"growth_mod":1.10},
    2:{"exit_mod":1.00,"growth_mod":0.95},
    3:{"exit_mod":0.85,"growth_mod":0.88},
}
DIFFICULTY = {
    "Casual":   {"cash":70e6,"exit_mult":10.5,"quarters":12,"lp_start":85,"paths":{"moic":1.3,"lp":52,"exits":1}},
    "Balanced": {"cash":50e6,"exit_mult":9.2, "quarters":12,"lp_start":72,"paths":{"moic":1.8,"lp":62,"exits":3}},
    "Hardcore": {"cash":35e6,"exit_mult":8.0, "quarters":12,"lp_start":55,"paths":{"moic":2.2,"lp":58,"exits":4}},
}
EFFECTS_MOIC = {
    "ceo_stays":+.16,"ceo_slows":-.08,"ceo_gone":-.18,"ceo_fired_clean":-.18,
    "crisis_lawyer":-.09,"disaster":-.28,"big_growth":+.22,"medium_growth":+.15,
    "nothing":.00,"partial_save":-.07,"slight_miss":-.11,"litigation":-.18,
    "deal_lost":.00,"deal_expensive":-.04,"deal_clever":+.09,"rival_rivalry":.00,
    "lp_amused":.00,"pressure_exit":.00,"bought_time":.00,"lp_annoyed":.00,
    "recap_lp":-.04,"lp_secondary":.00,"lp_furious":.00,"force_exit":.00,
    "auction_process":+.14,"addon_success":+.16,"addon_negotiate":+.06,
    "rate_hedge":+.05,"risky_hold":+.12,"ceo_upgrade":+.16,"mgmt_stable":+.05,
    "slow_resolution":-.04,"ipo_process":+.09,"key_retained":+.08,
}
EFFECTS_LP = {
    "lp_amused":+6,"bought_time":-3,"lp_annoyed":-11,"recap_lp":+11,
    "lp_secondary":-18,"lp_furious":-26,"rival_rivalry":+3,
}
FORCE_EXIT = {"pressure_exit","force_exit"}

@dataclass
class Co:
    id:str; sector:str; revenue:float; ebitda:float; margin:float; growth:float
    entry_mult:float; entry_ev:float; entry_debt:float; entry_equity:float
    entry_q:int=0; moic_mod:float=1.0

@dataclass
class GS:
    diff:str="Balanced"; q:int=0; cash:float=50e6
    companies:list=field(default_factory=list)
    exited:list=field(default_factory=list)
    deals:list=field(default_factory=list)
    lp:int=65; exit_mod:float=1.0; growth_mod:float=1.0
    sector_mods:dict=field(default_factory=dict)
    forced_exit:str=""; season_shown:int=0
    @property
    def season(self): return 1 if self.q+1<=4 else (2 if self.q+1<=8 else 3)
    @property
    def tot(self): return DIFFICULTY[self.diff]["quarters"]

def make_deals(gs,n=5,rng=None):
    if rng is None: rng=random
    deals=[]
    for _ in range(n):
        s=rng.choice(list(SECTORS)); p=SECTORS[s]
        rev=rng.uniform(*p["rev"])*1e6; mg=rng.uniform(*p["margin"])
        eb=rev*mg; gr=rng.uniform(*p["growth"])
        em=round(rng.uniform(6.5,9.8),1); ev=eb*em
        debt=eb*rng.uniform(3.0,5.2); eq=max(ev-debt,ev*0.08)
        deals.append(Co(id=str(rng.random()),sector=s,revenue=rev,ebitda=eb,
            margin=mg,growth=gr,entry_mult=em,entry_ev=ev,entry_debt=debt,
            entry_equity=eq,entry_q=gs.q))
    # Guarantee >=2 affordable deals
    budget=max(gs.cash*0.55, DIFFICULTY[gs.diff]["cash"]*0.40)
    aff=[d for d in deals if d.entry_equity<=budget]
    if len(aff)<2:
        for _ in range(8):
            s2=rng.choice(list(SECTORS)); p2=SECTORS[s2]
            rev2=rng.uniform(p2["rev"][0],p2["rev"][0]+(p2["rev"][1]-p2["rev"][0])*.4)*1e6
            mg2=rng.uniform(*p2["margin"]); eb2=rev2*mg2; gr2=rng.uniform(*p2["growth"])
            em2=round(rng.uniform(6.2,7.6),1); ev2=eb2*em2
            debt2=eb2*rng.uniform(2.8,4.0); eq2=max(ev2-debt2,ev2*0.08)
            if eq2<=budget:
                c2=Co(id=str(rng.random()),sector=s2,revenue=rev2,ebitda=eb2,margin=mg2,
                    growth=gr2,entry_mult=em2,entry_ev=ev2,entry_debt=debt2,entry_equity=eq2,entry_q=gs.q)
                deals.append(c2); aff.append(c2)
                if len(aff)>=2: break
    return deals

def calc(c,gs):
    si=SEASONS[gs.season]; sm=gs.sector_mods.get(c.sector,1.0)
    qh=gs.q-c.entry_q; yh=qh/4.0
    mature=max(qh-8,0)/4.0
    eg=c.growth*gs.growth_mod*sm*si["growth_mod"]*((1-.07)**mature)
    debt=c.entry_debt
    for yr in range(1,int(yh)+1):
        my=max((yr*4-8)/4,0)
        y_eg=c.growth*gs.growth_mod*sm*si["growth_mod"]*((1-.07)**my)
        yr_e=c.revenue*((1+y_eg)**yr)*c.margin
        debt=max(debt-max(yr_e*0.55-debt*0.065,0)*0.35,0)
    rev=c.revenue*((1+eg)**yh); ebitda=rev*c.margin
    pm=0.88+yh*.12 if yh<1 else (1.0+(yh-1)*.073 if yh<=3 else 1.22-(yh-3)*.025)
    cfg=DIFFICULTY[gs.diff]
    em=cfg["exit_mult"]*gs.exit_mod*sm*pm*si["exit_mod"]
    equity=max(ebitda*em-debt,0)*max(c.moic_mod,.1)
    moic=max(equity/max(c.entry_equity,1), 0.95 if yh<.25 else 0)
    irr=(moic**(1/max(yh,.25))-1) if yh>0 else 0
    leverage=debt/max(ebitda,1)
    icr=ebitda/max(debt*0.065,1)
    return {"equity":equity,"moic":moic,"irr":irr,"yh":yh,"leverage":leverage,"icr":icr}

def blended_moic(gs):
    ti=sum(c.entry_equity for c in gs.companies)+sum(e["eq"] for e in gs.exited)
    to=sum(calc(c,gs)["equity"] for c in gs.companies)*.88+sum(e["proc"] for e in gs.exited)
    return to/max(ti,1)

def sell(gs,idx):
    c=gs.companies[idx]; m=calc(c,gs)
    gs.cash+=m["equity"]
    gs.exited.append({"eq":c.entry_equity,"proc":m["equity"],"moic":m["moic"],"irr":m["irr"]})
    gs.companies.pop(idx); gs.lp=min(100,gs.lp+9)

def apply_event(gs,effect,cid=None):
    d_moic=EFFECTS_MOIC.get(effect,0)
    d_lp=EFFECTS_LP.get(effect,0)
    if cid:
        for c in gs.companies:
            if c.id==cid: c.moic_mod=max(.1,min(c.moic_mod+d_moic,3.0)); break
    gs.lp=max(0,min(100,gs.lp+d_lp))
    if effect in FORCE_EXIT and cid:
        idx=next((i for i,c in enumerate(gs.companies) if c.id==cid),None)
        if idx is not None: sell(gs,idx)

def adv(gs,rng):
    gs.q+=1
    if not gs.exited and gs.q>4: gs.lp=max(15,gs.lp-3)
    gs.deals=make_deals(gs,5,rng)
    if gs.q>=gs.tot: return
    # Random event
    if rng.random()<0.45 and gs.companies:
        effect=rng.choice(list(EFFECTS_MOIC.keys()))
        apply_event(gs,effect,gs.companies[0].id if gs.companies else None)

MAX_PORT=4

def check_paths(gs):
    cfg=DIFFICULTY[gs.diff]["paths"]; bm=blended_moic(gs)
    return {
        "returns":bm>=cfg["moic"],
        "lp":gs.lp>=cfg["lp"],
        "exits":len(gs.exited)>=cfg["exits"],
    }

# ── Player archetypes ────────────────────────────────────────────────────────

def pick_deal(gs, strategy, rng):
    if len(gs.companies)>=MAX_PORT: return None
    aff=[(i,d) for i,d in enumerate(gs.deals) if d.entry_equity<=gs.cash]
    if not aff: return None
    if strategy=="greedy_growth":  return max(aff,key=lambda x:x[1].growth)[0]
    if strategy=="value":          return min(aff,key=lambda x:x[1].entry_mult)[0]
    if strategy=="random":         return rng.choice(aff)[0]
    if strategy=="diversify":
        held={c.sector for c in gs.companies}
        fresh=[(i,d) for i,d in aff if d.sector not in held]
        return max(fresh or aff,key=lambda x:x[1].growth)[0]
    if strategy=="cash_hoard":
        ch=[(i,d) for i,d in aff if d.entry_equity<gs.cash*.45]
        return max(ch,key=lambda x:x[1].growth)[0] if ch else None
    if strategy=="proj_moic":
        cfg=DIFFICULTY[gs.diff]
        def p3(d):
            r3=d.revenue*((1+d.growth)**3); eb3=r3*d.margin; debt=d.entry_debt
            for yr in range(1,4):
                yr_e=d.revenue*((1+d.growth)**yr)*d.margin
                debt=max(debt-max(yr_e*.55-debt*.065,0)*.50,0)
            return max(eb3*cfg["exit_mult"]-debt,0)/max(d.entry_equity,1)
        return max(aff,key=lambda x:p3(x[1]))[0]
    return rng.choice(aff)[0]

def pick_sell(gs, strategy, rng):
    if not gs.companies: return None
    moics=[(i,calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
    # Always sell if portfolio full
    if len(gs.companies)>=MAX_PORT:
        return max(moics,key=lambda x:x[1])[0]
    if strategy=="never":           return None
    if strategy=="random":          return max(moics,key=lambda x:x[1])[0] if rng.random()<.2 else None
    thresholds={"greedy_growth":1.9,"value":1.7,"diversify":2.1,"cash_hoard":1.5,"proj_moic":1.8}
    t=thresholds.get(strategy,1.8)
    # Also sell damaged companies
    dmg=[(i,c) for i,c in enumerate(gs.companies) if c.moic_mod<0.82]
    if dmg: return dmg[0][0]
    hits=[(i,m) for i,m in moics if m>t]
    return max(hits,key=lambda x:x[1])[0] if hits else None

def run_game(seed, diff, strategy):
    rng=random.Random(seed)
    cfg=DIFFICULTY[diff]
    gs=GS(diff=diff,cash=cfg["cash"],lp=cfg["lp_start"])
    gs.deals=make_deals(gs,5,rng)
    issues=[]; buys=sells=stuck_q=0
    cash_history=[]; moic_history=[]; lp_history=[]
    dead_end_quarters=0

    for _ in range(cfg["quarters"]):
        if gs.q>=gs.tot: break

        cash_history.append(gs.cash)
        moic_history.append(blended_moic(gs))
        lp_history.append(gs.lp)

        si=pick_sell(gs,strategy,rng)
        if si is not None: sell(gs,si); sells+=1

        bi=pick_deal(gs,strategy,rng)
        if bi is not None:
            d=gs.deals[bi]
            if d.entry_equity>gs.cash:
                issues.append("OVERSPEND")
            else:
                gs.cash-=d.entry_equity; d.entry_q=gs.q
                gs.companies.append(d); gs.deals.pop(bi); buys+=1
        else:
            if not gs.companies:
                dead_end_quarters+=1
                if dead_end_quarters>=3:
                    issues.append(f"DEAD_END: {dead_end_quarters}Q with no companies and can't afford any deal")

        # Check for math issues
        for c in gs.companies:
            m=calc(c,gs)
            if not math.isfinite(m["moic"]): issues.append("NAN_MOIC")
            if m["moic"]>60: issues.append(f"OUTLIER_MOIC:{m['moic']:.1f}x")
            if m["equity"]<0: issues.append("NEG_EQUITY")
            if m["leverage"]>8: issues.append(f"EXTREME_LEV:{m['leverage']:.1f}x")
            if m["icr"]<0.3: issues.append("ICR_CRITICAL")

        if gs.cash<-1000: issues.append(f"NEG_CASH:{gs.cash:.0f}")

        adv(gs,rng)

    fm=blended_moic(gs)
    if buys==0: issues.append("ZERO_BUYS")
    if sells==0 and buys>3: issues.append("ZERO_SELLS")
    if not math.isfinite(fm): issues.append("NAN_FINAL_MOIC")

    # Monotony check — was MOIC basically flat for 6+ quarters?
    if len(moic_history)>=6:
        last6=moic_history[-6:]
        spread=max(last6)-min(last6)
        if spread<0.05: issues.append("MOIC_FLATLINE: no movement last 6Q")

    # Cash hoarding check
    avg_cash_pct=[c/cfg["cash"] for c in cash_history]
    if statistics.mean(avg_cash_pct)>0.65:
        issues.append(f"CASH_HOARDING: avg {statistics.mean(avg_cash_pct)*100:.0f}% of start cash undeployed")

    paths=check_paths(gs)
    return {
        "diff":diff,"strategy":strategy,"moic":fm,"seed":seed,
        "paths_hit":sum(paths.values()),"exits":len(gs.exited),
        "lp_final":gs.lp,"buys":buys,"sells":sells,"issues":issues,
        "cash_end":gs.cash,"lp_history":lp_history,"moic_history":moic_history,
        "dead_end_quarters":dead_end_quarters,
    }

def run_all(n=40):
    diffs=["Casual","Balanced","Hardcore"]
    strats=["greedy_growth","value","random","diversify","cash_hoard","proj_moic"]
    results=[]
    for seed in range(n):
        for d in diffs:
            for s in strats:
                results.append(run_game(seed,d,s))
    return results

def analyze(results):
    print(f"\n{'='*68}")
    print(f"CARRYFORGE FULL AUDIT — {len(results)} games")
    print(f"{'='*68}")

    # ── WIN RATES ──
    print("\n── WIN RATES (paths_hit >= 1 = any win)")
    wr=defaultdict(list)
    for r in results: wr[(r['diff'],r['strategy'])].append(r['paths_hit']>=1)
    for diff in ["Casual","Balanced","Hardcore"]:
        print(f"  {diff}:")
        for st in ["greedy_growth","value","random","diversify","cash_hoard","proj_moic"]:
            w=wr[(diff,st)]; pct=sum(w)/len(w)*100 if w else 0
            flag=" ← BROKEN" if pct>95 or pct<5 else ""
            print(f"    {st:16s} {pct:5.1f}%{flag}")

    # ── MOIC DISTRIBUTION ──
    print("\n── MOIC DISTRIBUTION")
    md=defaultdict(list)
    for r in results:
        if math.isfinite(r['moic']): md[r['diff']].append(r['moic'])
    for diff,vals in md.items():
        sv=sorted(vals); n=len(sv)
        print(f"  {diff}: p10={sv[n//10]:.2f} p25={sv[n//4]:.2f} med={sv[n//2]:.2f} "
              f"p75={sv[3*n//4]:.2f} p90={sv[9*n//10]:.2f} max={sv[-1]:.2f}")

    # ── STRATEGY MOIC GAP (trivial if one always dominates) ──
    print("\n── STRATEGY MOIC AVERAGES")
    sm=defaultdict(list)
    for r in results:
        if math.isfinite(r['moic']): sm[r['strategy']].append(r['moic'])
    for st,vals in sorted(sm.items(),key=lambda x:-statistics.mean(x[1])):
        print(f"  {st:16s} avg={statistics.mean(vals):.2f}  std={statistics.stdev(vals):.2f}")

    # ── DEAD END STATES ──
    dead=sum(r['dead_end_quarters']>0 for r in results)
    print(f"\n── DEAD END STATES: {dead}/{len(results)} games hit cash-trap")
    worst=[r for r in results if r['dead_end_quarters']>=3]
    if worst:
        for r in worst[:3]:
            print(f"  [{r['diff']}/{r['strategy']}] {r['dead_end_quarters']}Q stuck, "
                  f"cash_end=${r['cash_end']/1e6:.1f}M")

    # ── LP DEATH SPIRAL ──
    lp_dead=sum(1 for r in results if r['lp_final']<20)
    print(f"\n── LP DEATH SPIRAL (<20 final): {lp_dead}/{len(results)} games")
    by_diff=defaultdict(int)
    for r in results:
        if r['lp_final']<20: by_diff[r['diff']]+=1
    for d,c in by_diff.items(): print(f"  {d}: {c}")

    # ── ZERO EXITS ──
    no_exits=sum(1 for r in results if r['exits']==0)
    print(f"\n── ZERO EXITS: {no_exits}/{len(results)} games")

    # ── CASH HOARDING ──
    hoard=sum(1 for r in results if any("CASH_HOARDING" in i for i in r['issues']))
    print(f"\n── CASH HOARDING (>65% undeployed avg): {hoard}/{len(results)}")

    # ── MOIC FLATLINE ──
    flat=sum(1 for r in results if any("FLATLINE" in i for i in r['issues']))
    print(f"\n── MOIC FLATLINE (no movement 6Q): {flat}/{len(results)}")

    # ── ALL UNIQUE BUGS ──
    all_bugs=[(r['diff'],r['strategy'],i) for r in results for i in r['issues']
              if not any(k in i for k in ("CASH_HOARDING","FLATLINE","DEAD_END"))]
    seen=set(); unique_bugs=[]
    for t in all_bugs:
        if t[2][:40] not in seen: seen.add(t[2][:40]); unique_bugs.append(t)
    print(f"\n── HARD BUGS ({len(all_bugs)} total, {len(unique_bugs)} unique)")
    for d,s,i in unique_bugs[:20]:
        print(f"  [{d}/{s}] {i}")

    # ── LBO MATH CHECKS ──
    print("\n── LBO MATH SPOT CHECKS")
    # Verify 1-year hold gives sensible MOIC
    from dataclasses import dataclass as dc
    rng=random.Random(42)
    gs=GS(diff="Balanced",cash=50e6,lp=65)
    gs.deals=make_deals(gs,5,rng)
    test_c=gs.deals[0]
    test_c.entry_q=0; gs.q=4  # 1 year hold
    m=calc(test_c,gs)
    print(f"  1yr hold MOIC: {m['moic']:.2f}x (expect 0.9-1.4x for typical deal)")
    gs.q=12  # 3yr hold
    m3=calc(test_c,gs)
    print(f"  3yr hold MOIC: {m3['moic']:.2f}x (expect 1.5-3.5x for typical deal)")
    print(f"  Leverage at entry: {test_c.entry_debt/max(test_c.ebitda,1):.1f}x (expect 3-5x)")
    print(f"  Entry equity: ${test_c.entry_equity/1e6:.1f}M on ${test_c.entry_ev/1e6:.1f}M EV")

    # ── SECTOR BALANCE ──
    print("\n── SECTOR BALANCE (which sectors appear in exited deals)")
    sector_exits=defaultdict(int)
    for r in results:
        if 'exits_by_sector' in r:
            for s,c in r['exits_by_sector'].items(): sector_exits[s]+=c
    # Pull from raw games
    all_exits=[e for r in results for e in []] # not tracked, note this
    print("  (detailed sector exit tracking not captured in this run)")

    print(f"\n{'='*68}")
    print("AUDIT COMPLETE")
    print(f"{'='*68}\n")

    return {
        "win_rates": wr,
        "moic_dist": md,
        "dead_ends": dead,
        "lp_deaths": lp_dead,
        "zero_exits": no_exits,
        "flatlines": flat,
        "hard_bugs": unique_bugs,
    }

if __name__=="__main__":
    print("Running 720 games (40 seeds × 3 difficulties × 6 strategies)...")
    results=run_all(n=40)
    audit=analyze(results)
