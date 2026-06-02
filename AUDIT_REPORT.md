# CarryForge — Full Audit Report
**720 games simulated · 6 strategies · 3 difficulties · 40 seeds each**

---

## IMMEDIATE CRASHES (already fixed)
- ✅ `Plotly ValueError: geo bgcolor/showgrid` — invalid keys in Plotly 6.x
- ✅ `sqlite3.OperationalError` — DB path inside read-only git mount
- ✅ `$0.0M equity cost` — sector rev ranges were in $M concepts but not multiplied by 1e6
- ✅ `KeyError: si['desc']` — SEASONS uses 'text' not 'desc'

---

## CRITICAL — Balance & Mechanics (Game-Breaking)

### 1. LBO Returns Are Too Low
**Simulation finding:** 3-year hold MOIC averages ~1.17–1.25x across all strategies. Real PE targets 2.5–3.5x at 3 years.
**Root cause analysis:**
- `blended_moic()` applies a `0.72×` haircut to all unrealized holdings. This is overly aggressive (real PE uses 0.85–0.90×)
- Exit multiple peak modifier tops out at `1.10×` for a 3-year hold, which is only a 10% boost
- Debt paydown over 3 years is minimal (~$15M on $90M debt typical), leaving huge debt overhang at exit
- Combined effect: player feels like returns never materialize
**Impact:** Every game feels like a failure. The core game loop (invest → grow → exit for profit) doesn't deliver satisfying numbers.
**Fix direction:** Raise unrealized discount to 0.88×, raise peak exit modifier to 1.25× at 3yr, accelerate debt paydown rate.

### 2. Cash Trap — 69% of Games Hit Dead Ends
**Simulation finding:** 496/720 games (69%) had periods where players had cash but couldn't afford any deal. The `cash_hoard` strategy was stuck for 12 consecutive quarters.
**Root cause:** Starting cash ($50M Balanced) vs. typical equity check ($30–80M). After 1 deal, players often can't afford a second. After selling, the proceeds are large but deal sizes scale with them.
**Impact:** Players stare at 5 un-affordable deals every quarter, feel frustrated, and the game stalls.
**Fix direction:**
- Generate 1–2 "small cap" deals per quarter (equity check ≤ 30% of current cash)
- Add a "pass on deal" option that unlocks a replacement smaller deal
- Reduce minimum deal size or add a $15–25M micro-deal tier for early quarters

### 3. Skill Doesn't Matter — Random Beats Optimized Strategies
**Simulation finding:**
- `random` strategy: avg MOIC 1.31x (HIGHEST)
- `proj_moic` (most analytical strategy): avg 1.25x
- `greedy_growth`: avg 1.21x
- The best analytical strategy underperforms random play
**Root cause:** Random events are the dominant return driver. The 62% event chance each quarter swamps any strategic signal from deal selection. A "good" deal (high growth) often doesn't outperform a "bad" deal because a positive moic_mod event on a bad deal beats negative events on a good deal.
**Impact:** Players learn quickly that their decisions don't matter, killing engagement. The "PE strategy" fantasy collapses.
**Fix direction:**
- Reduce event randomness weight — events should be ±10-15% max, not ±28-42%
- Make growth rate much more predictive of returns (current: growth contributes ~25% of variance; target: 50%)
- Add "skill multiplier" — good decisions (buying cheap, diversifying sectors) should meaningfully boost outcomes

### 4. 24% of Games Have Zero Exits
**Simulation finding:** 174/720 games ended with no exits at all.
**Root cause:** Sell thresholds are too high (2.0× MOIC required), and MOIC rarely exceeds 1.5× due to low returns issue above. Players rationally hold hoping it improves, but it never does.
**Impact:** LP Legend path becomes impossible (no DPI), LP satisfaction death-spirals, and the deal-maker path needs 4 exits on Balanced — nearly impossible with zero.
**Fix direction:** Lower MOIC thresholds, make 1.4× feel like a win worth celebrating, add a "smart exit timing" hint when conditions are favorable.

