"""
Weights-based portfolio simulator for the 2026-10-03 pre-registered candidates.

Targets are decided on the close of a decision day and held from the next
session: the decision day's own price move is never captured (no look-ahead).
Holdings drift with prices between decisions. Costs = bps per side on traded
notional. Uninvested weight is cash at 0%.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def simulate(prices: pd.DataFrame, targets: pd.DataFrame, cost_bps: float) -> pd.Series:
    cost = cost_bps / 10_000
    targets = targets.reindex(columns=prices.columns, fill_value=0.0)
    values = pd.Series(0.0, index=prices.columns)
    cash = 1.0
    equity_path = []
    prev = None
    for day, row in prices.iterrows():
        if prev is not None:
            growth = (row / prev).replace([np.inf, -np.inf], np.nan).fillna(1.0)
            values = values * growth
        equity = cash + values.sum()
        if day in targets.index:
            wanted = equity * targets.loc[day]
            equity -= (wanted - values).abs().sum() * cost
            values = equity * targets.loc[day]
            cash = equity - values.sum()
        equity_path.append(cash + values.sum())
        prev = row
    return pd.Series(equity_path, index=prices.index)


def metrics(equity: pd.Series, periods_per_year: int) -> dict:
    returns = equity.pct_change().dropna()
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    drawdown = equity / equity.cummax() - 1
    std = returns.std()
    return {
        "start": str(equity.index[0].date()),
        "end": str(equity.index[-1].date()),
        "cagr_pct": float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) * 100 if years > 0 else 0.0,
        "sharpe": float(returns.mean() / std * np.sqrt(periods_per_year)) if std > 0 else 0.0,
        "max_drawdown_pct": float(drawdown.min() * 100),
        "total_return_pct": float(equity.iloc[-1] / equity.iloc[0] - 1) * 100,
    }


def passes(strategy: dict, benchmark: dict) -> bool:
    """Pre-registered rule: Sharpe >= benchmark AND shallower max DD, in BOTH windows."""
    return all(
        strategy[w]["sharpe"] >= benchmark[w]["sharpe"]
        and strategy[w]["max_drawdown_pct"] > benchmark[w]["max_drawdown_pct"]
        for w in ("full", "recent")
    )
