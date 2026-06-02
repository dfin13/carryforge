"""
CarryForge Opacity Patch
=========================
Removes information that makes optimal choices too obvious:
  1. Deal cards: remove HOT/RISK tier badge chips
  2. Deal cards: replace computed Est 3yr MOIC with qualitative growth/margin signals
  3. Sell button: plain "Sell" with no arrow or primary highlighting
  4. Lever tooltips: replace exact % stats with qualitative risk descriptors

Run: python3 patch_opacity.py && python3 -m py_compile carryforge.py
"""

with open("carryforge.py") as f:
    src = f.read()

changes = []

def patch(desc, old, new, required=True):
    global src
    if old in src:
        src = src.replace(old, new)
        changes.append(("OK", desc))
    elif required:
        changes.append(("MISS", desc + "  ← NOT FOUND"))
    else:
        changes.append(("SKIP", desc + " (optional)"))

# ── FIX 1: Remove p3 computation and tier_chip from tab_deals ────────────────
patch(
    "deal cards: remove proj3 computation and tier_chip HOT/RISK badge",
    """        sec  = SECTORS[d.sector]
        p3   = proj3(d, gs)
        can  = d.entry_equity <= gs.cash and not full
        lev  = d.entry_debt / max(d.ebitda, 1)
        dot  = SECTOR_DOT_COLOR[d.sector]
        tier_chip = (f'<span class="chip chip-hot">HOT</span>' if d.tier == "hot"
                     else f'<span class="chip chip-risk">RISK</span>' if d.tier == "risky" else "")""",
    """        sec  = SECTORS[d.sector]
        can  = d.entry_equity <= gs.cash and not full
        lev  = d.entry_debt / max(d.ebitda, 1)
        dot  = SECTOR_DOT_COLOR[d.sector]
        # Qualitative signals — no computed MOIC
        gr = d.growth
        mg = d.margin
        gr_label = "Accelerating" if gr >= 0.18 else ("Growing" if gr >= 0.10 else ("Steady" if gr >= 0.05 else "Mature"))
        mg_label = "Strong" if mg >= 0.22 else ("Moderate" if mg >= 0.14 else "Thin")""",
)

# ── FIX 2: Remove tier_chip from header and Est 3yr metric ───────────────────
patch(
    "deal cards: remove tier_chip from header HTML",
    """              <div style="display:flex;align-items:center;gap:.45rem;margin-bottom:.35rem">
                <span class="dot" style="background:{dot};width:10px;height:10px"></span>
                <h3>{d.name}</h3> {tier_chip}
              </div>""",
    """              <div style="display:flex;align-items:center;gap:.45rem;margin-bottom:.35rem">
                <span class="dot" style="background:{dot};width:10px;height:10px"></span>
                <h3>{d.name}</h3>
              </div>""",
)

# ── FIX 3: Replace Est 3yr computed value with qualitative growth/margin ──────
patch(
    "deal cards: replace Est 3yr MOIC with qualitative momentum signals",
    """            <div style="display:flex;gap:.6rem;align-items:center;height:100%;padding:.4rem 0">
              <div style="text-align:center">
                <div class="num-md">{cf(d.entry_equity)}</div>
                <div class="lbl">Equity</div>
              </div>
              <div style="width:1px;height:32px;background:rgba(255,255,255,.07)"></div>
              <div style="text-align:center">
                <div class="num-md {mc(p3)}">{p3:.1f}×</div>
                <div class="lbl">Est 3yr</div>
              </div>
            </div>""",
    """            <div style="display:flex;gap:.6rem;align-items:center;height:100%;padding:.4rem 0">
              <div style="text-align:center">
                <div class="num-md">{cf(d.entry_equity)}</div>
                <div class="lbl">Equity</div>
              </div>
              <div style="width:1px;height:32px;background:rgba(255,255,255,.07)"></div>
              <div style="text-align:center;max-width:72px">
                <div style="font-size:.72rem;font-weight:600;color:#94a3b8">{gr_label}</div>
                <div style="font-size:.68rem;color:#64748b">{mg_label} margin</div>
              </div>
            </div>""",
)

# ── FIX 4: Plain sell button — no arrow, no primary type ─────────────────────
patch(
    "sell button: remove good_exit highlight and arrow indicator",
    """            good_exit = m['moic'] >= 1.4
            btn_lbl = "Sell" + (" ←" if good_exit else "")
            if st.button(btn_lbl, key=f"sell_{i}_{gs.quarter_num}", type="primary" if good_exit else "secondary"):
                sell_idx = i""",
    """            if st.button("Sell", key=f"sell_{i}_{gs.quarter_num}"):
                sell_idx = i""",
)

# ── FIX 5: Lever tooltips — qualitative risk descriptors ─────────────────────
patch(
    "lever tooltips: replace exact % stats with qualitative descriptors",
    """            sr = int(lev['success_rate']*100)
            title = f"title=\\"{lev['desc']}  |  {sr}% success  |  +{lev['win_moic']*100:.0f}% win / {lev['loss_moic']*100:.0f}% loss\\""""",
    """            _sr = lev['success_rate']
            _risk = "Low risk" if _sr >= 0.75 else ("Balanced" if _sr >= 0.60 else "High risk / high reward")
            title = f"title=\\"{lev['desc']}  |  {_risk}\\""""",
)

# ── Write back ────────────────────────────────────────────────────────────────
with open("carryforge.py", "w") as f:
    f.write(src)

print("\nOpacity Patch Results:")
for status, desc in changes:
    print(f"  [{status}] {desc}")
print(f"\nTotal: {sum(1 for s,_ in changes if s=='OK')} applied, "
      f"{sum(1 for s,_ in changes if s=='MISS')} missed, "
      f"{sum(1 for s,_ in changes if s=='SKIP')} skipped")
