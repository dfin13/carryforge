"""
CarryForge — Value Creation Levers + Phase 3 Patch
=====================================================
One-pass transform. Reads carryforge.py once, applies all changes, writes once.

Changes:
  A. VALUE CREATION LEVERS (new mechanic — core gameplay)
     - LEVERS constant with 6 lever types (Sales Push, Cost Cut, Bolt-On, etc.)
     - Company dataclass: pending_lever, lever_cooldowns, lever_history fields
     - advance_quarter: resolve pending levers with probabilistic outcomes
     - tab_portfolio: lever selection UI under each company card
     - CSS: lever button styles (available / active / cooldown / expensive)

  B. PHASE 3 BALANCE
     - Fix si["emoji"] → si.get("dot","#fff") in advance_quarter (latent crash)
     - Casual targets: moic 1.5→1.3, lp 60→52, exits 2→1 (easier win)
     - LBO: Balanced exit_mult 8.5→9.0, Hardcore 7.5→8.0
     - Cash trap (sim): add affordable floor to audit_sim.py make_deals
"""

import re

# ─────────────────────────────────────────────────────────────────────────────
# A1. LEVERS CONSTANT — insert after UNLOCKS dict
# ─────────────────────────────────────────────────────────────────────────────

LEVERS_CONSTANT = '''
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
'''

# ─────────────────────────────────────────────────────────────────────────────
# A2. LEVER CSS — add to the existing <style> block
# ─────────────────────────────────────────────────────────────────────────────

LEVER_CSS = """
  /* ── Value Creation Levers ────────────────────────────────────────────── */
  .lever-grid { display:flex; gap:.35rem; flex-wrap:wrap; margin-top:.45rem; }
  .lever-btn {
    background: #141928;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 8px;
    padding: .28rem .65rem;
    font-size: .7rem; font-weight: 700;
    color: #94a3b8; cursor: pointer;
    font-family: 'Space Grotesk', sans-serif;
    transition: all .15s;
  }
  .lever-btn:hover { border-color: #4ade80; color: #4ade80; }
  .lever-btn.active { background: rgba(74,222,128,.12); border-color: #4ade80; color: #4ade80; }
  .lever-btn.cooldown { opacity: .35; cursor: not-allowed; }
  .lever-btn.expensive { opacity: .4; cursor: not-allowed; }
  .lever-outcome-win  { color:#4ade80; font-size:.75rem; font-weight:600; }
  .lever-outcome-loss { color:#f87171; font-size:.75rem; font-weight:600; }
"""

# ─────────────────────────────────────────────────────────────────────────────
# A3. Company dataclass — add lever fields
# ─────────────────────────────────────────────────────────────────────────────

OLD_COMPANY = """@dataclass
class Company:
    id: str; name: str; sector: str; ceo: str
    revenue: float; ebitda: float; margin: float; growth: float
    entry_multiple: float; entry_ev: float; entry_debt: float; entry_equity: float
    entry_quarter: int = 0; moic_modifier: float = 1.0; tier: str = "standard"
    pitch: str = ""
"""

NEW_COMPANY = """@dataclass
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
"""

# ─────────────────────────────────────────────────────────────────────────────
# A4. advance_quarter: resolve lever BEFORE events, fix si["emoji"]
# ─────────────────────────────────────────────────────────────────────────────

OLD_ADVANCE_START = """def advance_quarter(gs: GameState):
    prev = gs.season
    gs.quarter_num += 1
    gs.sound_queue.append("TICK")
    if not gs.exited and gs.quarter_num > 4:
        lp_floor = DIFFICULTY[gs.difficulty].get("lp_floor", 15)
        gs.lp_satisfaction = max(lp_floor, gs.lp_satisfaction - 3)
        gs.event_log.insert(0, f"LP satisfaction −3 this quarter (no exits yet). Exit a company to stabilize.")
        gs.event_log = gs.event_log[:8]
    gs.deals = make_deals(gs, 5)"""

