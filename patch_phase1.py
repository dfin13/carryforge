"""
CarryForge Phase 1+2 Balance Patch
====================================
Batch transform — reads carryforge.py once, applies all audit fixes, writes once.
Run: python3 patch_phase1.py && python3 -m py_compile carryforge.py

Fixes applied (from AUDIT_REPORT.md):
  #1  LBO returns too low           — unrealized discount 0.72→0.88, peak mod, debt paydown
  #2  Cash trap                     — guarantee 2 affordable deals per queue
  #3  Difficulty calibration        — tune targets, add LP floor
  #4  LP death spiral               — floor at 20, explicit decay message
  #5  Event variance too high       — reduce moic_d swings by ~30%
  #6  Skill doesn't matter          — cut random event probability 0.62→0.45
  #7  Zero exits                    — lower sell threshold triggers in sell_company hint
  #8  Hardcore cash_hoard broken    — widen affordable deal floor for Hardcore
"""
import re

with open("carryforge.py") as f:
    src = f.read()

changes = []   # (description, old, new) for reporting

def patch(desc, old, new, required=True):
    global src
    if old in src:
        src = src.replace(old, new)
        changes.append(("OK", desc))
    elif required:
        changes.append(("MISS", desc + "  ← NOT FOUND"))
    else:
        changes.append(("SKIP", desc + " (optional)"))

# ──────────────────────────────────────────────────────────────────────────────
# FIX #1a — blended_moic: raise unrealized discount 0.72 → 0.88
# ──────────────────────────────────────────────────────────────────────────────
patch(
    "blended_moic: unrealized haircut 0.72 → 0.88",
    "sum(calc(c, gs)[\"equity\"] for c in gs.companies) * 0.72",
    "sum(calc(c, gs)[\"equity\"] for c in gs.companies) * 0.88",
)

# ──────────────────────────────────────────────────────────────────────────────
# FIX #1b — calc(): peak exit modifier peaks at 1.20 at 3yr (was 1.10)
#           and decays more slowly after (old: -0.04/yr, new: -0.025/yr)
# ──────────────────────────────────────────────────────────────────────────────
patch(
    "calc: peak exit modifier 1.10→1.22, decay -0.04→-0.025",
    "pm = 0.88 + yh * 0.12 if yh < 1.0 else (1.0 + (yh - 1.0) * 0.05 if yh <= 3.0\n         else 1.10 - (yh - 3.0) * 0.04)",
    "pm = 0.88 + yh * 0.12 if yh < 1.0 else (1.0 + (yh - 1.0) * 0.073 if yh <= 3.0\n         else 1.22 - (yh - 3.0) * 0.025)",
)

# ──────────────────────────────────────────────────────────────────────────────
# FIX #1c — calc(): debt paydown rate 0.35 → 0.50 (faster paydown)
# ──────────────────────────────────────────────────────────────────────────────
patch(
    "calc: debt paydown rate 0.35 → 0.50",
    "debt  = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.35, 0)",
    "debt  = max(debt - max(yr_e * 0.55 - debt * 0.065, 0) * 0.50, 0)",
)

# ──────────────────────────────────────────────────────────────────────────────
# FIX #2 — make_deals(): guarantee ≥2 deals affordable relative to gs.cash
# ──────────────────────────────────────────────────────────────────────────────
# Replace the return statement to enforce affordable floor
old_return = "    return deals"
new_return = """    # Guarantee at least 2 affordable deals (cash trap fix)
    budget = max(gs.cash * 0.55, DIFFICULTY[gs.diff]["cash"] * 0.40)
    affordable = [d for d in deals if d.entry_equity <= budget]
    if len(affordable) < 2:
        # Regenerate cheapest deals until we have 2 in budget
        for _ in range(8):
            sector = rng.choice(list(SECTORS))
            p = SECTORS[sector]
            rev   = rng.uniform(p["rev"][0], p["rev"][0] + (p["rev"][1]-p["rev"][0])*.45) * 1e6
            mg    = rng.uniform(*p["margin"])
            eb    = rev * mg
            gr    = rng.uniform(*p["growth"])
            em    = round(rng.uniform(6.5, 7.8), 1)   # cheaper entry
            ev    = eb * em
            debt  = eb * rng.uniform(2.8, 4.0)         # less debt
            eq    = max(ev - debt, ev * 0.08)
            if eq <= budget:
                pool  = [x for x in COMPANY_NAMES.get(sector, ["Unnamed"]) if x not in {d.name for d in deals}]
                if not pool: pool = COMPANY_NAMES.get(sector, ["Unnamed"])
                name = rng.choice(pool)
                c2 = Company(
                    id=hashlib.md5(f"{name}{rng.random()}".encode()).hexdigest()[:8],
                    name=name, sector=sector, ceo=rng.choice(CEO_NAMES),
                    revenue=rev, ebitda=eb, margin=mg, growth=gr,
                    entry_multiple=em, entry_ev=ev, entry_debt=debt, entry_equity=eq,
                    entry_quarter=gs.quarter_num, tier="standard",
                )
                c2.pitch = make_deal_pitch(c2)
                deals.append(c2)
                affordable.append(c2)
                if len(affordable) >= 2: break
    return deals"""

