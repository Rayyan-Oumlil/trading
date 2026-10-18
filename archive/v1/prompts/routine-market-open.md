# Prompt — Routine Market Open

Use this as the exact 8:30am weekday market-open routine prompt.

```text
You are running the 8:30am market-open routine for this workspace.

Before doing anything else:

1. Read all routine memory files first:
   - memory/operating-manual.md
   - memory/risk-limits.md
   - memory/routine-state.md
   - memory/portfolio-state.md
   - memory/watchlist.md
2. Read the latest relevant journal entry.
3. Read the relevant strategy spec for any planned trade.

Rules:

- Get all API keys from environment variables, not from `.env` files.
- Check for paper-trading/.HALT before any execution.
- Stay in paper mode unless files explicitly state otherwise.
- Notify only if a trade is actually placed or a serious failure occurs.
- If this is a remote run and you change files, commit and push them before exit.

Tasks:

1. **Market open snapshot** (via TradingView MCP or Perplexity):
   - ES, NQ, SPY, QQQ opening prices vs premarket levels
   - Overnight volatility vs expected
   - Any gaps or reversals from premarket brief

2. **Refresh account state**:
   - Call `/trade-portfolio` to pull live positions, P&L, margin health
   - Check for any overnight fills or corporate actions
   - Verify correlation matrix (any high-correlated positions?)

3. **Execute planned trades** (if any from premarket):
   - Re-check each vs current /trade-sentiment (did overnight news change conviction?)
   - Re-check vs memory/risk-limits.md (margin, max drawdown, position size)
   - If all checks pass: use `/trade-open {TICKER} {SIDE} {SIZE} {LEVERAGE} {ENTRY} {STOP} {TAKE_PROFIT}`
   - If checks fail: update journal with reason + skip

4. **Set stops and targets**:
   - Use the entry from the 5-agent research (technical key levels, risk-reward ratio)
   - If strategy uses trailing stops, set via exchange API
   - Log stop/target prices to memory/portfolio-state.md

5. **Log execution**:
   - Every order (filled or pending) → paper-trading/log.md with [timestamp, ticker, side, size, entry, stop, target]
   - Journal entry: brief note on what was opened + reasoning

6. **Update memory**:
   - memory/portfolio-state.md (refresh with live fills)
   - memory/routine-state.md (last execution timestamp)
   - journal/YYYY-MM-DD.md (execution log)

Output:

- **If trade placed:** ticker, size, entry, stop, target, risk-reward ratio
- **If no trade:** reason (failed risk check, sentiment shift, no setup qualified)
- **Status:** current open positions, margin utilization, next routine checkpoint (midday or close)
```
