"""CarryForge parallel playtest sim v2 — tests maturity-risk balance."""
import random, math, statistics
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict
import numpy as np

SECTORS = {
    'SaaS':      {'rev':(40,160), 'margin':(.28,.48),'growth':(.12,.32)},
    'Hardware':  {'rev':(90,300), 'margin':(.08,.18),'growth':(.04,.14)},
    'Healthcare':{'rev':(70,240), 'margin':(.14,.28),'growth':(.08,.22)},
    'Fintech':   {'rev':(35,120), 'margin':(.22,.42),'growth':(.22,.48)},
}
NAMES = {
    'SaaS':      ['CloudVault','DataFlow','SyncHub','AutoScale','SnapMetrics','PipelineAI','GridLogic','NovaDash','ClearLayer','VaultSync'],
    'Hardware':  ['TechWorks','PrecisionCo','SmartBuild','InnovateLabs','CoreForge','IronStack','PeakSystems','NexHardware'],
    'Healthcare':['HealthPlus','CareFlow','MedTech','LifeSpan','PulseCare','BioServe','ClearMed','VitalPath'],
    'Fintech':   ['PayHub','TradeFlow','VaultSecure','ClearPay','NovaMoney','LedgerX','SwiftBridge','CapitalOps'],
}
EVENTS=[
    {'type':'good','effect':'exit_mult','val':.10},
    {'type':'bad', 'effect':'exit_mult','val':-.08},
    {'type':'good','effect':'sector','val':.15,'sector':'SaaS'},
    {'type':'bad', 'effect':'sector','val':-.12,'sector':'Fintech'},
    {'type':'good','effect':'exit_mult','val':.12},
    {'type':'bad', 'effect':'growth','val':-.20},
    {'type':'good','effect':'sector','val':.18,'sector':'Healthcare'},
    {'type':'bad', 'effect':'sector','val':-.10,'sector':'Hardware'},
    {'type':'info','effect':None},
    {'type':'good','effect':'exit_mult','val':.06},
]
# Calibrated goals after maturity-risk tuning
DIFFICULTY={
    'Easy':    {'start_cash':60e6,'exit_mult_base':9.5,'goal_moic':1.8,'quarters':12},
    'Balanced':{'start_cash':50e6,'exit_mult_base':8.5,'goal_moic':2.0,'quarters':12},
    'Hard':    {'start_cash':40e6,'exit_mult_base':7.5,'goal_moic':2.3,'quarters':12},
}

# Per-quarter chance a company hits a bad event (management problem, competition, etc.)
# Ramps up with age to punish infinite holding
COMPANY_RISK_PER_QTR = 0.07    # 7% per quarter after maturity threshold
MATURITY_THRESHOLD   = 8       # quarters before risk kicks in
GROWTH_DECAY_PER_YR  = 0.08    # growth rate shrinks 8% per year after maturity

@dataclass
class Co:
    id:str; name:str; sector:str; revenue:float; ebitda:float; margin:float
    growth:float; entry_multiple:float; entry_ev:float; entry_debt:float
    entry_equity:float; entry_quarter:int=0
    damage:float=0.0   # accumulated bad-event damage (0.0–1.0 penalty on equity)

@dataclass
class GS:
    difficulty:str='Balanced'; quarter_num:int=0; cash:float=50e6; screen:str='game'
    companies:list=field(default_factory=list); exited:list=field(default_factory=list)
    deals:list=field(default_factory=list)
    exit_mult_mod:float=1.0; growth_mod:float=1.0; sector_mods:dict=field(default_factory=dict)
    @property
    def total_quarters(self): return DIFFICULTY[self.difficulty]['quarters']

def make_deals(gs,n=5,rng=None):
    if rng is None: rng=random
    deals=[]
    for _ in range(n):
        s=rng.choice(list(SECTORS)); p=SECTORS[s]
        rev=rng.uniform(*p['rev']); mg=rng.uniform(*p['margin']); ebitda=rev*mg
        gr=rng.uniform(*p['growth']); em=round(rng.uniform(6.5,9.5),1)
        ev=ebitda*em; debt=ebitda*rng.uniform(3.0,5.0)
        eq=max(ev-debt, ev*0.10)
        deals.append(Co(id=str(rng.random()),name=rng.choice(NAMES[s]),sector=s,
            revenue=rev,ebitda=ebitda,margin=mg,growth=gr,entry_multiple=em,
            entry_ev=ev,entry_debt=debt,entry_equity=eq,entry_quarter=gs.quarter_num))
    return deals