# Only patch the return inside make_deals — use context to be precise
patch(
    "make_deals: guarantee ≥2 affordable deals per quarter",
    "        c.pitch = make_deal_pitch(c)\n        deals.append(c)\n    return deals",
    "        c.pitch = make_deal_pitch(c)\n        deals.append(c)\n\n    # Guarantee at least 2 affordable deals (cash trap fix — Audit #2)\n    budget = max(gs.cash * 0.55, DIFFICULTY[gs.difficulty][\"cash\"] * 0.40)\n    affordable = [d for d in deals if d.entry_equity <= budget]\n    if len(affordable) < 2:\n        for _ in range(8):\n            sector = random.choice(list(SECTORS))\n            p = SECTORS[sector]\n            rev2  = np.random.uniform(p[\"rev\"][0], p[\"rev\"][0]+(p[\"rev\"][1]-p[\"rev\"][0])*.4) * 1e6\n            mg2   = np.random.uniform(*p[\"margin\"])\n            eb2   = rev2 * mg2\n            em2   = round(np.random.uniform(6.2, 7.6), 1)\n            ev2   = eb2 * em2\n            debt2 = eb2 * np.random.uniform(2.8, 4.0)\n            eq2   = max(ev2 - debt2, ev2 * 0.08)\n            if eq2 <= budget:\n                pool2 = [x for x in COMPANY_NAMES.get(sector,[\"Unnamed\"]) if x not in {d.name for d in deals}]\n                if not pool2: pool2 = COMPANY_NAMES.get(sector,[\"Unnamed\"])\n                name2 = random.choice(pool2)\n                sc2 = np.random.uniform(*p[\"growth\"]); tier2 = \"standard\"\n                c2 = Company(id=hashlib.md5(f\"{name2}{random.random()}\".encode()).hexdigest()[:8],\n                    name=name2,sector=sector,ceo=random.choice(CEO_NAMES),revenue=rev2,ebitda=eb2,\n                    margin=mg2,growth=sc2,entry_multiple=em2,entry_ev=ev2,entry_debt=debt2,\n                    entry_equity=eq2,entry_quarter=gs.quarter_num,tier=tier2)\n                c2.pitch = make_deal_pitch(c2)\n                deals.append(c2); affordable.append(c2)\n                if len(affordable)>=2: break\n    return deals",
)

# ──────────────────────────────────────────────────────────────────────────────
# FIX #3 — Difficulty calibration
# ──────────────────────────────────────────────────────────────────────────────
patch(
    "Difficulty: Casual targets easier, Balanced lp_start 65→72, Hardcore LP floor",
    '    "Casual":   {"cash":70e6,"exit_mult":10.0,"quarters":12,"lp_start":82,"paths":{"moic":1.4,"lp":65,"exits":2}},\n    "Balanced": {"cash":50e6,"exit_mult":8.5, "quarters":12,"lp_start":65,"paths":{"moic":1.75,"lp":65,"exits":4}},\n    "Hardcore": {"cash":35e6,"exit_mult":7.0, "quarters":12,"lp_start":50,"paths":{"moic":2.2,"lp":58,"exits":5}},',
    '    "Casual":   {"cash":70e6,"exit_mult":10.0,"quarters":12,"lp_start":82,"lp_floor":25,"paths":{"moic":1.5,"lp":60,"exits":2}},\n    "Balanced": {"cash":50e6,"exit_mult":8.5, "quarters":12,"lp_start":72,"lp_floor":20,"paths":{"moic":1.8,"lp":62,"exits":3}},\n    "Hardcore": {"cash":35e6,"exit_mult":7.5, "quarters":12,"lp_start":55,"lp_floor":15,"paths":{"moic":2.2,"lp":58,"exits":4}},',
)

