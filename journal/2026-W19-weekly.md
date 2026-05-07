---
date: 2026-05-07
week: W19 (2026-05-04 to 2026-05-07, partial — 4 trading days)
strategy: ma-crossover
---

# Weekly Review — 2026-W19

> NOTE: This routine is labeled "Friday close" but today is Thursday May 7. Week W19 data covers Mon May 4 through Thu May 7 (4 trading days, partial week). Treated as end-of-week review.

---

## 1. Weekly Scorecard

| Metric | Value |
|--------|-------|
| Portfolio weekly return | +1.77% |
| SPY weekly return | +1.74% (May 1 close $720.65 → May 7 partial $733.20) |
| QQQ weekly return | +3.36% (May 4 close $672.88 → May 7 partial $696.79) |
| Alpha vs SPY | +0.03% (essentially tracking) |
| Realized P&L this week | $0 (no trades executed — hold) |
| Unrealized P&L change | +$2,087 ($537 Mon close → $2,625 Thu current) |
| Total trades this week | 0 |
| Winners / Losers | n/a |
| Weekly Sharpe estimate | 1.58 (x sqrt(5)) — SMALL SAMPLE, 4 days, ignore statistically |

---

## 2. Daily Equity Progression

| Date | Equity | Daily Return | SPY Close |
|------|--------|-------------|-----------|
| Fri 2026-05-01 (prior week baseline) | $100,840.05 | — | $720.65 |
| Mon 2026-05-04 | $100,537.94 | -0.30% | $718.01 |
| Tue 2026-05-05 | $101,513.69 | +0.97% | $723.77 |
| Wed 2026-05-06 | $102,675.91 | +1.15% | $733.83 |
| Thu 2026-05-07 (partial, ~12:30 EDT) | $102,625.50 | -0.05% | $733.34 |

---

## 3. Benchmark Comparison

Portfolio tracks SPY closely because it IS SPY at 95% of equity:
- Portfolio: +1.77% | SPY: +1.74% | QQQ: +3.36%
- Alpha +0.03% is cash drag and rounding — not a signal.
- QQQ outperformed by ~1.6% this week, driven by mega-cap tech earnings (AAPL, META, AMZN, GOOGL all beat) + Iran deal risk-on.
- The strategy is long-only SPY trend following — it does not chase QQQ outperformance by design.

---

## 4. Backtest Reconciliation

| Metric | OOS Backtest | Paper (W19) |
|--------|-------------|-------------|
| Sharpe | 0.646 | 1.58 (4 days — meaningless) |
| Regime | Covered 2022 bear + 2023-24 bull | Sustained bull (SMA10 >SMA50 since entry Apr 23) |
| Trades | 3.02 / year | 1 open trade (~14 days) |

**Status: CANNOT RECONCILE YET.** Only 1 trade and ~14 calendar days of paper data. The Gate 2 check (`gate2_check.py`) should be run once 2 full weeks of clean daily data are logged. Target: next session (Phase B Gate 2 was re-dated to ~2026-04-23 +14 days = 2026-05-07 — so Gate 2 is NOW evaluable). Action: run gate2_check.py next manual session.

The 4-day weekly Sharpe of 1.58 is not comparable to the OOS Sharpe of 0.646. They measure different things. Do not flag as divergence.

---

## 5. Confidence Calibration Table

| Date | Decision | Confidence | Next-day SPY % | Right call? |
|------|----------|------------|---------------|-------------|
| 2026-05-07 | HOLD | 7/10 | — (tomorrow not yet known) | TBD |

Only one decision this week in the confidence log. The 2026-04-24 seed entry predates the multi-agent framework. Calibration requires at least 4 data points — run weekly review again in 2 weeks for a meaningful table.

**Prior holds vs outcomes (from equity data):**
- 2026-05-04 (Mon): SPY -0.40% → HOLD was fine (no cross, position still profitable)
- 2026-05-05 (Tue): SPY +0.80% → HOLD was correct (uptrend intact)
- 2026-05-06 (Wed): SPY +1.40% → HOLD was correct (big green day)
- 2026-05-07 (Thu, partial): SPY -0.09% → hold still correct (no cross signal)

Pattern: HOLD decisions have been correct every day this week because the bullish regime has been uninterrupted. No false positives.

---

## 6. Lessons Extracted

### What worked

1. **Rule-following over discretion.** On Monday (SPY -0.30%), there could be temptation to add a stop-trigger check. But the 5% stop wasn't hit ($677.94 is far away), and the MA was still above — so HOLD was correct. The dip reversed strongly Tue-Wed.

2. **Multi-agent synthesis.** Having technical, sentiment, and risk agents independently evaluate and then cross-check prevented any single-point failure. All three agreed this week → high confidence, no override needed.

3. **Journaling caught the stale-clone mistake.** Last session, the journal correctly stored the "outage was a phantom" correction. This week started with accurate baseline data because of that.

### What didn't / risks

1. **RSI creeping toward overbought.** RSI(14) = 74.8 today. OOS backtest exits are driven by MA cross_down only — the strategy has no RSI filter. But in practice, high RSI precedes corrections. Worth watching, not acting on.

2. **No sell signal = passive strategy.** This week was a gift (Iran deal, earnings beats). The strategy would have been equally passive during a slow grind down if no MA cross triggered. This is the nature of trend following — it does not short, it does not time tops.

3. **QQQ outperformed SPY by 1.6%.** Not a problem (we're not benchmarked to QQQ), but worth noting: if the next strategy candidate (RSI(2) mean reversion on QQQ) were live, this week would have been a strong test.

### Recurring patterns
- Every week so far: HOLD. No trades. This is normal for a MA crossover on SPY daily — the backtest averages 3 trades/year, or roughly 1 every 4 months.
- Volume on partial days is systematically low — need to not penalize confidence for low volume on intra-day routine runs.

### Biggest loss this week
None. Portfolio was up every day except slight dips Mon and Thu (partial). Re-run of 5-agent analysis not needed.

### Agent bias check
- Sentiment agent: risk_on this week. Iran deal is a legit catalyst. No obvious Friday/fear-premium bias detected.
- Technical agent: correctly detected no cross (persistent bullish trend). No miscalculation.
- Risk agent: GREEN all week. No false flags.

---

## 7. Next-Week Priorities

1. **Run Phase B Gate 2 evaluation.** Gate2 is now evaluable (`gate2_check.py --since 2026-04-23`). This is the most important task for next session — determines if paper trading matches backtest expectations.
2. **Fix ALPACA_PAPER_TRADE env var.** Add to GitHub Actions secrets.
3. **Monitor RSI.** If RSI closes above 78-80, document in journal as risk flag (still no action unless MA crosses).
4. **Strategy candidates.** Research RSI(2) Connors mean-reversion as next strategy. `research/strategy-candidates.md` already updated with VIX gate removed.
5. **Declare Phase A complete.** 3 consecutive green GHA runs needed — running count: 2/3 (need to verify tomorrow's run).

---

## 8. Open Questions for Rayyan

- Should the weekly close routine run on Thursday (as it did today) or only on Fridays? The cron should be checked.
- Gate 2: do you want to run `gate2_check.py` in the next manual session, or wait for exactly 2 calendar weeks from 2026-04-23 (i.e., until 2026-05-07)?
- RSI at 74.8: add RSI alert to pre-market routine output? (No action, just flagging.)
