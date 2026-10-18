# Prompt — Routine Close

Use this as the exact 3pm weekday close routine prompt.

```text
You are running the 3:00pm close routine for this workspace.

Before doing anything else:

1. Read all routine memory files first:
   - memory/operating-manual.md
   - memory/risk-limits.md
   - memory/routine-state.md
   - memory/portfolio-state.md
   - memory/watchlist.md
2. Read today’s journal entry if it exists.

Rules:

- Get all API keys from environment variables, not from `.env` files.
- Stay in paper mode unless files explicitly state otherwise.
- Send an end-of-day summary after the files are updated, not before.
- If this is a remote run and you change files, commit and push them before exit.

Tasks:

1. **Refresh live account state** (via `/trade-portfolio`):
   - Closed trades (realized P&L)
   - Open positions (unrealized P&L)
   - Total daily P&L
   - Margin utilization at close
   - Any failed orders or partial fills?

2. **Close of day housekeeping**:
   - Confirm all pending orders are still valid (or cancel if not).
   - Check for any overnight gaps on extended-hours trades (crypto).
   - Verify next-day stops/targets are correctly set.

3. **Write EOD state** back to memory files:
   - memory/portfolio-state.md: 
     - All open positions [ticker, entry, size, current P&L, stop, target]
     - Daily realized P&L
     - Buying power remaining
   - memory/routine-state.md: last close time, next premarket time
   - paper-trading/log.md: append every trade (open/close) with [entry, exit, P&L, reason]
   - journal/YYYY-MM-DD.md: end-of-day entry with day’s summary

4. **Calculate daily metrics**:
   - Win rate today (if closed trades)
   - R-multiple average (realized P&L / avg risk per trade)
   - Largest win, largest loss
   - Correlation with SPY (if equities)

5. **Send EOD notification** (if Telegram configured):
   - Concise summary: daily P&L, open positions, margin health, key trades
   - Avoid spam: only if P&L is material or a trade was cut

6. **If remote: commit and push** all changed files to GitHub

Output:

- **Daily scorecard:** total P&L, win/loss count, avg R-multiple, largest win/loss
- **Open position summary:** [ticker, entry, size, unrealized P&L %, stop, target]
- **Next-day action:** any gaps, overnight catalysts, premarket plan
- **Journal entry committed**
```
