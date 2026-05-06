# Strategy Candidates — Phase 5 Research Backlog

The MA crossover on SPY is in paper trading. Once 2 weeks of clean paper data exist, the next strategy enters research. This file is the backlog.

> Rule from CLAUDE.md: a new strategy needs its own `STRATEGY.md` spec, IS+OOS backtest, and 2/3 gates passing **before** it gets paper-traded.

---

## Selection criteria

A good "second strategy" is:
1. **Uncorrelated or anti-correlated with MA crossover** — diversifies regime risk. MA crossover wins in trending markets and bleeds in chop. The second strategy should ideally win in chop.
2. **Simple enough to backtest in <1 day** — no exotic data, no ML, no >3 parameters.
3. **Literature-defensible** — defaults from textbooks, not curve-fit numbers.
4. **Different timeframe or asset** — running 2 strategies on SPY daily is just doubling the same exposure.

---

## Candidates

### A. RSI(2) mean-reversion on SPY (Larry Connors)

- **Thesis:** Short-term oversold readings on SPY revert. Buy when RSI(2) < 10, exit when RSI(2) > 70 or close > 5-day MA.
- **Why it complements MA crossover:** Wins in chop / range-bound regimes where MA crossover whipsaws. Trade frequency is much higher (~30-50/year).
- **Data:** Same as MA strategy (SPY daily, 2015-2024).
- **Risks:** Famously dies in sustained bear markets. Need a regime filter (e.g., only trade longs above 200-day MA).
- **Effort:** ~4 hours to backtest. Can reuse most of `run_signal.py` infrastructure.
- **Source:** Connors, "Short Term Trading Strategies That Work" (2008). Standard literature defaults.

### B. VIX-gated SPY trend (regime filter, not a new strategy) — **REJECTED 2026-05-05**

- **Thesis:** Sit out of MA crossover when VIX > 25. High VIX = chop or panic = signal noise high.
- **Result:** Backtested with literature-default threshold 25 on the same IS (2015-2021) and OOS (2022-2024) windows. Pre-committed decision rule (Sharpe up AND drawdown down AND trades/year ≥ 3) failed on every dimension. OOS Sharpe identical to 3 decimals (0.646), max DD identical (-12.4%), trades/year dropped 3.02 → 2.68. Gate filtered only ~2 trades over 7 IS years — essentially a no-op at threshold 25, and a regression at lower returns. See `journal/2026-05-05.md` for full table.
- **Status:** Discarded. No re-tuning per CLAUDE.md §7.

### C. Sector momentum rotation (5 ETFs, 1-month look-back)

- **Thesis:** Rank XLK, XLF, XLE, XLV, XLI by 1-month return. Hold the top 2, rebalance monthly.
- **Why it complements MA crossover:** Different exposure (sector tilt, not broad market). Different bar frequency (monthly rebalance vs daily signal).
- **Data:** 5 ETFs, daily bars 2015-2024.
- **Risks:** Higher turnover, more slippage. Sector dispersion in bull markets can be small.
- **Effort:** ~6-8 hours. Needs more data wrangling.
- **Source:** Antonacci, "Dual Momentum Investing" (2014).

### D. Crypto BTC/ETH MA crossover (port of strategy 1 to a new asset)

- **Thesis:** Same logic, different asset. Tests whether the MA crossover thesis is asset-specific or general.
- **Why it complements:** Diversifies asset class. Crypto has different vol regime than equities.
- **Data:** Freqtrade already cloned. BTC/USDT daily from Binance.
- **Risks:** Crypto vol is 3-5x equity vol. May need different stop %. 24/7 markets break the "next-day open" execution model.
- **Effort:** ~8-12 hours. Most plumbing work since freqtrade is a different framework.

---

## Recommendation

~~**Do B before anything else.**~~ — Superseded 2026-05-05 (B failed empirical test).

**New recommendation:** **A (RSI(2) Connors mean-reversion on SPY)** is the natural next candidate. It targets the regime where MA crossover is weakest (chop), and the literature has well-documented defaults so no grid-search temptation. Wait until ≥ 2 weeks of clean paper data on the existing strategy before starting it — per CLAUDE.md, no new strategy gets paper-traded until 2/3 gates pass on the existing one.

---

## When to revisit this file

- After 2 weeks of paper trading the MA crossover (i.e., ~2026-05-08, depending on when paper started).
- After the weekly review routine has produced 4+ confidence calibration tables.
- If the MA crossover hits a sustained drawdown in paper and we want a hedge.

Do NOT start a second strategy because "the MA strategy is boring." Boring is the goal — the boring strategy is the one with proven gates.
