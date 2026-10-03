"""
One-shot run of the three candidates pre-registered in research/queue.md (2026-10-03).
Usage: python -m backtests.candidates.run
Writes backtests/candidates/results/<date>.json. Never re-run with changed parameters.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

from backtests.candidates.engine import metrics, passes, simulate
from backtests.candidates.strategies import crypto_ma_targets, dual_momentum_targets, sector_momentum_targets

RESULTS = Path(__file__).resolve().parent / "results"
RECENT_START = "2022-01-01"
REGIME_YEARS = (2008, 2020, 2022)


def closes(tickers: list[str], start: str) -> pd.DataFrame:
    df = yf.download(tickers, start=start, auto_adjust=True, progress=False)["Close"]
    return df[tickers].dropna(how="all")


def buy_and_hold(prices: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame([weights], index=prices.index[:1])


def evaluate(name, prices, targets, bench_prices, bench_weights, start, cost_bps, ppy) -> dict:
    p, bp = prices.loc[start:], bench_prices.loc[start:]
    eq = simulate(p, targets.loc[start:], cost_bps)
    beq = simulate(bp, buy_and_hold(bp, bench_weights), cost_bps)
    windows = {"full": (eq, beq), "recent": (eq.loc[RECENT_START:], beq.loc[RECENT_START:])}
    strat = {w: metrics(e, ppy) for w, (e, _) in windows.items()}
    bench = {w: metrics(b, ppy) for w, (_, b) in windows.items()}
    regimes = {
        str(y): {"strategy_pct": float(eq.loc[str(y)].iloc[-1] / eq.loc[str(y)].iloc[0] - 1) * 100,
                 "benchmark_pct": float(beq.loc[str(y)].iloc[-1] / beq.loc[str(y)].iloc[0] - 1) * 100}
        for y in REGIME_YEARS if str(y) in eq.index.year.astype(str)
    }
    return {"name": name, "strategy": strat, "benchmark": bench, "regimes": regimes,
            "rebalances": int(len(targets.loc[start:])), "passed": passes(strat, bench), "equity": eq}


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    sectors = closes(["XLK", "XLF", "XLE", "XLV", "XLI"], "2004-06-01")
    gem = closes(["SPY", "EFA", "AGG", "BIL"], "2003-10-01")
    spy = gem[["SPY"]]
    crypto = closes(["BTC-USD", "ETH-USD"], "2017-09-01")

    runs = [
        evaluate("sector_momentum", sectors, sector_momentum_targets(sectors), spy, {"SPY": 1.0}, "2005-01-01", 10, 252),
        evaluate("dual_momentum", gem, dual_momentum_targets(gem), spy, {"SPY": 1.0}, "2005-01-01", 10, 252),
        evaluate("crypto_trend", crypto, crypto_ma_targets(crypto), crypto,
                 {"BTC-USD": 0.5, "ETH-USD": 0.5}, "2018-01-01", 25, 365),
    ]
    crypto_ret = runs[2]["equity"].pct_change()
    spy_ret = spy["SPY"].pct_change()
    runs[2]["corr_with_spy"] = float(crypto_ret.reindex(spy_ret.index).corr(spy_ret))

    out = {"run_date": str(date.today()), "git_sha": sha, "data_source": "yfinance auto_adjust",
           "spec": "research/queue.md pre-registration 2026-10-03",
           "results": [{k: v for k, v in r.items() if k != "equity"} for r in runs]}
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{date.today()}.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    for r in out["results"]:
        print(f"\n== {r['name']}  ->  {'PASS' if r['passed'] else 'FAIL'}  ({r['rebalances']} rebalances)")
        for w in ("full", "recent"):
            s, b = r["strategy"][w], r["benchmark"][w]
            print(f"  {w:6} {s['start']}..{s['end']}  CAGR {s['cagr_pct']:6.2f}% vs {b['cagr_pct']:6.2f}%  "
                  f"Sharpe {s['sharpe']:.2f} vs {b['sharpe']:.2f}  MaxDD {s['max_drawdown_pct']:6.1f}% vs {b['max_drawdown_pct']:6.1f}%")
        for y, v in r["regimes"].items():
            print(f"  {y}: {v['strategy_pct']:6.1f}% vs {v['benchmark_pct']:6.1f}%")
        if "corr_with_spy" in r:
            print(f"  correlation with SPY: {r['corr_with_spy']:.2f}")
    print(f"\nSaved {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
