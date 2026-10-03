# Research Queue — trading-desk Sunday lab

The Sunday run of the trading-desk routine takes the **first** item whose status is `draft` or `approved`.

| Status | What the lab does |
|---|---|
| `draft` | Writes the spec questions Rayyan must answer (CLAUDE.md §3 #1) under the item. Runs **nothing**. |
| `approved` | Runs exactly the pre-registered backtest below — same parameters, windows, costs, pass rule. Writes results JSON + a dated row under the item, sets status `passed` or `failed`. One run per item, ever. |
| `passed` / `failed` / `rejected` | Skipped. A failed item is never re-run with new parameters (CLAUDE.md §7). |

Only Rayyan moves an item from `draft` to `approved` — by editing this file.

---

## Pre-registration — 2026-10-03 (written and committed BEFORE any code or result)

Approved by Rayyan in session 2026-10-02 ("yes" to testing three candidates). One run each. No parameter changes after results (CLAUDE.md §7).

**Common to all three**
- Data: yfinance daily adjusted closes (same source as every prior backtest here). Through the latest available session.
- Execution model: decide on the close of a rebalance day, hold from the next session (no look-ahead: signals use closes ≤ decision day). Positions drift with prices between rebalances.
- Costs: 10 bps per side on traded notional for ETFs, 25 bps per side for crypto.
- Metrics: CAGR, annualized Sharpe (daily, rf = 0), max drawdown, rebalances/year; also returns in 2008, 2020, 2022 (informational only).
- **PASS rule (all three):** versus the benchmark's buy-and-hold over the *same dates*, Sharpe ≥ benchmark Sharpe **and** max drawdown smaller (less negative) — in **both** the full window **and** the recent window 2022-01-01 → latest. Anything else = FAIL.

## 1. Sector momentum rotation (candidate C) — status: `failed`

- Universe: XLK, XLF, XLE, XLV, XLI (as specced in `strategy-candidates.md` §C).
- Signal: at each month's last session, rank by trailing 1-month (21-session) total return. Hold the top 2, 50% each.
- Window: 2005-01-01 → latest. Benchmark: SPY.

## 2. Dual momentum, GEM (Antonacci 2014) — status: `failed`

- Universe: SPY (US stocks), EFA (international stocks), AGG (bonds).
- Signal: at each month's last session, compute 12-month (252-session) total return of SPY, EFA and BIL (T-bills). If SPY's beats BIL's → hold the better of SPY/EFA (relative momentum); otherwise hold AGG (absolute momentum filter). 100% in one asset.
- Window: 2005-01-01 → latest (BIL starts 2007-05; before 12 months of BIL history exist, the T-bill hurdle is 0%). Benchmark: SPY.

## 3. Crypto trend — MA crossover port (candidate D) — status: `passed`

- Universe: BTC-USD, ETH-USD, 50% sleeve each.
- Signal (per coin, daily close): long when SMA(10) > SMA(50), else cash — identical parameters to ma-crossover. Evaluated every day (7 days/week).
- Window: 2018-01-01 → latest (ETH history + 50-day warm-up). Benchmark: 50/50 BTC/ETH buy-and-hold. Also report correlation of daily returns with SPY.

## Results — run once 2026-10-03 (code 6bb7f1d, `backtests/candidates/results/2026-10-02.json`)

| Candidate | Verdict | Full window: CAGR · Sharpe · MaxDD (vs benchmark) | 2022→latest: Sharpe · MaxDD (vs benchmark) |
|---|---|---|---|
| Sector momentum | **FAIL** | 11.38% vs 10.88% · 0.62 vs 0.64 · −65.3% vs −55.2% | 0.99 vs 0.74 · −23.9% vs −24.5% |
| Dual momentum | **FAIL** | 8.68% vs 10.88% · 0.61 vs 0.64 · −33.7% vs −55.2% | 0.47 vs 0.74 · −23.3% vs −24.5% |
| Crypto trend | **PASS** | 38.00% vs 19.70% · 0.94 vs 0.61 · −60.5% vs −87.9% | 0.59 vs 0.33 · −41.5% vs −69.3% |

Notes (no re-runs, no tweaks — CLAUDE.md §7):
- Sector momentum: strong since 2022 but −45.9% in 2008 vs SPY −36.2%. A 1-month look-back rotates into crashing sectors.
- Dual momentum: fails Sharpe narrowly but cuts max DD by ~40% (2008: −2.7% vs −36.2%). Any reuse as a *risk overlay* is a **new thesis** needing its own pre-registration — not a re-run of this one.
- Crypto trend: same SMA(10/50) as ma-crossover, not fitted to crypto. Correlation with SPY 0.17. **Max DD −60.5% is still huge** — sleeve size must assume a 60% drop can happen again.