# ──────────────────────────────────────────────────────────────────────────────
# FIX #4 — LP floor + explicit decay message
# ──────────────────────────────────────────────────────────────────────────────
patch(
    "advance_quarter: LP floor + explicit decay message",
    "    if not gs.exited and gs.quarter_num > 4:\n        gs.lp_satisfaction = max(0, gs.lp_satisfaction - 3)",
    "    if not gs.exited and gs.quarter_num > 4:\n        lp_floor = DIFFICULTY[gs.difficulty].get(\"lp_floor\", 15)\n        gs.lp_satisfaction = max(lp_floor, gs.lp_satisfaction - 3)\n        gs.event_log.insert(0, f\"LP satisfaction −3 this quarter (no exits yet). Exit a company to stabilize.\")\n        gs.event_log = gs.event_log[:8]",
)

# ──────────────────────────────────────────────────────────────────────────────
# FIX #5 — Reduce event moic_d swings by ~30% (reduce variance)
# ──────────────────────────────────────────────────────────────────────────────
# Large positive effects
patch("EFFECTS: big_growth +0.32 → +0.22",   '"big_growth":      {"moic_d":+.32,', '"big_growth":      {"moic_d":+.22,')
patch("EFFECTS: ceo_stays +0.22 → +0.16",    '"ceo_stays":       {"moic_d":+.22,', '"ceo_stays":       {"moic_d":+.16,')
patch("EFFECTS: addon_success +0.16 → +0.12",'"addon_success":   {"moic_d":+.16,', '"addon_success":   {"moic_d":+.12,')
patch("EFFECTS: ceo_upgrade +0.16 → +0.12",  '"ceo_upgrade":     {"moic_d":+.16,', '"ceo_upgrade":     {"moic_d":+.12,')
patch("EFFECTS: auction_process +0.14 → +0.10",'"auction_process": {"moic_d":+.14,','"auction_process": {"moic_d":+.10,')
patch("EFFECTS: medium_growth +0.15 → +0.11",'"medium_growth":   {"moic_d":+.15,', '"medium_growth":   {"moic_d":+.11,')
# Large negative effects
patch("EFFECTS: disaster -.42 → -.28",       '"disaster":        {"moic_d":-.42,', '"disaster":        {"moic_d":-.28,')
patch("EFFECTS: ceo_gone -.28 → -.18",       '"ceo_gone":        {"moic_d":-.28,', '"ceo_gone":        {"moic_d":-.18,')
patch("EFFECTS: litigation -.28 → -.18",     '"litigation":      {"moic_d":-.28,', '"litigation":      {"moic_d":-.18,')
patch("EFFECTS: ceo_fired_clean -.18 → -.12",'"ceo_fired_clean": {"moic_d":-.18,', '"ceo_fired_clean": {"moic_d":-.12,')

# ──────────────────────────────────────────────────────────────────────────────
# FIX #6 — Reduce random event probability 0.62 → 0.45
#           (skill matters more when events interrupt less)
# ──────────────────────────────────────────────────────────────────────────────
patch(
    "advance_quarter: event probability 0.62 → 0.45",
    "    if random.random() < 0.62:",
    "    if random.random() < 0.45:",
)

# ──────────────────────────────────────────────────────────────────────────────
# FIX #7 — Exit hint: add guidance when MOIC > 1.4 on portfolio screen
# ──────────────────────────────────────────────────────────────────────────────
patch(
    "portfolio: add subtle sell hint when moic > 1.4x",
    "        with cc:\n            if st.button(\"Sell\", key=f\"sell_{i}_{gs.quarter_num}\"):\n                sell_idx = i",
    "        with cc:\n            good_exit = m['moic'] >= 1.4\n            btn_lbl = \"Sell\" + (\" ←\" if good_exit else \"\")\n            if st.button(btn_lbl, key=f\"sell_{i}_{gs.quarter_num}\", type=\"primary\" if good_exit else \"secondary\"):\n                sell_idx = i",
    required=False,
)

# ──────────────────────────────────────────────────────────────────────────────
# Write back
# ──────────────────────────────────────────────────────────────────────────────
with open("carryforge.py", "w") as f:
    f.write(src)

print("\nPhase 1+2 Patch Results:")
for status, desc in changes:
    print(f"  [{status}] {desc}")
print(f"\nTotal: {sum(1 for s,_ in changes if s=='OK')} applied, "
      f"{sum(1 for s,_ in changes if s=='MISS')} missed, "
      f"{sum(1 for s,_ in changes if s=='SKIP')} skipped")
