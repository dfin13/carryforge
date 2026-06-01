# CarryForge — Quick Start

## 🎮 Play Now

```bash
# Install dependencies
pip install streamlit pandas numpy plotly altair

# Run the game
streamlit run carryforge.py

# Open browser to http://localhost:8501
```

---

## ✨ What's Included (v1.0)

### **Core Features**
✅ 3 difficulty modes (Casual, Balanced, Hardcore)  
✅ Procedural deal generator (8 sectors, randomized metrics)  
✅ Realistic LBO model (EBITDA growth, debt paydown, exit multiple)  
✅ Interactive value creation levers (3 per company: growth, margin, multiple)  
✅ Live financial calculations (MOIC, IRR, equity value)  
✅ Portfolio management with exit mechanics  
✅ Fund & LP tracking (capital deployment, DPI, satisfaction)  
✅ Save/load system (SQLite with 3 save slots)  
✅ Market sentiment & macro events  
✅ Beautiful dark finance UI theme  
✅ Mobile-responsive design  

### **Gameplay Loop**
1. **Overview**: Dashboard of fund performance & portfolio
2. **Deal Flow**: Browse 6 companies per quarter, choose to invest
3. **Portfolio**: Manage value creation levers, monitor returns, exit companies
4. **Market**: View macro conditions & historical trends
5. **Fund & LPs**: Monitor LP satisfaction & fundraising readiness
6. **Advance Quarter**: Simulate time, grow portfolio, receive new deals

---

## 🎯 First Game (20–30 min)

1. Launch app → Select **Casual** difficulty
2. On **Overview**, note your $50M capital + available cash
3. Go to **Deal Flow**, review 3–4 companies
4. **Invest** in 2 companies that look good (check equity check ≤ available capital)
5. Go to **Portfolio**, adjust each company's levers (sliders)
6. Watch MOIC & IRR update in real-time
7. **Advance Quarter** 2–3 times to grow the companies
8. When MOIC > 2.0x, go back to Portfolio and **Exit** one company
9. Repeat: new deals → invest → grow → exit → fund II readiness

---

## 📊 Key Metrics Explained

| Metric | What It Means |
|--------|---------------|
| **MOIC** | "Money Multiple" — If you invest $10M and MOIC is 2.5x, you get $25M back |
| **IRR** | Annualized return percentage — 30%+ IRR is excellent in PE |
| **DPI** | How much capital has been returned to LPs so far |
| **Equity Check** | Amount of equity you pay upfront for an LBO |
| **Entry Multiple** | EBITDA multiple you're buying at (6–10x is typical) |
| **Exit Multiple** | EBITDA multiple you're selling at (8–10x is typical) |

---

## 💡 Strategy Tips

1. **Diversify sectors** — Don't buy only SaaS; vary Business Services, Manufacturing, etc.
2. **Watch multiples** — Lower entry = higher upside (buy at 6x, sell at 9x = 1.5x from multiple arbitrage alone)
3. **Manage levers** — Revenue growth + margin expansion + multiple arbitrage all contribute
4. **Hold for time** — Higher IRR requires patience; 4–7 years is typical for PE
5. **Exit winners** — Take profits when MOIC > 2.0x; don't get greedy
6. **Monitor debt** — High leverage = high risk; watch covenant safety

---

## 🔧 Customization (Code)

All core mechanics are in `carryforge.py` and easily customizable:

```python
# Change starting capital
fund = Fund(..., raised_capital=100_000_000)  # $100M instead of $50M

# Adjust sector parameters
sector_params["SaaS"] = {
    "rev_range": (100, 200),  # Higher revenue companies
    "margin_range": (0.35, 0.55),  # Higher margins
    "growth_range": (0.20, 0.40),  # Higher growth
}

# Change base exit multiple
exit_multiple = 9.5  # Instead of 8.5

# Add new sectors
SectorEnum.ENERGY = "Energy"
sector_params["Energy"] = {...}
```

---

## 📈 Phase 2 Planned (Not in v1)

- ⏳ **Rival PE firms** (compete for deals, trash-talk emails)
- ⏳ **Covenant monitoring** (leverage ratios, interest coverage)
- ⏳ **Add-on M&A** (each company can make 2–3 bolt-on acquisitions)
- ⏳ **Fundraising roadshow** (unlock Fund II with mini-game)
- ⏳ **ESG events** (compliance challenges, narrative depth)
- ⏳ **Recaps & secondary sales** (more exit options)
- ⏳ **Full performance dashboard** (waterfall charts, heatmaps)

See `CARRYFORGE_GUIDE.md` for full roadmap.

---

## 🐛 Issues / Feedback

If something breaks:
1. Clear Streamlit cache: `streamlit cache clear`
2. Restart the app: `Ctrl+C` then `streamlit run carryforge.py` again
3. Check that you're using **Streamlit 1.40+**: `pip install --upgrade streamlit`

---

## 📝 Notes for Devs

- **Database**: `.claude/carryforge.db` (SQLite) stores saves
- **Session state**: All game data lives in `st.session_state.game_state`
- **Page structure**: Simple router in `main()` — easy to convert to Streamlit Pages (multipage) later
- **Styling**: All CSS injected via `st.markdown()` with custom vars
- **No external APIs**: Fully local, no API keys needed

---

**Built with Python 3.11+ | Streamlit 1.40+ | Pandas | Numpy | Plotly**

Enjoy building your PE empire! 💼♦️
