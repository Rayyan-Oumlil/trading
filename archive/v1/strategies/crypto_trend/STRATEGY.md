---
name: crypto-trend
version: 1
created: 2026-10-03
stage: paper
author: rayyan
---

# Crypto Trend — SMA(10/50) on BTC and ETH

## 1. Thesis
Crypto trends hard and crashes hard. Being long only while the 10-day average is above the 50-day keeps most of the trend and sidesteps the worst of the crashes. Same rule as ma-crossover, not fitted to crypto.

## 2. Universe
Signal: BTC-USD and ETH-USD (24/7, UTC days). Since 2026-10-04 the position is held through US spot ETFs **IBIT** and **ETHA** in the IBKR paper account (was BTC/USD, ETH/USD coins on Alpaca). Two independent 5% sleeves.

## 3. Timeframe
Daily bars, UTC days (Alpaca crypto bars close 00:00 UTC). Only completed days are used.

## 4. Entry Signal
Per coin: SMA(close, 10) > SMA(close, 50) on the last completed UTC day, and no position → buy.

## 5. Exit Rules
Per coin: SMA(10) ≤ SMA(50) → sell the full position. No stop, no time stop (as backtested).

## 6. Position Sizing
On a flat→long flip, buy **5% of account equity** (notional). No rebalancing while long; the sleeve drifts with price. Total crypto exposure at entry: 10% of equity.

## 7. Execution
Market orders, GTC, placed by `run_signal.py` after 00:00 UTC (Windows task 20:10 ET, GHA fallback 00:20 UTC). Fill immediately. Backtest assumed 25 bps per side.

## 8. Data
Live: Alpaca crypto bars. Backtest: yfinance BTC-USD / ETH-USD. Parity 2026-10-03: SMA10 within 0.2–0.3%, SMA50 within 0.5–0.6%, identical signals. Near a crossover, venue differences can shift a signal by a day.

## 9. Success Criteria (pre-registered — research/queue.md)
PASSED 2026-10-03: CAGR 38.0% vs 19.7% (50/50 hold), Sharpe 0.94 vs 0.61, MaxDD −60.5% vs −87.9%; 2022→latest Sharpe 0.59 vs 0.33, MaxDD −41.5% vs −69.3%. Correlation with SPY 0.17.

## 10. Kill Conditions
- Sleeve drawdown worse than 2× backtest max DD is impossible to detect at −60.5% before real damage, so the practical kill is **account-level**: the desk halts on its existing flags; Rayyan reviews if the crypto sleeves together lose more than 5% of account equity.
- Any fill deviating > 5% from the prior UTC close → halt and debug (crypto gaps are larger than equities').

## 11. Parameters
| Name | Value | Source |
|---|---|---|
| fast | 10 | ma-crossover (unchanged) |
| slow | 50 | ma-crossover (unchanged) |
| sleeve | 5% of equity per coin | Rayyan approved 10% total, 2026-10-03 |

## 12. Runs
| Date | Type | Result |
|---|---|---|
| 2026-10-03 | Backtest 2018-01-01→latest, pre-registered, run once | PASS (see §9). `backtests/candidates/results/2026-10-02.json` |
| 2026-10-03 | Paper start | First buys expected Sat 2026-10-03 20:10 ET run (both coins long) |

### 2026-10-04 — execution moved to ETFs (no signal change)
Parameters, signal series and weights unchanged. Execution: market-on-open in whole IBIT/ETHA shares at the US session after the signal's UTC day; weekend flips act Monday evening. Expected cost vs backtest: ETF fee 0.25%/yr plus up to ~3 days of delay after weekend flips. This paper run is the crypto-via-ETF measurement (roadmap idea 0). See plans/2026-10-04-ibkr-paper.md.