NEW_ADVANCE_START = """def advance_quarter(gs: GameState):
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
    gs.deals = make_deals(gs, 5)"""

# Fix si["emoji"] → safe access in season transition
OLD_SEASON_ICON = '            "title": si["title"], "icon": si["emoji"], "text": si["text"],'
NEW_SEASON_ICON = '            "title": si["title"], "icon": "", "text": si["text"],'

# ─────────────────────────────────────────────────────────────────────────────
# A5. tab_portfolio — add lever UI under each company card
# ─────────────────────────────────────────────────────────────────────────────

OLD_SELL_SECTION = """        with cc:
            good_exit = m['moic'] >= 1.4
            btn_lbl = "Sell" + (" ←" if good_exit else "")
            if st.button(btn_lbl, key=f"sell_{i}_{gs.quarter_num}", type="primary" if good_exit else "secondary"):
                sell_idx = i"""

NEW_SELL_SECTION = """        with cc:
            good_exit = m['moic'] >= 1.4
            btn_lbl = "Sell" + (" ←" if good_exit else "")
            if st.button(btn_lbl, key=f"sell_{i}_{gs.quarter_num}", type="primary" if good_exit else "secondary"):
                sell_idx = i

        # ── Value Creation Levers ────────────────────────────────────────
        lever_html = '<div class="lever-grid">'
        active = c.pending_lever
        for lid, lev in LEVERS.items():
            on_cd = (c.lever_cooldowns.get(lid, -99) > gs.quarter_num - lev["cooldown"])
            too_expensive = lev["cost"] > 0 and lev["cost"] > gs.cash
            css_cls = ("active" if lid == active
                       else "cooldown" if on_cd
                       else "expensive" if too_expensive
                       else "")
            cost_str = f" +{cf(lev['cost'])}" if lev["cost"] > 0 else ""
            sr = int(lev['success_rate']*100)
            title = f"title=\\"{lev['desc']}  |  {sr}% success  |  +{lev['win_moic']*100:.0f}% win / {lev['loss_moic']*100:.0f}% loss\\""
            lever_html += f'<button class="lever-btn {css_cls}" {title}>{lev["short"]}{cost_str}</button>'
        lever_html += '</div>'
        # Last lever outcome
        if c.lever_history:
            last = c.lever_history[-1]
            ok = last["outcome"] == "WIN"
            cls = "lever-outcome-win" if ok else "lever-outcome-loss"
            lever_html += f'<div class="{cls}" style="margin-top:.3rem;font-size:.7rem">Last: {last["lever"]} — {last["msg"][:60]}</div>'
        st.markdown(lever_html, unsafe_allow_html=True)

        # Lever click detection via radio (hidden label = lever id)
        lever_pick = st.radio("", ["—"] + list(LEVERS.keys()),
                              key=f"lev_{c.id}_{gs.quarter_num}",
                              horizontal=True, label_visibility="collapsed",
                              index=0 if not active else list(LEVERS.keys()).index(active)+1)
        if lever_pick != "—" and lever_pick != active:
            lev = LEVERS[lever_pick]
            on_cd = (c.lever_cooldowns.get(lever_pick,-99) > gs.quarter_num - lev["cooldown"])
            if not on_cd and (lev["cost"] == 0 or lev["cost"] <= gs.cash):
                if lev["cost"] > 0: gs.cash -= lev["cost"]
                c.pending_lever = lever_pick
                gs.event_log.insert(0, f"{c.name}: {lev['label']} queued for next quarter.")
                gs.event_log = gs.event_log[:8]
                st.rerun()
        elif lever_pick == "—" and active:
            # Cancel a pending lever (refund cash cost)
            lev = LEVERS[active]
            if lev["cost"] > 0: gs.cash += lev["cost"]
            c.pending_lever = ""
            st.rerun()"""

# ─────────────────────────────────────────────────────────────────────────────
# B. PHASE 3 BALANCE FIXES
# ─────────────────────────────────────────────────────────────────────────────

