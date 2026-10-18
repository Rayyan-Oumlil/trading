# Prompt — Routine Weekly Review

Use this as the exact Friday 4pm weekly review routine prompt.

```text
You are running the Friday 4:00pm weekly review routine for this workspace.

Before doing anything else:

1. Read all routine memory files first:
   - memory/operating-manual.md
   - memory/risk-limits.md
   - memory/routine-state.md
   - memory/portfolio-state.md
   - memory/watchlist.md
2. Read the week’s relevant journal entries.
3. Read any active strategy specs touched this week.

Rules:

- Get all API keys from environment variables, not from `.env` files.
- Stay factual. Grade the week honestly.
- If this is a remote run and you change files, commit and push them before exit.

Tasks:

1. **Gather the week's data**:
   - Read all daily journal entries from Mon-Fri (or Mon-Thu if no Fri trades)
   - Calculate weekly realized P&L (sum of all daily closes)
   - Count: total trades, winners, losers, big wins (>+2%), big losses (>-2%)

2. **Benchmark performance**:
   - Portfolio weekly return (realized + unrealized as of close Friday)
   - SPY weekly return (via TradingView or Perplexity)
   - QQQ weekly return (for tech exposure context)
   - Weekly Sharpe estimate: (avg daily return) / (daily std dev) * sqrt(5)
   - Compare backtest Sharpe vs paper Sharpe (should be within 10%)

3. **Reconcile backtest vs reality**:
   - Read STRATEGY.md expected Sharpe
   - If paper Sharpe diverged >10% from backtest:
     - Check for data quality issues (slippage, commissions, gaps)
     - Check for parameter drift (did I tweak entry/exit rules?)
     - Check for correlation changes (was market regime different than backtest assumed?)
   - If reconciliation fails, flag for strategy review (don't keep trading)

4. **Extract lessons**:
   - What trades worked? (Identify 2-3 patterns that won)
   - What trades failed? (Identify 2-3 patterns that lost)
   - Recurring mistakes: overtrading? Revenge trading? Missed signals?
   - What improved from last week?
   - What degraded?

5. **5-agent feedback loop**:
   - For your 3-5 biggest losses this week, re-run the 5-agent analysis (technical + sentiment + fundamentals + risk + thesis)
   - Compare agents' scores at entry vs what actually happened
   - Did sentiment flip overnight? Did technicals matter less than fundamentals? Update operating assumptions.

6. **Update files**:
   - memory/routine-state.md: add "weekly review complete" timestamp
   - memory/portfolio-state.md: refresh current open positions
   - journal/YYYY-MM-DD-week.md: full weekly entry with scorecard, lessons, next-week plan
   - STRATEGY.md (if needed): only if evidence supports a documented change (not tweaking)

7. **Notify** (if Telegram):
   - Weekly scorecard: P&L, Sharpe, win rate, benchmark comparison
   - Key lesson (1 sentence)

8. **If remote: commit and push** all changes to GitHub

Output:

- **Weekly scorecard:** total P&L, win %, avg trade, largest win/loss, Sharpe estimate
- **Benchmark comparison:** portfolio % vs SPY % vs QQQ %
- **Backtest reconciliation:** "Paper Sharpe matches backtest" or "DIVERGED >10%, needs investigation"
- **Top 3 lessons learned** from the week
- **5-agent feedback:** any systematic bias discovered in technicals/sentiment/fundamentals?
- **Next-week priorities:** what to focus on Monday morning
- **Any strategy changes?** (rarely; must be evidence-based)
```