---

## HIGH PRIORITY — Balance Issues

### 5. Difficulty Calibration Is Off
**Simulation finding:**
- Casual: 85–100% win rate (should be 60–70%)
- Balanced: 25–77% win rate (huge variance between strategies — cash_hoard 25% vs value 77%)
- Hardcore: 2.5–45% win rate (should be 25–40%)

**Casual too easy:** Every strategy wins easily. No tension. No decisions matter.
**Hardcore broken for conservative players:** `cash_hoard` wins 2.5% of the time — effectively unwinnable. The LP path (`keep LPs ≥ 58`) becomes impossible after repeated quarters without exits, causing LP death spiral.

**Fix direction:**
- Casual: Lower exit_mult_base from 10.0 to 9.0 and tighten deal cost spreads
- Hardcore: LP satisfaction decay should stop at 35 (floor), not 0, to prevent unrecoverable spirals
- Add "Balanced" as the actual sweet spot with 50–60% win rate for good players

### 6. LP Satisfaction Death Spiral
**Simulation finding:** 22 games (3%) hit LP satisfaction below 20 — effectively game over but the game doesn't tell you. 18/22 were Hardcore.
**Root cause:** LP decays 3/quarter when no exits, but with the cash trap preventing exits and low MOIC making selling feel wrong, satisfaction craters without player understanding why.
**Impact:** Players feel punished without understanding what to do differently.
**Fix direction:**
- LP satisfaction floor at 20 (can't fall below — LPs grumble but don't leave)
- Add a "LP intervention" event when satisfaction drops below 35: a specific actionable choice
- Make the LP decay message much more explicit: "LP satisfaction drops 3 pts this quarter because you haven't returned any capital"

### 7. 57% of Games Have >65% Cash Undeployed
**Simulation finding:** On average, 57% of games left more than 65% of starting capital sitting idle throughout the game.
**Implication:** Players feel like they're missing out on the "empire building" fantasy. A PE fund with 65% dry powder and nothing to deploy is a failed fund.
**Fix direction:**
- Ensure at least 2 deals per quarter are affordable (< 60% of current cash)
- Add "LP pressure" for holding too much dry powder too long: "LPs question why 68% of committed capital is undeployed"
- Reduce deal equity costs by 15–20% across the board

---

## MEDIUM PRIORITY — Gameplay Depth

### 8. Strategy Is Solved in 5 Minutes
**Finding:** There are only 3 visible deal attributes (sector, growth%, entry multiple). The optimal strategy is immediately obvious: buy high-growth, low-multiple deals. Once a player figures this out, there's no more decision-making.
**What's missing:**
- No counterplay tension (e.g., high growth = higher covenant risk = crisis events more likely)
- No market timing decisions (Season 1 vs 3 has no current player agency)
- No portfolio construction meta (there's no synergy between sectors)
- No leverage tradeoffs (all deals use the same debt formula)
**Fix direction:**
- Add hidden deal traits (revealed through "diligence"): customer concentration, management quality, IP moat
- Add leverage choice: pick 3x, 4x, or 5x debt at entry. High leverage = higher return potential + higher crisis probability
- Make high-growth deals more expensive (growth premium), so cheap + moderate-growth can outperform

### 9. Events Are Narrative Dead Ends
**Current state:** 16 events with 3 choices each. But:
- Outcomes of choices are never referenced again
- No "state persistence" — if you fired a CEO, the company doesn't act differently
- The same CEO can be "poached" multiple times (no dedup)
- Most "nothing" choices are identical to "slight_miss" outcomes
- Events don't respond to company age (a 2-week-old deal shouldn't have CEO poaching)
**Impact:** Events feel like random number generators with flavor text, not decisions.
**Fix direction:**
- Add event cooldowns (no same event type within 4 quarters per company)
- Persist event outcomes as company "flags" that affect future events and moic_mod
- Add 5–8 "follow-up" events that only trigger if prior events occurred