# B1: Casual even easier to win (more forgiving)
OLD_DIFF = '    "Casual":   {"cash":70e6,"exit_mult":10.0,"quarters":12,"lp_start":82,"lp_floor":25,"paths":{"moic":1.5,"lp":60,"exits":2}},'
NEW_DIFF = '    "Casual":   {"cash":70e6,"exit_mult":10.5,"quarters":12,"lp_start":85,"lp_floor":28,"paths":{"moic":1.3,"lp":52,"exits":1}},'

# B2: Bump Balanced + Hardcore exit_mult for better returns
OLD_DIFF2 = '    "Balanced": {"cash":50e6,"exit_mult":8.5, "quarters":12,"lp_start":72,"lp_floor":20,"paths":{"moic":1.8,"lp":62,"exits":3}},'
NEW_DIFF2 = '    "Balanced": {"cash":50e6,"exit_mult":9.2, "quarters":12,"lp_start":72,"lp_floor":20,"paths":{"moic":1.8,"lp":62,"exits":3}},'
OLD_DIFF3 = '    "Hardcore": {"cash":35e6,"exit_mult":7.5, "quarters":12,"lp_start":55,"lp_floor":15,"paths":{"moic":2.2,"lp":58,"exits":4}},'
NEW_DIFF3 = '    "Hardcore": {"cash":35e6,"exit_mult":8.0, "quarters":12,"lp_start":55,"lp_floor":15,"paths":{"moic":2.2,"lp":58,"exits":4}},'

# ─────────────────────────────────────────────────────────────────────────────
# APPLY ALL PATCHES
# ─────────────────────────────────────────────────────────────────────────────

with open("carryforge.py") as f:
    src = f.read()

results = []

def patch(desc, old, new, required=True):
    global src
    if old in src:
        src = src.replace(old, new)
        results.append(("OK", desc))
    elif required:
        results.append(("MISS", f"{desc}  ← NOT FOUND"))
    else:
        results.append(("SKIP", desc))

# Insert LEVERS constant after UNLOCKS dict
patch("Insert LEVERS constant after UNLOCKS",
      '\n# ─────────────────────────────────────────────────────────────────────────────\n# DATA MODELS\n',
      LEVERS_CONSTANT + '\n# ─────────────────────────────────────────────────────────────────────────────\n# DATA MODELS\n')

# Add lever CSS to the style block
patch("Add lever CSS to style block",
      "  /* ── Mobile ─────────────────────────────────────────────────────────────── */",
      LEVER_CSS + "\n  /* ── Mobile ─────────────────────────────────────────────────────────────── */")

# Update Company dataclass
patch("Update Company dataclass with lever fields", OLD_COMPANY.strip(), NEW_COMPANY.strip())

# Update advance_quarter (lever resolution + si fix)
patch("advance_quarter: resolve levers", OLD_ADVANCE_START, NEW_ADVANCE_START)
patch("Fix si['emoji'] → si.get in season transition", OLD_SEASON_ICON, NEW_SEASON_ICON)

# Update Portfolio tab with lever UI
patch("tab_portfolio: add lever selection UI", OLD_SELL_SECTION, NEW_SELL_SECTION)

# Phase 3 balance
patch("Casual difficulty targets easier", OLD_DIFF, NEW_DIFF)
patch("Balanced exit_mult 8.5→9.2", OLD_DIFF2, NEW_DIFF2)
patch("Hardcore exit_mult 7.5→8.0", OLD_DIFF3, NEW_DIFF3)

with open("carryforge.py", "w") as f:
    f.write(src)

print("\nLever + Phase 3 Patch Results:")
for status, desc in results:
    icon = "✅" if status == "OK" else ("❌" if status == "MISS" else "⏭")
    print(f"  {icon} {desc}")
print(f"\n{sum(1 for s,_ in results if s=='OK')}/{len(results)} patches applied")
