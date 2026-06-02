"""
CarryForge Parallel Playtest Simulator v2
==========================================
Imports from game_engine.py — single source of truth.
Adds lever-aware simulation strategies.
"""

import random, math, statistics
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from game_engine import (
    SECTORS, DIFFICULTY, LEVERS, EFFECTS, SEASONS,
    Company, GameState,
    make_deals, calc, blended_moic, proj3,
    check_paths, sell_company, apply_effect, advance_quarter, cf
)

MAX_PORT = 4

# ── Strategy helpers ─────────────────────────────────────────────────────────

def pick_deal(gs, strategy, rng):
    if len(gs.companies) >= MAX_PORT: return None
    aff = [(i,d) for i,d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
    if not aff: return None
    if strategy == "greedy_growth":  return max(aff, key=lambda x: x[1].growth)[0]
    if strategy == "value":          return min(aff, key=lambda x: x[1].entry_multiple)[0]
    if strategy == "random":         return rng.choice(aff)[0]
    if strategy == "diversify":
        held = {c.sector for c in gs.companies}
        fresh = [(i,d) for i,d in aff if d.sector not in held]
        return max(fresh or aff, key=lambda x: x[1].growth)[0]
    if strategy == "cash_hoard":
        ch = [(i,d) for i,d in aff if d.entry_equity < gs.cash * 0.50]
        return max(ch, key=lambda x: x[1].growth)[0] if ch else None
    if strategy in ("proj_moic", "lever_heavy", "lever_safe"):
        cfg = DIFFICULTY[gs.difficulty]
        def p3(d):
            r3 = d.revenue * ((1+d.growth)**3); eb3 = r3 * d.margin; debt = d.entry_debt
            for yr in range(1,4):
                yr_e = d.revenue*((1+d.growth)**yr)*d.margin
                debt = max(debt - max(yr_e*.55-debt*.065,0)*.50, 0)
            return max(eb3 * cfg["exit_mult"] - debt, 0) / max(d.entry_equity, 1)
        return max(aff, key=lambda x: p3(x[1]))[0]
    return rng.choice(aff)[0]

def pick_sell(gs, strategy, rng):
    if not gs.companies: return None
    moics = [(i, calc(c,gs)["moic"]) for i,c in enumerate(gs.companies)]
    if len(gs.companies) >= MAX_PORT:
        return max(moics, key=lambda x: x[1])[0]
    if strategy == "never":   return None
    if strategy == "random":  return max(moics, key=lambda x: x[1])[0] if rng.random() < .2 else None
    thresholds = {"greedy_growth":1.9,"value":1.7,"diversify":2.1,"cash_hoard":1.5,
                  "proj_moic":1.8,"lever_heavy":1.7,"lever_safe":1.8}
    t = thresholds.get(strategy, 1.8)
    hits = [(i,m) for i,m in moics if m > t]
    return max(hits, key=lambda x: x[1])[0] if hits else None

def pick_lever(gs, c, strategy, rng):
    """Choose a value creation lever for company c. Returns lever_id or None."""
    if strategy == "lever_heavy":
        # Pick highest expected-value lever that's off cooldown and affordable
        best, best_ev = None, -999
        for lid, lev in LEVERS.items():
            on_cd = c.lever_cooldowns.get(lid, -99) > gs.quarter_num - lev["cooldown"]
            if on_cd: continue
            if lev["cost"] > gs.cash: continue
            ev = lev["success_rate"] * lev["win_moic"] + (1-lev["success_rate"]) * lev["loss_moic"]
            if ev > best_ev: best, best_ev = lid, ev
        return best
    elif strategy == "lever_safe":
        # Only use low-risk levers (success_rate >= 0.70)
        options = [lid for lid,lev in LEVERS.items()
                   if lev["success_rate"] >= 0.70
                   and lev["cost"] <= gs.cash
                   and not (c.lever_cooldowns.get(lid,-99) > gs.quarter_num - lev["cooldown"])]
        return rng.choice(options) if options else None
    return None

def run_game(seed, diff, strategy):
    rng = random.Random(seed)
    cfg = DIFFICULTY[diff]
    gs  = GameState(difficulty=diff, cash=cfg["cash"], lp_satisfaction=cfg["lp_start"])
    gs.deals = make_deals(gs, 5)
    issues = []; buys = sells = dead_q = 0
    cash_history = []; moic_history = []

    for _ in range(cfg["quarters"]):
        if gs.screen == "score": break

        cash_history.append(gs.cash)
        moic_history.append(blended_moic(gs))

        # Levers before sell/buy
        if strategy in ("lever_heavy","lever_safe"):
            for c in gs.companies:
                if not c.pending_lever:
                    lid = pick_lever(gs, c, strategy, rng)
                    if lid:
                        lev = LEVERS[lid]
                        if lev["cost"] <= gs.cash:
                            gs.cash -= lev["cost"]
                            c.pending_lever = lid

        si = pick_sell(gs, strategy, rng)
        if si is not None: sell_company(gs, si); sells += 1

        bi = pick_deal(gs, strategy, rng)
        if bi is not None:
            d = gs.deals[bi]
            if d.entry_equity <= gs.cash:
                gs.cash -= d.entry_equity; d.entry_quarter = gs.quarter_num
                gs.companies.append(d); gs.deals.pop(bi); buys += 1
        elif not gs.companies: dead_q += 1

        for c in gs.companies:
            m = calc(c, gs)
            if not math.isfinite(m["moic"]): issues.append("NAN_MOIC")
            if m["moic"] > 60: issues.append(f"OUTLIER:{m['moic']:.1f}x")
        if gs.cash < -1000: issues.append(f"NEG_CASH")

        advance_quarter(gs)

    fm = blended_moic(gs)
    if buys == 0: issues.append("ZERO_BUYS")
    if sells == 0 and buys > 3: issues.append("ZERO_SELLS")
    if len(moic_history) >= 6 and max(moic_history[-6:])-min(moic_history[-6:]) < 0.05:
        issues.append("FLATLINE")
    avg_cash_pct = [c/cfg["cash"] for c in cash_history]
    if statistics.mean(avg_cash_pct) > 0.65: issues.append("CASH_HOARD")
    if dead_q >= 3: issues.append(f"DEAD_END:{dead_q}Q")

    paths = check_paths(gs)
    return {
        "diff":diff,"strategy":strategy,"moic":fm,"seed":seed,
        "paths_hit":sum(1 for p in paths.values() if p["hit"]),"exits":len(gs.exited),
        "lp_final":gs.lp_satisfaction,"buys":buys,"sells":sells,
        "issues":issues,"cash_end":gs.cash,"dead_q":dead_q,
    }

def run_all(n=40):
    diffs = ["Casual","Balanced","Hardcore"]
    strats = ["greedy_growth","value","random","diversify",
              "cash_hoard","proj_moic","lever_heavy","lever_safe"]
    results = []
    for seed in range(n):
        for d in diffs:
            for s in strats:
                results.append(run_game(seed, d, s))
    return results

def analyze(results):
    print(f"\n{'='*68}")
    print(f"CARRYFORGE FULL AUDIT — {len(results)} games")
    print(f"{'='*68}")

    print("\n── WIN RATES")
    wr = defaultdict(list)
    for r in results: wr[(r['diff'],r['strategy'])].append(r['paths_hit']>=1)
    for diff in ["Casual","Balanced","Hardcore"]:
        print(f"  {diff}:")
        for st in ["greedy_growth","value","random","diversify","cash_hoard",
                   "proj_moic","lever_heavy","lever_safe"]:
            w = wr[(diff,st)]; pct = sum(w)/len(w)*100 if w else 0
            flag = " ← BROKEN" if pct > 95 or pct < 5 else ""
            print(f"    {st:16s} {pct:5.1f}%{flag}")

    print("\n── MOIC DISTRIBUTION")
    md = defaultdict(list)
    for r in results:
        if math.isfinite(r['moic']): md[r['diff']].append(r['moic'])
    for diff, vals in md.items():
        sv = sorted(vals); n = len(sv)
        print(f"  {diff}: p25={sv[n//4]:.2f} med={sv[n//2]:.2f} "
              f"p75={sv[3*n//4]:.2f} max={sv[-1]:.2f}")

    print("\n── STRATEGY MOIC AVERAGES")
    sm = defaultdict(list)
    for r in results:
        if math.isfinite(r['moic']): sm[r['strategy']].append(r['moic'])
    for st, vals in sorted(sm.items(), key=lambda x: -statistics.mean(x[1])):
        print(f"  {st:16s} avg={statistics.mean(vals):.2f}  std={statistics.stdev(vals):.2f}")

    dead = sum(r['dead_q'] >= 3 for r in results)
    print(f"\n── DEAD ENDS (≥3Q stuck): {dead}/{len(results)}")

    lp_dead = sum(r['lp_final'] < 20 for r in results)
    print(f"── LP DEATHS (<20 final): {lp_dead}/{len(results)}")

    no_exit = sum(r['exits'] == 0 for r in results)
    print(f"── ZERO EXITS: {no_exit}/{len(results)}")

    flat = sum(any("FLATLINE" in i for i in r['issues']) for r in results)
    print(f"── MOIC FLATLINES: {flat}/{len(results)}")

    hoard = sum(any("CASH_HOARD" in i for i in r['issues']) for r in results)
    print(f"── CASH HOARDING: {hoard}/{len(results)}")

    bugs = [(r['diff'],r['strategy'],i) for r in results for i in r['issues']
            if not any(k in i for k in ("FLATLINE","CASH_HOARD","DEAD_END"))]
    seen = set(); uniq = []
    for t in bugs:
        if t[2][:40] not in seen: seen.add(t[2][:40]); uniq.append(t)
    print(f"\n── HARD BUGS ({len(bugs)} total, {len(uniq)} unique)")
    for d,s,i in uniq[:10]: print(f"  [{d}/{s}] {i}")

    print("\n── LEVER STRATEGY COMPARISON (lever vs no-lever)")
    lever_moics = [r['moic'] for r in results if r['strategy'] in ("lever_heavy","lever_safe")
                   and math.isfinite(r['moic'])]
    base_moics  = [r['moic'] for r in results if r['strategy'] in ("proj_moic","value")
                   and math.isfinite(r['moic'])]
    if lever_moics and base_moics:
        print(f"  Lever avg: {statistics.mean(lever_moics):.2f}x  "
              f"Non-lever avg: {statistics.mean(base_moics):.2f}x  "
              f"Delta: {statistics.mean(lever_moics)-statistics.mean(base_moics):+.2f}x")

    # LBO spot check
    print("\n── LBO SPOT CHECK")
    rng = random.Random(42)
    gs_t = GameState(difficulty="Balanced",cash=50e6,lp_satisfaction=65)
    gs_t.deals = make_deals(gs_t,5)
    tc = gs_t.deals[0]; tc.entry_quarter=0
    gs_t.quarter_num=4; m1=calc(tc,gs_t)
    gs_t.quarter_num=12; m3=calc(tc,gs_t)
    print(f"  1yr MOIC: {m1['moic']:.2f}x  3yr MOIC: {m3['moic']:.2f}x")
    print(f"  Entry: {cf(tc.entry_equity)} equity on {cf(tc.entry_ev)} EV  Lev {tc.entry_debt/max(tc.ebitda,1):.1f}x")

    print(f"\n{'='*68}\n")

if __name__ == "__main__":
    print("Running 960 games (40 seeds × 3 diffs × 8 strategies)...")
    results = run_all(n=40)
    analyze(results)
