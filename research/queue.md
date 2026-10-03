# Research Queue — trading-desk Sunday lab

The Sunday run of the trading-desk routine takes the **first** item whose status is `draft` or `approved`.

| Status | What the lab does |
|---|---|
| `draft` | Writes the spec questions Rayyan must answer (CLAUDE.md §3 #1) under the item. Runs **nothing**. |
| `approved` | Runs exactly the pre-registered backtest below — same parameters, windows, costs, pass rule. Writes results JSON + a dated row under the item, sets status `passed` or `failed`. One run per item, ever. |
| `passed` / `failed` / `rejected` | Skipped. A failed item is never re-run with new parameters (CLAUDE.md §7). |

Only Rayyan moves an item from `draft` to `approved` — by editing this file.

---

## 1. Sector / dual momentum rotation — status: `draft`

- **Source:** `research/strategy-candidates.md` §C.
- **Thesis (one line):** Relative strength among broad ETFs persists for months; rotating monthly into the strongest, with an absolute-momentum cash filter, beats buy-and-hold SPY on a risk-adjusted basis across regimes.
- **Must answer before approval:** universe (sector ETFs vs SPY/EFA/AGG), lookback (12-1 vs 6 vs 1 month), holdings count, rebalance day, cash proxy, costs/slippage, IS/OOS windows (must include 2008, 2020, 2022), and the pre-registered pass rule (proposed: OOS Sharpe ≥ SPY's AND max DD ≤ SPY's over the same window).
- **Lab questions:** (written by the lab on its first Sunday)
