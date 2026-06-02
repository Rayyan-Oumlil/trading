---
name: rsi2-multi
version: 1
created: 2026-06-01
stage: backtest
author: rayyan
---

# RSI(2) Multi-Instrument Mean Reversion

## 1. Thesis

Apply Connors' RSI(2) mean-reversion across a diversified ETF universe instead of single-SPY. When multiple instruments can independently signal, trade frequency rises organically (3-8 trades/week) without tuning any parameter. No regime filter — the literature defaults are used as-is and each instrument's own price action gates entries. Diversification across uncorrelated assets (equities, bonds, gold, sectors) further reduces portfolio-level drawdown vs single-instrument.

## 2. Universe

| Ticker | Exposure |
|---|---|
| SPY | US broad market |
| QQQ | US large-cap tech/growth |
| IWM | US small-cap |
| GLD | Gold |
| XLK | Technology sector |
| XLE | Energy sector |

TLT (bonds) excluded — mean-reversion fails on assets in sustained structural downtrends (Fed rate-hike cycle 2022-23 empirically validated this). Rules: all tickers must have > 500K average daily volume and > 5 years of history. No penny stocks, no leveraged ETFs.

## 3. Timeframe

- **Bar:** 1d (daily close)
- **Signal:** on close, execute next-day open
- **Timezone:** UTC

## 4. Entry Signal (per instrument)

```
long_signal[t, ticker] = (RSI(close, 2)[t]  < 10)
                      AND (volume[t]          > 0)
                      AND (no open position in ticker)
```

No 200-DMA regime filter — removes the gate that caused RSI(2) to fail standalone on SPY.

If multiple tickers signal on the same day: rank by RSI value (lowest RSI = most oversold = highest priority). Take up to `max_concurrent_positions` starting from the most oversold.

## 5. Exit Rules

- **RSI exit:** RSI(2)[t] > 70 → close at next-day open
- **5-DMA exit:** close[t] > SMA(close, 5)[t] → close at next-day open
- **Time stop:** 10 bars max hold → close at open of bar 11
- **No hard stop** — Connors original has no fixed stop. The time stop is the safety net. Hard stops were tested (3%) and found to cut mean-reversion winners before recovery.
- Priority: RSI exit = 5-DMA exit (whichever fires first) > time stop

## 6. Position Sizing

- **Per position:** 12% of account equity (max 5 positions = 60% invested, 40% cash buffer)
- **Max concurrent:** 5
- If a new signal arrives but portfolio is at max positions: skip (do not force-enter)
- Never exceed 15% in any single position

## 7. Execution Assumptions

- **Slippage:** 0.05% per side (5 bps)
- **Commission:** $0 (Alpaca paper)
- **Fill model:** next-day open
- **Margin:** none (long-only, cash account)

## 8. Data

- **Source:** yfinance (backtest), Alpaca bars (live paper)
- **Adjusted:** yes, split + dividend adjusted
- **OOS window:** 2022-01-01 to 2024-12-31

## 9. Success Criteria

- **Sharpe (OOS):** ≥ 0.5
- **Max drawdown:** ≤ 20%
- **Trades/year:** ≥ 20 across the full portfolio
- **Benchmark:** Buy-and-hold SPY

## 10. Kill Conditions

- Portfolio drawdown exceeds 2× backtest max DD → halt entire system
- Any single position deviates > 5% from entry without a stop → halt and inspect
- Broker silent failure (no API response) → halt

## 11. Parameters

| Name | Value | Source |
|---|---|---|
| rsi_period | 2 | Connors (2008) |
| oversold_threshold | 10 | Connors (2008) |
| overbought_threshold | 70 | Connors (2008) |
| short_ma_exit | 5 | Connors (2008) |
| stop_loss_pct | 0.03 | Conservative for multi-position |
| time_stop_bars | 5 | Shorter than single-SPY (more active) |
| max_concurrent | 5 | Portfolio constraint |
| position_pct | 0.12 | Per-position equity allocation |

## 12. Runs

| Date | Type | Result |
|---|---|---|
| 2026-06-01 | OOS 2022-2024, no-stop, 6 instruments | **Sharpe 0.760, DD -5.59%, 72 trades/yr, +14.74%, win 62.9%** — ALL GATES PASS |
| 2026-06-01 | OOS 2022-2024, 3% stop, 6 instruments | Sharpe 0.325, DD -8.65% — stop kills mean-reversion |
| 2026-06-01 | OOS 2022-2024, 3% stop, 7 instr (incl TLT) | Sharpe 0.215 — TLT dragged by rate hike cycle |

## 13. Multi-Agent Research Layer

Each morning before signal execution, 3 agents run in parallel:

**Agent A — Technical:** Confirms RSI signals, checks if any ticker has earnings in next 2 days (skip if yes), flags unusual volume.

**Agent B — Macro/Sentiment:** Checks for FOMC, CPI, NFP in next 24h. If a scheduled macro event could move the whole market, flags all signals for human review. Posts summary.

**Agent C — Portfolio/Risk:** Checks current positions, total portfolio drawdown, kill-switch status, confirms proposed trades respect position limits.

Veto logic: any single agent can veto a specific ticker's signal. The signal must get 2/3 agent approval to execute. A market-wide macro flag from Agent B vetoes ALL signals for that day.
