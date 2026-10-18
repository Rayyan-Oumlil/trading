# Prompt — Routine Premarket

Use this as the exact 6am weekday pre-market routine prompt.

```text
You are running the 6:00am pre-market routine for this workspace.

Before doing anything else:

1. Read all routine memory files first:
   - memory/operating-manual.md
   - memory/risk-limits.md
   - memory/routine-state.md
   - memory/portfolio-state.md
   - memory/watchlist.md
2. Read the latest relevant journal entry.
3. If any active strategy is involved, read its STRATEGY.md before acting.

Rules:

- Use Perplexity for research if `PERPLEXITY_API_KEY` is available.
- Get all API keys from environment variables, not from `.env` files.
- Stay in paper mode unless files explicitly state otherwise.
- Do not notify unless something is urgent.
- If this is a remote run and you change files, commit and push them before exit.

Tasks:

1. **Market context** (Perplexity or web search):
   - Overnight moves: Asia close, Europe open
   - Pre-market futures (ES, NQ, BTC, ETH)
   - Implied open for SPY, QQQ
   - VIX, yields, major currency pairs
   - Any overnight news or catalyst

2. **Watchlist research** (5-agent parallel for top 3):
   - For each ticker in memory/watchlist.md top 3:
     - Run `/trade-technicals` (regime, key levels, momentum)
     - Run `/trade-sentiment` (news, social, catalysts)
     - Synthesize: is this a setup today?
   - Note: fundamentals rarely change intraday; use `/trade-fundamentals` only if earnings-related

3. **Benchmark context**:
   - SPY: support/resistance, trend, correlation to macro
   - QQQ: tech-heavy regime, earnings calendar, concentration risk
   - BTC: if crypto in watchlist, funding rates and flows
   - VIX: complacency or panic? Adjust aggressiveness

4. **Event calendar**:
   - Earnings premarket/postmarket today?
   - Economic data (CPI, jobs, Fed speak)?
   - Options expiry or volatility events?

5. **Finalize brief**:
   - Draft trade ideas ONLY if: (a) specific entry+stop+target, (b) risk-bounded per memory/risk-limits.md, (c) aligned with active strategy rules
   - If nothing qualifies, output “no action today”
   - Log the decision to today’s journal

6. **Update memory**:
   - memory/watchlist.md (new scores if /trade-* was run)
   - memory/routine-state.md (last run timestamp, context summary)
   - memory/portfolio-state.md (no change unless positions moved overnight)
   - journal/YYYY-MM-DD.md (premarket entry)

Output:

- **Briefing header:** Market regime (trending/ranging), key indices, VIX level, sentiment (bullish/neutral/bearish)
- **Watchlist candidates:** Up to 3 tickers with entry zone, stop, target, R-multiple
- **Action plan:** Explicit trades to consider at open, or “no action” with reason
- **Risk check:** Verify correlation, position size, margin health before any open
```
