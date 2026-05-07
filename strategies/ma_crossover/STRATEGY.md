---
name: ma-crossover
version: 1
created: 2026-04-22
stage: backtest
author: rayyan
---

# MA Crossover (SPY Daily)

## 1. Thesis

The 10/50 SMA crossover is a simple trend-following filter on SPY. When the fast MA crosses above the slow MA, the dominant trend has recently shifted upward — the strategy rides that trend until the opposite cross. The edge is not prediction; it is trend participation with a hard stop to limit drawdowns in false breakouts. Literature defaults (10/50) are used deliberately — if the thesis is right, it should work with standard parameters, not tuned ones.

## 2. Universe

- **Assets:** SPY (S&amp;P 500 ETF)
- **Filters:** None — single instrument
- **Exclusions:** No trading on days with zero volume (data gaps)

## 3. Timeframe

- **Bar:** 1d (daily close)
- **Session:** Entire trading day (signal on close, execute next-day open — no look-ahead)
- **Timezone:** UTC

## 4. Entry Signal

```
long_signal[t] = (SMA(close, 10)[t]     > SMA(close, 50)[t])
             AND (SMA(close, 10)[t-1]   <= SMA(close, 50)[t-1])
             AND (volume[t]             > 0)
```

Execute on **next-day open** (bar t+1). No look-ahead bias.

## 5. Exit Rules

- **Stop-loss:** 5% from entry fill price (fixed %)
- **Take-profit:** None
- **Signal exit:** next-day open when fast_sma crosses below slow_sma
- **Priority:** If stop-loss and signal exit trigger same bar, stop-loss takes precedence

## 6. Position Sizing

- **Method:** fixed % of equity
- **Per-trade size:** 95% of current equity (fully invested or flat — single instrument)
- **Max concurrent positions:** 1

## 7. Execution Assumptions (backtest)

- **Slippage model:** 0.05% per side (5 bps)
- **Commission:** $0 (Alpaca paper has no commissions on equities)
- **Fill model:** next-day open price
- **Short fees:** N/A (long-only)

## 8. Data

- **Source:** Alpaca free tier (daily bars via `alpaca-py`) or yfinance fallback during dev
- **Adjusted:** yes — split + dividend-adjusted close (`auto_adjust=True`)
- **In-sample range:** 2015-01-01 to 2021-12-31 (7 years, covers 2015-19 bull + 2020 COVID crash)
- **Out-of-sample range:** 2022-01-01 to 2024-12-31 (covers 2022 bear + 2023-24 bull)

## 9. Success Criteria

- **Min Sharpe (OOS):** 0.5 (beats random, not spectacular)
- **Max drawdown tolerated:** 25%
- **Min trades:** 5 per year (enough to estimate statistics)
- **Benchmark:** Buy-and-hold SPY (same period)

## 10. Kill Conditions

- Live drawdown exceeds 2× backtest max drawdown → halt
- No trades for 90 days (strategy stuck) → halt and inspect
- Any fill price deviates >2% from signal price → halt and debug

## 10.5 Watch Flags (non-actionable, journal only)

These do NOT trigger automated actions. They are flags the routine surfaces in the journal so I can review whether the regime is changing under the strategy.

- **RSI(14) > 78 on signal bar:** log warning in journal entry — overbought, MA crossover historically continues but draw-downs shorten on the next reversal.
- **RSI(14) > 85 on signal bar:** log warning AND require a one-sentence justification for continuing to hold in the daily journal entry. Still no automated SELL — the only exit rules are §5.
- **Volume < 0.7× 20-day avg on signal bar:** log warning — thin tape, signals are noisier. Caveat: ignore if the routine ran intraday and pulled a partial bar.

These are observational. The strategy spec is unchanged: exits are ONLY §5 (stop-loss, signal exit). Adding RSI as an exit rule would be a parameter change requiring a new STRATEGY.md version and re-backtest — not a watch flag.

## 11. Parameters

| Name | Value | Source | Notes |
|------|-------|--------|-------|
| fast_period | 10 | literature | Standard fast MA, NOT tuned |
| slow_period | 50 | literature | Standard slow MA, NOT tuned |
| stop_pct | 0.05 | fixed | Hard rule, not tuned |
| slippage_bps | 5 | estimate | Conservative for SPY daily |
| position_pct | 0.95 | fixed | 5% cash buffer |

## 12. Runs

| Date | Type | Run ID | Result | Link |
|------|------|--------|--------|------|
| 2026-04-23 | backtest IS (2015-2021) | 20260423_193804_in_sample | Sharpe 0.822, DD -15.0%, 22 trades, 72% return | [results](../../backtests/ma_crossover/results/) |
| 2026-04-23 | backtest OOS (2022-2024) | 20260423_193805_out_of_sample | Sharpe 0.646, DD -12.4%, 9 trades, 21% return | [results](../../backtests/ma_crossover/results/) |
| 2026-05-07 | Gate 2 paper review (carry-in) | 2026-04-23→2026-05-07 | SOFT-PASS — actual +2.69% vs expected +3.40% (21% rel spread, 0 fills, 14 days) | [review](../../journal/2026-05-07_gate2_review.md) |

## 13. Notes

Starting with literature defaults (10/50) so this is not a tuned strategy. If it fails OOS with default parameters, the thesis is wrong, not the parameters. No re-tuning allowed unless the thesis changes (per PRINCIPLES.md corollary rule).
