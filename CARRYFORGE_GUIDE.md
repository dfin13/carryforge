# CarryForge — Game Guide & Development Roadmap

## 🚀 How to Run

### Prerequisites
```bash
pip install streamlit pandas numpy plotly altair
```

### Launch the Game
```bash
streamlit run carryforge.py
```

Then open your browser to `http://localhost:8501`.

---

## 🎮 Core Gameplay Loop (v1)

### 1. **Main Menu**
- Start a new game (select difficulty: Casual, Balanced, Hardcore)
- Load from up to 3 save slots
- Quick tips and mechanics overview

### 2. **Quarterly Turn Structure**

**Overview Dashboard**
- Fund performance snapshot (capital raised, deployed, available)
- Portfolio company values (real-time LBO metrics)
- Quick navigation to all game sections
- Save button (auto-saves to SQLite)

**Deal Flow**
- 6 procedurally-generated companies per quarter
- Each has randomized sector, revenue, EBITDA, growth rate, and entry multiple
- Click "Invest" to add to portfolio (deducts from available capital)
- Click "View Details" for full company profile

**Portfolio Management**
- View all owned companies with live financials
- **Value creation levers** (3 per company):
  - Revenue Growth: Boost base growth rate (+0–50%)
  - Margin Expansion: Expand EBITDA margin (+0–30%)
  - Multiple Arbitrage: Improve exit multiple (+0–30%)
- Real-time MOIC, IRR, and equity value recalculation as you adjust sliders
- Exit button: Realize returns and add to available capital

**Market & Economy**
- Market sentiment, M&A activity, interest rate trends
- Historical quarterly returns chart

**Fund & LP Relations**
- LP commitments and satisfaction tracking
- Gross DPI and Fund II readiness assessment

**Advance Quarter Button**
- Simulates 1 quarter forward
- All portfolio companies grow/contract
- Random macro events (market tailwinds, portfolio wins, etc.)
- Deal flow refreshes for next quarter

---

## 📊 Game Mechanics Explained

### **Procedural Company Generator**
Each deal in deal flow is randomly generated with:
- **Sector** (8 options: SaaS, Manufacturing, Healthcare, Retail, Business Services, FinTech, Logistics, Media)
- **Sector-specific parameters**: Revenue range, EBITDA margin range, growth rate range
- **Entry multiple**: 6–10x EBITDA (realistic LBO entry)
- **Entry debt**: 1.5–3x equity (typical leverage)

### **LBO Model (Simplified but Accurate)**

**Input:** Company metrics (revenue, EBITDA, entry cost, growth rate, levers)

**Quarterly Calculations:**
1. **EBITDA Growth**: Base growth + lever boosts
2. **Debt Paydown**: 20% of FCF (~60% of EBITDA) pays down principal each year
3. **Exit Multiple**: Base 8.5x, plus leverage from multiple arbitrage lever
4. **Enterprise Value** = Exit EBITDA × Exit Multiple
5. **Equity Value** = Enterprise Value − Net Debt
6. **MOIC** = Equity Value / Entry Equity Check
7. **IRR** = Annualized return based on MOIC and holding period

### **Value Creation Levers**

Each company has **3 independent levers** you can adjust:

| Lever | Effect | Range |
|-------|--------|-------|
| **Revenue Growth** | Multiplier on base growth rate | +0–50% |
| **Margin Expansion** | Boost EBITDA margin over time | +0–30% |
| **Multiple Arbitrage** | Improve exit multiple | +0–30% |

**How to use:** Drag sliders to see MOIC/IRR update in real-time. This teaches players about value creation sources (organic growth vs. operational improvements vs. market multiple expansion).

### **Returns Metrics**

- **MOIC** (Money Multiple of Invested Capital): Total return multiplier (e.g., 2.5x = $1 invested → $2.50 realized)
- **IRR** (Internal Rate of Return): Annualized return percentage
- **DPI** (Distributions to Paid-In): How much of invested capital has been returned to LPs
- **TVPI** (Total Value to Paid-In): DPI + unrealized gains on remaining portfolio

