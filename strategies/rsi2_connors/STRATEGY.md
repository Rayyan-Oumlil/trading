---
name: rsi2-connors
version: 1
created: 2026-05-07
stage: research
author: rayyan
parent_strategy_doc: ../ma_crossover/STRATEGY.md
---

# RSI(2) Connors Mean Reversion (SPY Daily, with 200-DMA filter)

## 1. Thesis

Short-term oversold readings on SPY mean-revert in trending/sideways markets. Specifically, when the 2-day RSI drops below 10 while SPY is still in a long-term uptrend (above its 200-day MA), the dip is a buyable pullback — not a regime change. Exits when the dip is "absorbed" (RSI back above 70) or when price reclaims the short-term mean (close > 5-day MA).

This is the canonical Larry Connors short-term mean-reversion strategy. Literature defaults are used deliberately (RSI period 2, oversold threshold 10, exit threshold 70, regime filter 200-DMA) — if the thesis is right, it should work with standard parameters. **Why this is the next strategy after MA crossover:** it targets exactly the regime where MA crossover bleeds (chop / range-bound markets where the 10/50 cross whipsaws). Trade frequency ~30-50/year vs. MA's 3/year — we'll get statistical confidence faster.

## 2. Universe

- **Assets:** SPY (S&P 500 ETF)
- **Filters:** 200-day MA regime filter — only enter longs when close > SMA(200)
- **Exclusions:** Days with zero volume (data gaps); days where SMA(200) is not yet defined (first 200 bars of any dataset)

## 3. Timeframe

- **Bar:** 1d (daily close)
- **Session:** Entire trading day (signal on close, execute next-day open — no look-ahead)
- **Timezone:** UTC

## 4. Entry Signal

```
long_signal[t] = (RSI(close, 2)[t]      < 10)
             AND (close[t]              > SMA(close, 200)[t])
             AND (volume[t]             > 0)
```

Execute on **next-day open** (bar t+1). No look-ahead bias.

## 5. Exit Rules

- **Stop-loss:** None (Connors original — mean reversion needs room; the regime filter does the heavy lifting). Re-evaluate after first backtest if drawdown is unacceptable.
- **Take-profit:** None (signal-based exit only).
- **Signal exit (primary):** next-day open when RSI(close, 2) > 70.
- **Signal exit (alt):** next-day open when close > SMA(close, 5). Whichever fires first.
- **Time stop:** if neither exit fires within 10 bars, close at next-day open of bar 11. (Caps tail risk on a stuck position.)

## 6. Position Sizing

- **Method:** fixed % of equity
- **Per-trade size:** 95% of current equity (matches MA crossover for clean A/B comparison)
- **Max concurrent positions:** 1
- **Co-existence with MA crossover:** when paper-traded alongside, the two strategies share the same capital pool (95% allocation cap means at most one is in the market at a time, the other waits). This avoids 2× exposure but limits diversification benefit. Open question for backtest design — see §13.

## 7. Execution Assumptions (backtest)

- **Slippage model:** 0.05% per side (5 bps) — same as MA crossover
- **Commission:** $0 (Alpaca paper)
- **Fill model:** next-day open price
- **Short fees:** N/A (long-only)

## 8. Data

- **Source:** Alpaca free tier (daily bars via `alpaca-py`) or yfinance fallback
- **Adjusted:** yes — split + dividend-adjusted close (`auto_adjust=True`)
- **In-sample range:** 2015-01-01 to 2021-12-31 (matches MA crossover for direct comparison)
- **Out-of-sample range:** 2022-01-01 to 2024-12-31 (matches MA crossover)
- **Minimum lookback:** 200 bars before first signal can fire (for SMA(200))

## 9. Success Criteria

- **Min Sharpe (OOS):** 0.5 (same bar as MA crossover)
- **Max drawdown tolerated:** 15% (lower than MA's 25% — mean-reversion has more frequent but smaller losses, larger DD would be a red flag)
- **Min trades:** 20 per year IS, 15 per year OOS (mean reversion needs sample size)
- **Benchmark:** Buy-and-hold SPY, AND MA crossover OOS (so we can argue diversification)
- **Correlation with MA crossover OOS:** target < 0.4. If correlation is high, this is just doubling MA crossover, not diversifying.

## 10. Kill Conditions

- Live drawdown exceeds 2× backtest max drawdown → halt
- No trades for 60 days (mean-reversion should fire often) → halt and inspect (lower threshold than MA crossover's 90 days)
- Any fill price deviates >2% from signal price → halt and debug
- 5 consecutive losing trades → halt and inspect (mean-reversion regime broken)

## 11. Parameters

| Name | Value | Source | Notes |
|------|-------|--------|-------|
| rsi_period | 2 | literature (Connors 2008) | Standard, NOT tuned |
| oversold_threshold | 10 | literature | Standard, NOT tuned |
| overbought_threshold | 70 | literature | Standard, NOT tuned |
| regime_filter_period | 200 | literature | 200-DMA standard regime filter |
| short_ma_exit | 5 | literature | Connors uses 5-day MA as alt exit |
| time_stop_bars | 10 | inferred | Conservative cap on stuck positions |
| slippage_bps | 5 | estimate | Same as MA crossover |
| position_pct | 0.95 | fixed | Matches MA crossover for comparability |

## 12. Runs

| Date | Type | Run ID | Result | Link |
|------|------|--------|--------|------|
| — | (pending IS backtest) | — | — | — |
| — | (pending OOS backtest) | — | — | — |

## 13. Open Design Questions (resolve before backtest)

1. **Capital sharing model.** When run alongside MA crossover, does it share the same 95% allocation, or get its own? Two flavors:
   - **Shared pool (recommended):** 95% cap split between strategies; if MA is long, RSI(2) waits. Conservative, avoids 2× SPY exposure.
   - **Independent pools (avoid):** 95% × 2 = 190% gross — that's leverage. Reject unless explicitly desired.
2. **Should we add a hard stop?** Connors original has no stop. But a 5% hard stop (mirroring MA crossover) would let us A/B compare with a controlled risk envelope. Decision: backtest BOTH variants (with-stop and without-stop) and pick the higher OOS Sharpe.
3. **Time stop rationale.** Connors does not specify a time stop. The 10-bar cap is mine — needed for paper-trading determinism (no positions stuck for months without an exit signal). Worth removing in a sensitivity check.
4. **Regime filter sensitivity.** Test 100-DMA, 150-DMA, 200-DMA. Pick the one that filters out 2022 cleanly and use it in OOS. Resist the urge to tune further.

## 14. Notes

- **Why now:** MA crossover Gate 2 hit SOFT-PASS today (2026-05-07). Gate-2 SOFT-PASS unblocks research on the next strategy per CLAUDE.md (research can proceed; no paper trading until Gate 2 PASSES cleanly).
- **Effort estimate:** 4 hours to backtest (per `research/strategy-candidates.md`). Most of `run_signal.py` plumbing is reusable.
- **Backstop:** if the strategy fails OOS with literature defaults, the thesis is wrong, not the parameters. No re-tuning per CLAUDE.md §7.
- **Correlation matters more than absolute performance.** A Sharpe-0.5 strategy with -0.2 correlation to MA crossover is more valuable than a Sharpe-0.7 strategy with +0.7 correlation.