### 10. Sectors Are Purely Cosmetic
**Finding:** Sector choice has zero strategic impact beyond visual differentiation. SaaS companies behave identically to Healthcare — only the generated growth rate differs.
**What should differ by sector:**
- Event distribution (Healthcare gets FDA events, SaaS gets customer churn, etc.)
- LP reaction (ESG LP hates Industrial/Logistics, loves Healthcare)
- Exit multiple sensitivity (SaaS multiples compress harder in The Reckoning)
- Recession resilience (Healthcare more defensive, Consumer more cyclical)
**Fix direction:** Sector-specific event tables + sector modifiers per season

### 11. No Meaningful Add-On M&A
**Current state:** Add-on M&A appears as a random event ("Bolt-On Opportunity") with a +0.15 moic_mod outcome. It has no mechanics — no cash outlay, no integration risk, no EBITDA accretion modeling.
**What it should be:** An active player choice with a real capital decision. "Spend $8M on a bolt-on" should deduct cash, add ~15% EBITDA, and create integration risk events.
**Fix direction:** Make add-ons a player-initiated action available on Portfolio screen for owned companies

### 12. The 3D Globe Is Purely Visual (No Gameplay)
**Current state:** Globe shows company locations, but clicking a pin doesn't do anything, and locations are random — you can't invest in specific geographies.
**Opportunity:** Geography could be a meaningful mechanic:
- "European headquarters" unlocks EU LP types
- "Emerging market exposure" triggers specific events
- "Geographic diversification" bonus for holding companies across 3+ regions
**Fix direction:** For now, make globe pins clickable (jumps to portfolio tab for that company). Long-term: geographic investment meta-game.

---

## LOW PRIORITY — UX & Polish

### 13. Score Screen Doesn't Teach
**Current state:** You get a letter grade and paths hit count. That's it.
**What's missing:**
- Which decisions mattered most (best/worst deal)
- What you should do differently next time
- How your MOIC compares to typical players
- Timeline view of your J-curve
**Fix direction:** Post-game "debrief" showing your best exit, biggest mistake, and one tactical tip for your next run.

### 14. No Onboarding / Tutorial
**Finding:** First-time players see 5 deal cards with metrics they don't understand (entry multiple, leverage ratio, etc.) and a "Next Quarter" button. There's no guidance.
**Current hint:** A single text hint on the Overview tab if you have no companies. Insufficient.
**Fix direction:** 3-step interactive tutorial: (1) explain the loop, (2) walk through one deal selection, (3) show a simulated quarter advance.

### 15. The "Next Quarter" Button Feels Cheap
**Current state:** Clicking "Next Quarter" immediately rerenders the page. There's no animation, no loading state, no "results reel."
**What players expect:** A 1–2 second transition that shows what happened this quarter (growth, events, LP changes) as a brief highlight.
**Fix direction:** Use `st.progress` + `time.sleep(0.1)` animation or a modal-style "Quarter Results" card that appears before the page refreshes.

### 16. Win Paths Are Always Visible But Often Impossible
**Current state:** All 3 win paths are displayed with progress throughout the game.
**Problem:** By Quarter 8, if you're on Hardcore and LP satisfaction is 45 (target: 60), the LP path is mathematically impossible. But it keeps showing as "behind" — creating false hope and confusion.
**Fix direction:** Add "locked out" visual state (gray out path if mathematically impossible) with tooltip explaining why. Also add "still achievable!" confidence indicator.

### 17. Deal Cards Don't Show IRR
**Current state:** Deal cards show estimated 3yr MOIC.
**Missing:** Estimated 3yr IRR (more actionable for experienced players who think in IRR terms).
**Fix direction:** Show both: `1.8× · 24% IRR` on the deal card.