def calc(c, gs):
    qh = gs.quarter_num - c.entry_quarter
    yh = qh / 4.0

    sm = gs.sector_mods.get(c.sector, 1.0)

    # Growth decays after maturity
    mature_qtrs = max(qh - MATURITY_THRESHOLD, 0)
    mature_yrs  = mature_qtrs / 4.0
    effective_growth = c.growth * gs.growth_mod * sm * ((1 - GROWTH_DECAY_PER_YR) ** mature_yrs)

    # Debt paydown year by year
    debt = c.entry_debt
    for yr in range(1, int(yh) + 1):
        yr_growth = c.growth * gs.growth_mod * sm * ((1 - GROWTH_DECAY_PER_YR) ** max(yr - MATURITY_THRESHOLD/4, 0))
        yr_e = c.revenue * ((1 + yr_growth) ** yr) * c.margin
        debt = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)

    rev    = c.revenue * ((1 + effective_growth) ** yh)
    ebitda = rev * c.margin

    em     = DIFFICULTY[gs.difficulty]['exit_mult_base'] * gs.exit_mult_mod * sm
    equity = max(ebitda * em - debt, 0) * (1.0 - c.damage)  # damage reduces equity
    moic   = equity / max(c.entry_equity, 1)
    irr    = (moic ** (1 / max(yh, 0.25)) - 1) if yh > 0 else 0
    return {'equity': equity, 'moic': moic, 'irr': irr, 'yh': yh}

def apply_company_risks(gs, rng):
    """Each held company: 7% chance of bad event after 8 quarters."""
    for c in gs.companies:
        age = gs.quarter_num - c.entry_quarter
        if age >= MATURITY_THRESHOLD and rng.random() < COMPANY_RISK_PER_QTR:
            c.damage = min(c.damage + rng.uniform(0.10, 0.25), 0.70)

def pm(gs):
    ti = sum(c.entry_equity for c in gs.companies)
    to = sum(calc(c, gs)['equity'] for c in gs.companies)
    for e in gs.exited: ti += e['eq']; to += e['proc']
    return to / ti if ti > 0 else 1.0

def adv(gs, rng):
    gs.quarter_num += 1
    gs.deals = make_deals(gs, 5, rng)
    apply_company_risks(gs, rng)
    if rng.random() < 0.35:
        ev = rng.choice(EVENTS); eff = ev.get('effect')
        if eff == 'exit_mult': gs.exit_mult_mod = round(1 + ev['val'], 3)
        elif eff == 'growth':  gs.growth_mod    = round(1 + ev['val'], 3)
        elif eff == 'sector' and 'sector' in ev: gs.sector_mods[ev['sector']] = round(1 + ev['val'], 3)
    else:
        gs.exit_mult_mod = 1 + (gs.exit_mult_mod - 1) * 0.5
        gs.growth_mod    = 1 + (gs.growth_mod    - 1) * 0.5
    if gs.quarter_num >= gs.total_quarters: gs.screen = 'done'

def do_sell(gs, idx):
    c = gs.companies[idx]; m = calc(c, gs)
    gs.cash += m['equity']
    gs.exited.append({'eq': c.entry_equity, 'proc': m['equity'], 'moic': m['moic']})
    gs.companies.pop(idx)

def pick(gs, strat, rng):
    aff = [(i, d) for i, d in enumerate(gs.deals) if d.entry_equity <= gs.cash]
    if not aff: return None
    if strat == 'growth':    return max(aff, key=lambda x: x[1].growth)[0]
    if strat == 'value':     return min(aff, key=lambda x: x[1].entry_multiple)[0]
    if strat == 'random':    return rng.choice(aff)[0]
    if strat == 'diversify':
        held = {c.sector for c in gs.companies}
        fr   = [(i, d) for i, d in aff if d.sector not in held]
        return max(fr or aff, key=lambda x: x[1].growth)[0]
    if strat == 'cash_hoard':
        ch = [(i, d) for i, d in aff if d.entry_equity < gs.cash * 0.50]
        return max(ch, key=lambda x: x[1].growth)[0] if ch else None
    em = DIFFICULTY[gs.difficulty]['exit_mult_base']
    def p3(d): return d.revenue * ((1 + d.growth) ** 3) * d.margin * em / max(d.entry_equity, 1)
    return max(aff, key=lambda x: p3(x[1]))[0]

