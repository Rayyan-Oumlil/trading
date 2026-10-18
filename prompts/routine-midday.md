# Prompt — Routine Midday

Use this as the exact noon weekday midday routine prompt.

```text
You are running the noon midday routine for this workspace.

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
- Check the kill switch before any execution.
- Stay in paper mode unless files explicitly state otherwise.
- Notify only if you cut a position, materially tighten a stop, or hit a risk limit.
- If this is a remote run and you change files, commit and push them before exit.

Tasks:

1. **Pull live portfolio** (via `/trade-portfolio`):
   - Current P&L for each open position
   - Unrealized loss % (which positions are underwater?)
   - Margin utilization and liquidation distance (if leveraged)
   - Correlation matrix (are positions moving together?)

2. **Check kill-switch status**:
   - Is paper-trading/.HALT present? If yes, close all positions and stop.
   - Is memory/risk-limits.md max daily drawdown hit? If yes, close all.
   - Is any single position > 2x expected loss limit? If yes, cut it now.

3. **Apply midday rules**:
   - **Big losers:** If any position is down >3% (or per STRATEGY.md), re-run `/trade-sentiment` to confirm thesis still holds.
     - If sentiment flipped bearish (score dropped >20), cut 50% of position now.
     - If thesis intact, hold and let stop-loss handle it.
   - **Winners:** Tighten stops only if strategy rule explicitly says to (e.g., “move stop to breakeven once +2% profit”).
   - **Correlated pairs:** If two positions are both down and correlated >0.7, consider closing the smaller one to reduce systematic risk.

4. **Scan for surprise catalysts** (Perplexity or Twitter):
   - Any surprise news (guidance, acquisition, regulatory, geopolitical) since 8:30am?
   - If yes and it impacts a position thesis, update sentiment and act accordingly.

5. **Log all changes**:
   - paper-trading/log.md: [timestamp, action, ticker, new position size or exit, reason]
   - memory/portfolio-state.md: refresh with live P&L
   - journal/YYYY-MM-DD.md: brief note on midday action (or “no change”)

6. **Update memory**:
   - memory/routine-state.md (last check timestamp)
   - memory/risk-limits.md if drawdown limit is approached (alert for close routine)

Output:

- **If positions were cut/reduced:** what was closed, why (loss limit, sentiment flip, risk), new portfolio composition
- **If positions were tightened:** which, old stop → new stop, reason
- **If no change:** current P&L, margin health, rationale for holding
- **Status:** time to close? (if drawdown limit near, flag for routine-close)
```