### 18. Fund Tab Is Passive — Should Be Active
**Current state:** Fund tab shows LP characters + rival intel. No actions.
**Opportunity:** Fund management should have player-driven decisions:
- "Call LP" action: spend relationship credit to request patience (pauses LP decay for 2Q)
- "Issue LP Update" deck: small LP satisfaction boost for doing good comms
- "Co-invest offer": let an LP co-invest alongside you in a specific deal (extra capital but LP gets carried interest exposure)
**Fix direction:** Add 1–2 active LP actions per quarter on the Fund tab

### 19. Market Tab Doesn't Drive Decisions
**Current state:** Market tab shows season info and a globe. Informational only.
**Missing:** Forward guidance — what should players actually DO with this information?
- "The Reckoning is coming in 2Q — should you accelerate exits?"
- "Bull market: seller's market. Entry multiples are elevated — be selective."
**Fix direction:** Add "Market Intelligence" section with 2–3 actionable callouts per season

### 20. Rival Firms Have No Actual Impact
**Current state:** Rival firms appear in some events ("Apex Capital bid $8M over you") and on the Fund tab. That's it.
**What they should do:** Rival firms should:
- Bid on deals (making some deals unavailable unless you outbid)
- Track their own performance (rival AUM grows alongside yours)
- Send more personalized emails when they're outperforming you
- Create genuine scarcity and competition
**Fix direction:** Each quarter, 1 deal from the flow is "contested" — rival bids. Player can match (pays premium), use other leverage, or pass.

---

## SUMMARY — Priority Ranking

| # | Issue | Type | Impact | Effort |
|---|-------|------|--------|--------|
| 1 | LBO returns too low (~1.2× at 3yr) | Bug/Balance | CRITICAL | Medium |
| 2 | Cash trap — 69% games hit dead-end | Balance | CRITICAL | Small |
| 3 | Skill doesn't matter (random beats optimal) | Design | CRITICAL | Large |
| 4 | 24% games have zero exits | Balance | Critical | Small |
| 5 | Difficulty calibration off | Balance | High | Small |
| 6 | LP death spiral unrecoverable | Balance | High | Small |
| 7 | 57% cash undeployed all game | Balance | High | Medium |
| 8 | Strategy solved in 5 min (no depth) | Design | High | Large |
| 9 | Events are narrative dead ends | Design | Medium | Large |
| 10 | Sectors are cosmetic | Design | Medium | Large |
| 11 | No real add-on M&A mechanics | Feature | Medium | Medium |
| 12 | Globe is purely visual | Feature | Low | Medium |
| 13 | No post-game debrief | UX | Medium | Small |
| 14 | No tutorial | UX | High | Medium |
| 15 | "Next Q" has no feedback animation | UX | Medium | Small |
| 16 | Win paths don't show "locked out" state | UX | Medium | Small |
| 17 | Deal cards missing IRR | UX | Low | Tiny |
| 18 | Fund tab has no active player actions | Feature | Medium | Medium |
| 19 | Market tab doesn't drive decisions | UX | Low | Small |
| 20 | Rivals have no real gameplay impact | Feature | High | Large |

---

## RECOMMENDED FIX ORDER

### Phase 1: Make It Feel Right (balance pass, ~3 hours)
1. Fix LBO returns — adjust unrealized discount, peak modifier, debt paydown
2. Fix cash trap — ensure 2 affordable deals always in queue
3. Fix difficulty calibration — tune targets
4. Add LP satisfaction floor (20) and explicit decay messaging

### Phase 2: Make It Matter (depth pass, ~5 hours)
5. Make skill matter — reduce event variance, make growth more predictive
6. Add leverage choice (3×/4×/5×) at deal entry
7. Add hidden deal traits (quality tiers beyond hot/standard/risk)
8. Add active LP actions (call, update, co-invest)

### Phase 3: Make It Memorable (depth + polish, ~8 hours)
9. Sector-specific events and modifiers
10. Rival firms bidding on deals
11. Post-game debrief screen
12. 3-step interactive tutorial
13. Quarter advance results animation

---
*Generated by audit_sim.py — 720 automated playthroughs + code analysis*
