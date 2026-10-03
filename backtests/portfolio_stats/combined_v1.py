"""
Descriptive stats of the LIVE portfolio v1 (SPY trend 85.5% + BTC 5% + ETH 5%), 2018 → latest.
Not a strategy test: no parameter is chosen here. Feeds plans/2026-10-03-roadmap-to-live.md.
Usage: python -m backtests.portfolio_stats.combined_v1
"""
from __future__ import annotations

import json
import math
import subprocess
from datetime import date
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
import yfinance as yf

from backtests.candidates.engine import simulate
from backtests.candidates.strategies import crypto_ma_targets

START = "2018-01-01"
WEIGHTS = {"SPY": 0.855, "BTC-USD": 0.05, "ETH-USD": 0.05}
COST_BPS = {"SPY": 5, "BTC-USD": 25, "ETH-USD": 25}
RESULTS = Path(__file__).resolve().parent / "results"


def closes(tickers: list[str], start: str) -> pd.DataFrame:
    return yf.download(tickers, start=start, auto_adjust=True, progress=False)["Close"][tickers].dropna(how="all")


def sleeve(prices: pd.DataFrame, cost_bps: float) -> pd.Series:
    """Long/flat SMA(10/50), trading only on flips — the live rule."""
    targets = crypto_ma_targets(prices) * prices.shape[1]
    return simulate(prices.loc[START:], targets.loc[START:], cost_bps)


def stats(eq: pd.Series, ppy: int = 365) -> dict:
    r = eq.pct_change().dropna()
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    return {
        "cagr": (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1,
        "vol": r.std() * math.sqrt(ppy),
        "sharpe": r.mean() / r.std() * math.sqrt(ppy),
        "max_drawdown": (eq / eq.cummax() - 1).min(),
    }


def min_track_record_years(r: pd.Series, conf: float = 0.95, ppy: int = 365) -> float:
    """Bailey & López de Prado (2012): periods needed to be `conf` sure the Sharpe is > 0."""
    sr = r.mean() / r.std()
    g3, g4 = r.skew(), r.kurt() + 3  # pandas kurt() is excess kurtosis
    n = 1 + (1 - g3 * sr + (g4 - 1) / 4 * sr**2) * (NormalDist().inv_cdf(conf) / sr) ** 2
    return n / ppy


def main() -> int:
    spy = closes(["SPY"], "2017-06-01")
    crypto = closes(["BTC-USD", "ETH-USD"], "2017-09-01")
    sleeves = {"SPY": sleeve(spy[["SPY"]], COST_BPS["SPY"])}
    sleeves |= {c: sleeve(crypto[[c]], COST_BPS[c]) for c in ("BTC-USD", "ETH-USD")}

    cal = pd.date_range(START, crypto.index[-1], freq="D")
    on_cal = lambda s: s.reindex(cal).ffill().bfill()  # noqa: E731 — SPY sleeve flat on weekends
    portfolio = sum(WEIGHTS[k] * on_cal(v) for k, v in sleeves.items()) + (1 - sum(WEIGHTS.values()))
    bench = on_cal(spy["SPY"].loc[START:])
    bench = bench / bench.iloc[0]

    rp, rb = portfolio.pct_change().dropna(), bench.pct_change().dropna()
    excess = rp - rb
    rel_3m = (portfolio / portfolio.shift(91) - bench / bench.shift(91)).dropna()
    worst_3m = portfolio.rolling(91).apply(lambda w: (w / np.maximum.accumulate(w) - 1).min()).dropna()
    years = (cal[-1] - cal[0]).days / 365.25
    flips = {c: (crypto_ma_targets(crypto[[c]]).loc[START:].diff().abs().sum(axis=1) > 0).sum() / years
             for c in ("BTC-USD", "ETH-USD")}

    out = {
        "run_date": str(date.today()),
        "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "window": [str(cal[0].date()), str(cal[-1].date())],
        "portfolio_v1": {**stats(portfolio), "min_track_record_years_sharpe_gt_0": min_track_record_years(rp)},
        "spy_buy_hold": stats(bench),
        "spy_trend_sleeve_alone": stats(on_cal(sleeves["SPY"])),
        "excess_vs_spy": {"information_ratio": excess.mean() / excess.std() * math.sqrt(365)},
        "rolling_3m_return_minus_spy": {"p05": rel_3m.quantile(0.05), "median": rel_3m.median()},
        "rolling_3m_worst_drawdown": {"p05": worst_3m.quantile(0.05)},
        "crypto_flips_per_year": flips,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{date.today()}.json"
    path.write_text(json.dumps(out, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, default=lambda x: round(float(x), 4)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