---

## 💾 Save/Load System

- **Auto-save**: Every quarter advance saves to SQLite
- **Manual save**: "Save Game" button on Overview (Slot 1)
- **Multiple slots**: Support for Slots 1–3 (easily extendable)
- **Persistent data**: Game state stored as JSON in database (robust to schema changes)

---

## 🎨 UI/UX Features (v1)

### **Dark Finance Theme**
- Navy/black background with emerald green accents
- Subtle radial gradients (emerald + gold)
- Card-based design with hover effects
- Responsive layout for mobile (tabs stack vertically)

### **Visual Feedback**
- Metric cards with directional indicators (↑↓)
- Color-coded text (green for positive, red for negative, gold for highlights)
- Smooth Plotly charts with dark template
- Instant updates when levers change

### **Mobile Optimization**
- `st.set_page_config(layout="wide")` allows pinch-zoom on mobile
- Large button tap targets (full-width buttons)
- Vertical card stacking on small screens
- Navigation buttons at bottom of each page

---

## 📈 Phase 2: Advanced Features (Roadmap)

### **Immediate Additions (1–2 hours each)**

1. **Add-On M&A**
   - Each portfolio company can acquire 2–3 "bolt-on" targets per year
   - Small cash payments add revenue/EBITDA
   - Teaches players about tuck-in acquisitions

2. **Rival PE Firms**
   - 2–3 AI-controlled rival funds compete for deals
   - Occasional emails with trash-talk ("We're winning the space, mate!")
   - Helps players understand competitive market dynamics

3. **Covenant Monitoring**
   - Debt covenants (leverage ratio, interest coverage)
   - Breaching covenant = forced dividend, lower flexibility
   - Adds complexity / strategy layer

4. **Fundraising Roadshow Mini-Game**
   - After Fund I shows 1.5x+ MOIC, unlock Fund II raise
   - Interactive LP pitch (choose tone: aggressive, conservative, balanced)
   - Success based on DPI, IRR, and pitch quality

5. **ESG & Compliance Events**
   - Random ESG violations in portfolio (reputational damage)
   - Compliance spend requirements
   - Adds narrative depth

### **Medium-Term (Phase 2B, 3–5 hours each)**

6. **Recapitalizations**
   - Secondary buyouts (sell majority stake to larger PE firm)
   - Partial exits with dividend recaps
   - Teaches fund economics

7. **Macro Economic Cycles**
   - 2–3 year boom/bust cycles
   - Exit multiples and growth rates tied to macro sentiment
   - Interest rates affect debt cost

8. **Performance Dashboard Upgrades**
   - Waterfall charts for each company (entry, value creation, exit)
   - Funnel chart: deal flow → investments → exits
   - Heatmap of portfolio performance over time

9. **Scenario Planning / What-If Engine**
   - Simulate different lever adjustments before committing
   - "What if I sell in 5 years vs. 7 years?"
   - Side-by-side comparisons

10. **Narrative Events & Storytelling**
    - Company-specific story (e.g., "SaaS company lands Salesforce partnership")
    - CEO changes, key departures, competitive threats
    - Events should affect metrics and create tension

### **Phase 3: Premium Features (Long-term)**

11. **Multiplayer / Leaderboard**
    - Compare your DPI/IRR with other players
    - Weekly/monthly challenges
    - Global rankings

12. **Educational Mode**
    - Detailed tooltips explaining every metric
    - "Real PE" toggle showing case studies from actual deals
    - Interactive tutorials for each mechanic

13. **Custom Game Modes**
    - "Turnaround specialist" (buy distressed companies)
    - "Tech-focused" (limited to SaaS/FinTech deals)
    - "Macro hedger" (short market cycles)