def sell_dec(gs, strat, rng):
    if not gs.companies: return None
    moics = [(i, calc(c, gs)['moic']) for i, c in enumerate(gs.companies)]
    if strat == 'random':    return max(moics, key=lambda x: x[1])[0] if rng.random() < 0.20 else None
    if strat == 'aggressive': return None
    t = {'growth': 1.8, 'value': 1.7, 'diversify': 2.0, 'cash_hoard': 1.5}.get(strat, 1.8)
    # Also sell if company is significantly damaged
    damage_sells = [(i, c) for i, c in enumerate(gs.companies) if c.damage > 0.30]
    if damage_sells: return damage_sells[0][0]
    hits = [(i, m) for i, m in moics if m > t]
    return max(hits, key=lambda x: x[1])[0] if hits else None

def run_one(args):
    seed, diff, strat = args
    rng = random.Random(seed)
    cfg = DIFFICULTY[diff]
    gs  = GS(difficulty=diff, cash=cfg['start_cash'])
    gs.deals = make_deals(gs, 5, rng)
    issues = []; buys = sells = 0

    for _ in range(cfg['quarters']):
        if gs.screen == 'done': break
        si = sell_dec(gs, strat, rng)
        if si is not None: do_sell(gs, si); sells += 1
        bi = pick(gs, strat, rng)
        if bi is not None:
            d = gs.deals[bi]
            if d.entry_equity > gs.cash: issues.append('OVERSPEND')
            else:
                gs.cash -= d.entry_equity; d.entry_quarter = gs.quarter_num
                gs.companies.append(d); gs.deals.pop(bi); buys += 1
        for c in gs.companies:
            m = calc(c, gs)
            if not math.isfinite(m['moic']): issues.append('NAN_MOIC')
            if m['moic'] > 40: issues.append(f'OUTLIER {m["moic"]:.1f}x')
            if m['equity'] < 0: issues.append(f'NEG_EQ')
        if gs.cash < -100: issues.append(f'NEG_CASH')
        adv(gs, rng)

    fm = pm(gs)
    if buys == 0: issues.append('ZERO_BUYS')
    if not math.isfinite(fm): issues.append('NAN_FINAL')
    return {'diff': diff, 'strat': strat, 'moic': fm,
            'won': fm >= cfg['goal_moic'], 'issues': issues,
            'buys': buys, 'sells': sells}

def main():
    print('Running 720 games (40×3×6)...')
    combos = [(s, d, st) for s in range(40)
              for d  in ['Easy', 'Balanced', 'Hard']
              for st in ['growth', 'value', 'random', 'diversify', 'cash_hoard', 'aggressive']]

    results = []
    with ProcessPoolExecutor() as ex:
        for r in as_completed(ex.submit(run_one, c) for c in combos):
            results.append(r.result())

    print('\n── WIN RATES')
    wr = defaultdict(list)
    for r in results: wr[(r['diff'], r['strat'])].append(r['won'])
    for diff in ['Easy', 'Balanced', 'Hard']:
        print(f'  {diff} (goal {DIFFICULTY[diff]["goal_moic"]}×):')
        for st in ['growth','value','random','diversify','cash_hoard','aggressive']:
            w = wr[(diff, st)]; pct = sum(w) / len(w) * 100 if w else 0
            flag = ' ← BROKEN' if (pct > 92 or pct < 8) else ''
            print(f'    {st:14s} {pct:5.1f}%{flag}')

    print('\n── MOIC DISTRIBUTION')
    md = defaultdict(list)
    for r in results:
        if math.isfinite(r['moic']): md[r['diff']].append(r['moic'])
    for diff, vals in md.items():
        sv = sorted(vals); n = len(sv)
        print(f'  {diff}: p25={sv[n//4]:.2f}  med={sv[n//2]:.2f}  p75={sv[3*n//4]:.2f}  max={sv[-1]:.2f}')

    print('\n── STRATEGY MOIC (all diffs)')
    sm = defaultdict(list)
    for r in results:
        if math.isfinite(r['moic']): sm[r['strat']].append(r['moic'])
    for st, vals in sorted(sm.items(), key=lambda x: -statistics.mean(x[1])):
        print(f'  {st:14s} avg={statistics.mean(vals):.2f}  std={statistics.stdev(vals):.2f}')

    all_issues = [(r['diff'], r['strat'], i) for r in results for i in r['issues']]
    print(f'\n── BUGS ({len(all_issues)} total)')
    seen = set()
    for d, s, i in all_issues:
        k = i[:80]
        if k not in seen: seen.add(k); print(f'  [{d}/{s}] {i}')
    if not all_issues: print('  ✅ None found.')

    all_moics = [r['moic'] for r in results if math.isfinite(r['moic'])]
    print(f'\n── OUTLIERS  max={max(all_moics):.2f}×  min={min(all_moics):.2f}×')

if __name__ == '__main__':
    main()
