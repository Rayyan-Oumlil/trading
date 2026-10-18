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

### A. RSI(2) mean-reversion on SPY (Larry Connors) — **REJECTED 2026-05-07**

- **Status:** Specced + backtested + rejected same day. See [strategies/rsi2_connors/STRATEGY.md §12](../strategies/rsi2_connors/STRATEGY.md) for full result tables and failure analysis.
- **Result summary:** IS Sharpe 0.424, OOS Sharpe 0.308 (both below the 0.5 bar). OOS trades/year 6.78 (below the 15 bar). Max DD acceptable at -6.6% OOS. Hard-stop variant strictly worse on every dimension.
- **Why it failed OOS:** the 200-DMA filter blocks entries during most of 2022 (bear market — price below 200-DMA). The 2023-24 rally was so steady that RSI(2) < 10 readings became rare. Combined: only 6.78 trades/year vs the literature-claimed 30-50.
- **What the result preserved (saved insights):**
  - Correlation with MA crossover OOS is 0.187 (genuinely diversifying — structural, applies to any future mean-reversion candidate).
  - Connors' "no hard stop" framing is empirically correct on this data.
  - Time stop at 10 bars never binds in practice — exits are signal-driven.
  - 200-DMA regime filter is too restrictive in non-uptrend years; future regime gates need rising-slope or 100-DMA variants (DIFFERENT strategy, not a tweak).
- **No re-tuning** per CLAUDE.md §7 and PRINCIPLES.md corollary. One parameter pass used.

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
~~**Do A (RSI(2) Connors).**~~ — Superseded 2026-05-07 (A failed OOS gates, see above).

**New recommendation:** **C (sector momentum rotation)** is now the lead candidate. Two reasons:
1. Different shape entirely — momentum, not mean reversion. Two failed mean-reversion-style filters (B and A) suggest the wrong frame for this regime; pivot to a different model class.
2. Different exposure (sector ETFs, monthly rebalance) reduces correlation risk with MA crossover by construction.

**Alternative: D (crypto BTC/ETH MA crossover).** Tests whether the MA crossover thesis is asset-specific or general. Higher operational cost (different framework — freqtrade), but no new strategy *concept* to validate.

**Wait condition:** before starting C or D, ma-crossover should hit a clean Gate 2 PASS. Currently SOFT-PASS at 21% relative spread; re-run target 2026-05-21.

---

## When to revisit this file

- After 2 weeks of paper trading the MA crossover (i.e., ~2026-05-08, depending on when paper started).
- After the weekly review routine has produced 4+ confidence calibration tables.
- If the MA crossover hits a sustained drawdown in paper and we want a hedge.

Do NOT start a second strategy because "the MA strategy is boring." Boring is the goal — the boring strategy is the one with proven gates.
