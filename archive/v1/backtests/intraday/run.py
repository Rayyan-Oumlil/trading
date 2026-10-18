"""
Pre-registered intraday backtests — research/queue.md items 4, 5, 6 (2026-10-04).
One run. Rules, costs, windows and the PASS rule come from the pre-registration; do not tune.

Usage: python -m backtests.intraday.run
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backtests.intraday.data import by_day, load  # noqa: E402

COSTS = {"paper": 0.0035 + 0.001, "realistic": 0.005 + 0.005}  # $ per share per side
WINDOWS = {
    "in_sample": ("2016-01-01", "2022-12-31"),
    "out_of_sample": ("2023-01-01", None),
    "post_publication": ("2024-05-01", None),
    "full": ("2016-01-01", None),
}
START_EQUITY = 100_000.0
LOOKBACK = 14
CHECKS = list(range(29, 360, 30))  # bar indices ending at 10:00, 10:30, …, 15:30
LAST = 389  # bar 15:59 → its close is the 16:00 price


class Days:
    def __init__(self, symbol: str) -> None:
        frames = by_day(load(symbol))
        self.dates = list(frames)
        stack = lambda col: np.stack([frames[d][col].to_numpy() for d in self.dates])  # noqa: E731
        self.o, self.h, self.l, self.c, self.v = (stack(k) for k in ("open", "high", "low", "close", "volume"))
        tp = (self.h + self.l + self.c) / 3
        with np.errstate(invalid="ignore", divide="ignore"):
            self.vwap = np.cumsum(tp * self.v, axis=1) / np.cumsum(self.v, axis=1)
        self.vwap = pd.DataFrame(self.vwap).T.ffill().bfill().T.to_numpy()  # minutes before the first trade
        self.close = self.c[:, LAST]


def _trade_pnl(side: int, shares: int, entry: float, exit_: float, cost: float) -> float:
    return side * shares * (exit_ - entry) - 2 * cost * shares


def noise_area(d: Days, cost: float, max_lev: float) -> tuple[list[float], int, list[float]]:
    """Returns (daily returns aligned with d.dates, number of round trips, per-trade returns)."""
    opens = d.o[:, 0]
    move = np.abs(d.c / opens[:, None] - 1)
    daily_ret = np.r_[np.nan, d.close[1:] / d.close[:-1] - 1]
    equity, rets, trades = START_EQUITY, [], []
    for i in range(len(d.dates)):
        if i <= LOOKBACK:
            rets.append(0.0)
            continue
        sigma = move[i - LOOKBACK:i].mean(axis=0)
        ub = max(opens[i], d.close[i - 1]) * (1 + sigma)
        lb = min(opens[i], d.close[i - 1]) * (1 - sigma)
        vol = np.std(daily_ret[i - LOOKBACK:i], ddof=1)
        size = min(max_lev, 0.02 / vol) if vol > 0 else max_lev
        shares = math.floor(equity * size / opens[i])
        pnl, side, entry = 0.0, 0, 0.0

        def close_out(price: float) -> None:
            nonlocal pnl, side
            p = _trade_pnl(side, shares, entry, price, cost)
            pnl += p
            trades.append(p / (shares * entry) if shares else 0.0)
            side = 0

        for m in CHECKS:
            price = d.c[i, m]
            if side == 1 and price < max(ub[m], d.vwap[i, m]):
                close_out(price)
            elif side == -1 and price > min(lb[m], d.vwap[i, m]):
                close_out(price)
            if side == 0 and shares > 0:
                if price > ub[m]:
                    side, entry = 1, price
                elif price < lb[m]:
                    side, entry = -1, price
        if side:
            close_out(d.close[i])
        rets.append(pnl / equity)
        equity += pnl
    return rets, len(trades), trades


def last_half_hour(d: Days, cost: float) -> tuple[list[float], int, list[float]]:
    equity, rets, trades = START_EQUITY, [0.0], []
    for i in range(1, len(d.dates)):
        r1 = d.c[i, 29] / d.close[i - 1] - 1
        side = 1 if r1 > 0 else -1 if r1 < 0 else 0
        entry = d.c[i, 359]
        shares = math.floor(equity / entry)
        pnl = _trade_pnl(side, shares, entry, d.close[i], cost) if side else 0.0
        if side:
            trades.append(pnl / (shares * entry))
        rets.append(pnl / equity)
        equity += pnl
    return rets, len(trades), trades


def opening_range(d: Days, cost: float) -> tuple[list[float], int, list[float]]:
    equity, rets, trades = START_EQUITY, [], []
    for i in range(len(d.dates)):
        o, c = d.o[i, 0], d.c[i, 4]
        entry = d.o[i, 5]
        side = 1 if c > o else -1 if c < o else 0
        stop = d.l[i, :5].min() if side == 1 else d.h[i, :5].max()
        risk = (entry - stop) * side
        if side == 0 or risk <= 0:
            rets.append(0.0)
            continue
        target = entry + side * 10 * risk
        exit_ = d.close[i]
        for m in range(5, LAST + 1):
            hit_stop = d.l[i, m] <= stop if side == 1 else d.h[i, m] >= stop
            if hit_stop:  # gap through the stop fills at the bar's open
                exit_ = min(stop, d.o[i, m]) if side == 1 else max(stop, d.o[i, m])
                break
            if (d.h[i, m] >= target) if side == 1 else (d.l[i, m] <= target):
                exit_ = target
                break
        shares = math.floor(equity / entry)
        pnl = _trade_pnl(side, shares, entry, exit_, cost)
        trades.append(pnl / (shares * entry))
        rets.append(pnl / equity)
        equity += pnl
    return rets, len(trades), trades


def stats(rets: pd.Series, n_trades: float | None = None, years: float | None = None) -> dict:
    eq = (1 + rets).cumprod()
    years = years or len(rets) / 252
    sd = rets.std()
    out = {
        "cagr_pct": round((eq.iloc[-1] ** (1 / years) - 1) * 100, 2),
        "total_return_pct": round((eq.iloc[-1] - 1) * 100, 1),
        "sharpe": round(rets.mean() / sd * math.sqrt(252), 2) if sd > 0 else 0.0,
        "max_dd_pct": round((eq / eq.cummax() - 1).min() * 100, 1),
    }
    if n_trades is not None:
        out["trades_per_year"] = round(n_trades / years, 1)
    return out


def window(series: pd.Series, start: str, end: str | None) -> pd.Series:
    return series[(series.index >= pd.Timestamp(start)) & (series.index <= pd.Timestamp(end or "2100-01-01"))]


def verdict(strat: dict, spy: dict) -> bool:
    return (strat["sharpe"] >= spy["sharpe"] + 0.10 and strat["max_dd_pct"] >= 0.8 * spy["max_dd_pct"]
            and strat["total_return_pct"] > 0)


def main() -> int:
    spy, qqq = Days("SPY"), Days("QQQ")
    spy_ret = pd.Series(np.r_[0.0, spy.close[1:] / spy.close[:-1] - 1], index=pd.DatetimeIndex(spy.dates))
    runs = {
        "4_noise_area_1x": lambda c: noise_area(spy, c, 1.0),
        "4_noise_area_4x_paper_info_only": lambda c: noise_area(spy, c, 4.0),
        "5_last_half_hour": lambda c: last_half_hour(spy, c),
        "6_orb_qqq_1x": lambda c: opening_range(qqq, c),
    }
    results: dict = {"spy_buy_hold": {w: stats(window(spy_ret, *span)) for w, span in WINDOWS.items()}}
    for name, fn in runs.items():
        results[name] = {}
        for cost_name, cost in COSTS.items():
            rets, _, trades = fn(cost)
            idx = pd.DatetimeIndex(spy.dates if not name.startswith("6") else qqq.dates)
            series = pd.Series(rets, index=idx)
            per_window = {}
            for w, span in WINDOWS.items():
                part = window(series, *span)
                n = int((part != 0).sum())  # days with at least one trade
                per_window[w] = stats(part) | {"days_traded_per_year": round(n / (len(part) / 252), 1)}
            per_window["hit_rate_pct"] = round(100 * float(np.mean(np.array(trades) > 0)), 1)
            per_window["round_trips"] = len(trades)
            results[name][cost_name] = per_window
    oos_spy = results["spy_buy_hold"]["out_of_sample"]
    results["verdicts"] = {
        name: ("PASS" if verdict(results[name]["realistic"]["out_of_sample"], oos_spy) else "FAIL")
        for name in runs if "info_only" not in name
    }
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    results["meta"] = {"run_date": str(date.today()), "code_sha": sha, "data": "Alpaca SIP 1-min, raw, regular session",
                       "first_day": str(spy.dates[0].date()), "last_day": str(spy.dates[-1].date()),
                       "costs_per_share_per_side": COSTS, "windows": WINDOWS}
    out = ROOT / "backtests" / "intraday" / "results" / f"{date.today()}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
