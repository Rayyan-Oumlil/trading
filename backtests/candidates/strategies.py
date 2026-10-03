"""Target-weight generators for the 2026-10-03 pre-registered candidates (research/queue.md)."""
from __future__ import annotations

import pandas as pd


def month_ends(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return pd.Series(index, index=index).groupby(index.to_period("M")).last().pipe(pd.DatetimeIndex)


def sector_momentum_targets(prices: pd.DataFrame, lookback: int = 21, top: int = 2) -> pd.DataFrame:
    momentum = prices.pct_change(lookback)
    rows = {}
    for day in month_ends(prices.index):
        score = momentum.loc[day].dropna()
        if len(score) < top:
            continue
        winners = score.nlargest(top).index
        rows[day] = pd.Series(0.0, index=prices.columns).where(~prices.columns.isin(winners), 1.0 / top)
    return pd.DataFrame(rows).T


def dual_momentum_targets(prices: pd.DataFrame, lookback: int = 252) -> pd.DataFrame:
    momentum = prices.pct_change(lookback)
    assets = ["SPY", "EFA", "AGG"]
    rows = {}
    for day in month_ends(prices.index):
        spy, efa = momentum.at[day, "SPY"], momentum.at[day, "EFA"]
        if pd.isna(spy) or pd.isna(efa):
            continue
        tbill = momentum.at[day, "BIL"] if "BIL" in prices and pd.notna(momentum.at[day, "BIL"]) else 0.0
        pick = ("EFA" if efa > spy else "SPY") if spy > tbill else "AGG"
        rows[day] = {a: 1.0 if a == pick else 0.0 for a in assets}
    return pd.DataFrame(rows).T[assets]


def crypto_ma_targets(prices: pd.DataFrame, fast: int = 10, slow: int = 50) -> pd.DataFrame:
    sleeve = 1.0 / prices.shape[1]
    long_ = prices.rolling(fast).mean() > prices.rolling(slow).mean()
    ready = prices.rolling(slow).mean().notna()
    weights = (long_ & ready).astype(float) * sleeve
    changed = weights.diff().abs().sum(axis=1) > 0
    changed.iloc[0] = True
    return weights[changed]  # trade only when a coin's signal flips; sleeves drift in between
