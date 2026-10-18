---
name: <strategy-name>
version: 1
created: YYYY-MM-DD
stage: research  # research | backtest | paper | live | archived
author: rayyan
---

# <Strategy Name>

## 1. Thesis

One paragraph. Why does this strategy have an edge? Answer as if to a skeptical quant — don't wave your hands.

## 2. Universe

- **Assets:** (e.g., SPX 500 constituents, top-20 crypto by volume)
- **Filters:** (min avg volume, price > $5, exclude biotech, etc.)
- **Exclusions:** (earnings within 3 days? halts? recent IPOs?)

## 3. Timeframe

- **Bar:** 1m / 5m / 1h / 1d
- **Session:** RTH only? 24/7? 0900-1500 UTC?
- **Timezone:** UTC (default) — note deviations

## 4. Entry Signal

Exact formula. If a human can't recompute this by hand from the spec, the spec is wrong.

```
Example:
  long_signal = (close > SMA(close, 200)) AND (RSI(14) < 30) AND (volume > SMA(volume, 20) * 1.5)
```

## 5. Exit Rules

- **Stop-loss:** (fixed %, ATR-based, time-stop, signal reversal)
- **Take-profit:** (fixed %, ATR-based, trailing, none)
- **Time-stop:** (exit after N bars if neither SL nor TP hit)
- **Regime exit:** (flatten if VIX > X, or if drawdown exceeds Y)

## 6. Position Sizing

- **Method:** fixed $ / fixed % / vol-scaled / Kelly-fraction
- **Per-trade size:** (e.g., 1% of equity, or $N notional)
- **Max concurrent positions:** N
- **Max sector / correlation exposure:** N

## 7. Execution Assumptions (backtest)

- **Slippage model:** (basis points, % of spread, fixed)
- **Commission:** (per-share, per-trade, exchange fees)
- **Fill model:** (next bar open, VWAP, mid-at-signal)
- **Short fees:** (if applicable)

## 8. Data

- **Source:** (Alpaca / Yahoo / Polygon / Binance)
- **Adjusted?** dividend + split adjusted: yes/no
- **Range used for in-sample:** YYYY-MM-DD to YYYY-MM-DD
- **Range reserved for out-of-sample:** YYYY-MM-DD to YYYY-MM-DD

## 9. Success Criteria

- **Min Sharpe (OOS):** X
- **Max drawdown tolerated:** Y%
- **Min trades/year:** N (low trade count = high variance estimate)
- **Benchmark:** (buy-hold SPY, or BTC, or equal-weight universe)

## 10. Kill Conditions

- Live drawdown exceeds X% of backtest max drawdown -> halt.
- Win rate drifts more than Y% below backtest -> halt.
- Any trade execution diverges from spec -> halt and debug.

## 11. Parameters

All tunables in one table. Every change below requires a new entry in `notes.md` with a reason.

| Name | Value | Source | Notes |
|------|-------|--------|-------|
| sma_fast | 10 | tuned | via grid search on 2020-2022 |
| sma_slow | 50 | tuned | " |
| stop_pct | 5 | fixed | hard rule, not tuned |

## 12. Runs

| Date | Type | Run ID | Result | Link |
|------|------|--------|--------|------|
| ... | backtest/paper/live | ... | ... | [../../backtests/...](../../backtests/) |

## 13. Notes

Open questions. Rejected alternatives. Anything future-me needs to know.