14. **PDF Export & Recap**
    - Full game recap as PDF (portfolio summary, returns, timeline)
    - "Share your results" social sharing
    - Achievement badges ("Unicorn Hunter", "Covenant Master", etc.)

---

## 🛠️ Code Architecture

### **File Structure (Single-File v1)**

```
carryforge.py
├── Imports & Config
├── Custom CSS
├── Data Models (Enums, @dataclass)
├── Database Functions (init_db, save_game, load_game)
├── Game Logic
│   ├── generate_company()
│   ├── calculate_company_value()
│   ├── generate_deal_flow()
│   ├── generate_quarterly_events()
│   └── advance_quarter()
├── UI Pages
│   ├── page_main_menu()
│   ├── page_difficulty_select()
│   ├── page_overview()
│   ├── page_deal_flow()
│   ├── page_portfolio()
│   ├── page_market()
│   └── page_fund_lps()
└── Main Router & Session State
```

### **Key Design Patterns**

1. **Session State**: All game data stored in `st.session_state.game_state`
2. **Page Router**: Simple string-based navigation (not Streamlit multipage yet)
3. **Data Classes**: Type-safe models for Fund, Company, GameState
4. **Custom CSS**: Injected via `st.markdown(..., unsafe_allow_html=True)`
5. **Procedural Generation**: `generate_company()` uses numpy + random for realism

### **Extensibility**

- Add new game mechanics: Write a function in **Game Logic** section, call from `advance_quarter()` or appropriate page
- Add new pages: Create `page_xxx()` function, add case to main router
- Add new sectors: Extend `sector_params` dict in `generate_company()`
- Add new events: Extend `event_pool` list in `generate_quarterly_events()`

---

## 🎯 Next Steps to Play

1. **Run the game:**
   ```bash
   streamlit run carryforge.py
   ```

2. **Start a new game** (Casual mode recommended for first playthrough)

3. **Core loop to try:**
   - Review overview dashboard (understand your fund metrics)
   - Browse 3–4 deals in Deal Flow
   - Invest in 2 companies that look promising
   - Go to Portfolio, adjust value creation levers for each
   - Advance 1–2 quarters and watch metrics improve
   - Exit a company when MOIC looks good
   - Repeat until you've raised Fund II or hit a game over state

4. **Win conditions:**
   - **Casual**: 1.5x MOIC by Q12 (3 years)
   - **Balanced**: 2.5x MOIC by Q12
   - **Hardcore**: 3.0x+ MOIC by Q12

---

## 🐛 Known Limitations & Fixes

| Issue | Status | Fix |
|-------|--------|-----|
| No sound effects | v1 (backlog) | Add `st-audio` with ka-ching on exit |
| No covenant math yet | v1 (backlog) | Implement leverage covenant checks |
| Limited AI rivals | v1 (backlog) | Add rival fund mechanics in Phase 2 |
| No mobile bottom nav | v1 | CSS improvements for native app feel |
| Static exit multiple | v1 | Tie exit multiple to macro sentiment |

---

## 📚 Inspiration & References

This game draws ideas from:
- **Actual PE mechanics**: Entry multiples, EBITDA growth, debt schedules, exit multiples
- **Strategy games**: Management simulation loop (Capitalism, Two Point Hospital)
- **Educational design**: Progressive complexity, instant feedback, tutorial integration
- **Streamlit examples**: Card-based layouts, Plotly dark themes, session state patterns

Code patterns adapted from:
- Streamlit official demos
- Plotly financial dashboard templates
- SQLite game save systems (roguelikes, indie games)

---

## 📞 Support

For bugs, feature requests, or gameplay questions:
1. Check the **Game Basics** section in-game (accessible from main menu)
2. Try Casual mode first to learn mechanics
3. Adjust slider values to see real-time feedback (teaching tool)

---

**Made with ♦ for PE lovers & strategy game enthusiasts.**
