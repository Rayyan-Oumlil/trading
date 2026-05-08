"""Backtest runner for RSI(2) Connors mean-reversion on SPY (with 200-DMA filter).

Usage:
    python backtests/rsi2_connors/run_backtest.py --start 2014-01-01 --end 2021-12-31 --label in_sample
    python backtests/rsi2_connors/run_backtest.py --start 2021-01-01 --end 2024-12-31 --label out_of_sample
    python backtests/rsi2_connors/run_backtest.py --start 2014-01-01 --end 2021-12-31 --label in_sample_with_stop --use-hard-stop

Note: --start should be ~1 year earlier than the analysis window so the 200-DMA
warmup completes before the first signal can fire. Results are reported only
for trades that closed within the requested window.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from strategies.rsi2_connors.signals import calculate_signals  # noqa: E402

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SLIPPAGE_PCT = 0.0005
POSITION_PCT = 0.95
HARD_STOP_PCT = 0.05  # only applied when --use-hard-stop is passed
TIME_STOP_BARS = 10


@dataclass(frozen=True)
class BacktestConfig:
    ticker: str
    start: str
    end: str
    label: str
    use_hard_stop: bool
    initial_equity: float = 100_000.0


def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for {ticker} {start} -> {end}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    return df


def run_backtest(
    df: pd.DataFrame,
    initial_equity: float = 100_000.0,
    use_hard_stop: bool = False,
) -> dict:
    """Replay RSI(2) Connors with no look-ahead.

    Entry on next-day open after long_entry=True on signal bar.
    Exit on next-day open after long_exit=True OR time stop OR (optional) hard stop.
    """
    signals = calculate_signals(df)

    cash = initial_equity
    position = 0.0
    entry_price = 0.0
    entry_date: str | None = None
    entry_idx = -1
    stop_price = 0.0
    trades: list[dict] = []
    equity_curve: list[dict] = []

    for i in range(1, len(signals)):
        row = signals.iloc[i]
        prev_row = signals.iloc[i - 1]
        date = signals.index[i]

        # 1) Hard stop (optional, intraday low check).
        if use_hard_stop and position > 0 and float(row["low"]) <= stop_price:
            fill = stop_price * (1 + SLIPPAGE_PCT)
            exit_value = position * fill
            pnl = (fill - entry_price) * position
            cash += exit_value
            trades.append({
                "entry_date": entry_date,
                "entry_price": round(entry_price, 4),
                "exit_date": str(date.date()),
                "exit_price": round(fill, 4),
                "shares": round(position, 4),
                "pnl": round(pnl, 2),
                "exit_reason": "hard_stop",
                "bars_held": i - entry_idx,
            })
            position = 0.0
            entry_idx = -1

        # 2) Signal exit at next-day open (uses prev bar's long_exit flag).
        if position > 0 and bool(prev_row["long_exit"]):
            fill = float(row["open"]) * (1 - SLIPPAGE_PCT)
            exit_value = position * fill
            pnl = (fill - entry_price) * position
            cash += exit_value
            trades.append({
                "entry_date": entry_date,
                "entry_price": round(entry_price, 4),
                "exit_date": str(date.date()),
                "exit_price": round(fill, 4),
                "shares": round(position, 4),
                "pnl": round(pnl, 2),
                "exit_reason": "signal",
                "bars_held": i - entry_idx,
            })
            position = 0.0
            entry_idx = -1

        # 3) Time stop: if neither exit fired within TIME_STOP_BARS, force exit at bar N+1.
        if position > 0 and entry_idx > 0 and (i - entry_idx) >= TIME_STOP_BARS:
            fill = float(row["open"]) * (1 - SLIPPAGE_PCT)
            exit_value = position * fill
            pnl = (fill - entry_price) * position
            cash += exit_value
            trades.append({
                "entry_date": entry_date,
                "entry_price": round(entry_price, 4),
                "exit_date": str(date.date()),
                "exit_price": round(fill, 4),
                "shares": round(position, 4),
                "pnl": round(pnl, 2),
                "exit_reason": "time_stop",
                "bars_held": i - entry_idx,
            })
            position = 0.0
            entry_idx = -1

        # 4) New entry: long_entry on prev bar -> buy at today's open.
        if position == 0 and bool(prev_row["long_entry"]):
            fill = float(row["open"]) * (1 + SLIPPAGE_PCT)
            shares = (cash * POSITION_PCT) / fill
            cost = shares * fill
            cash -= cost
            position = shares
            entry_price = fill
            entry_date = str(date.date())
            entry_idx = i
            stop_price = fill * (1 - HARD_STOP_PCT)

        equity_value = cash + position * float(row["close"])
        equity_curve.append({"date": str(date.date()), "equity": equity_value})

    # End-of-period: liquidate any open position at last close.
    if position > 0:
        last = signals.iloc[-1]
        fill = float(last["close"]) * (1 - SLIPPAGE_PCT)
        exit_value = position * fill
        pnl = (fill - entry_price) * position
        cash += exit_value
        trades.append({
            "entry_date": entry_date,
            "entry_price": round(entry_price, 4),
            "exit_date": str(signals.index[-1].date()),
            "exit_price": round(fill, 4),
            "shares": round(position, 4),
            "pnl": round(pnl, 2),
            "exit_reason": "end_of_period",
            "bars_held": len(signals) - 1 - entry_idx,
        })
        position = 0.0

    equity = cash

    equity_series = pd.Series(
        [e["equity"] for e in equity_curve],
        index=pd.to_datetime([e["date"] for e in equity_curve]),
    )

    returns = equity_series.pct_change().dropna()
    total_return = (equity - initial_equity) / initial_equity
    years = max(len(equity_curve) / 252.0, 1e-9)
    annualized_return = (1 + total_return) ** (1 / years) - 1
    sharpe = float(returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0.0
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

    win_trades = [t for t in trades if t["pnl"] > 0]
    win_rate = len(win_trades) / len(trades) if trades else 0.0
    avg_bars_held = (
        sum(t["bars_held"] for t in trades) / len(trades) if trades else 0.0
    )

    exit_reasons: dict[str, int] = {}
    for t in trades:
        exit_reasons[t["exit_reason"]] = exit_reasons.get(t["exit_reason"], 0) + 1

    return {
        "initial_equity": initial_equity,
        "final_equity": round(equity, 2),
        "total_return_pct": round(total_return * 100, 2),
        "annualized_return_pct": round(annualized_return * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "total_trades": len(trades),
        "win_rate_pct": round(win_rate * 100, 2),
        "trades_per_year": round(len(trades) / years, 2),
        "avg_bars_held": round(avg_bars_held, 2),
        "exit_reasons": exit_reasons,
        "trades": trades,
        "equity_curve": equity_curve,
    }


def benchmark_buy_hold(df: pd.DataFrame) -> dict:
    start_price = float(df["close"].iloc[0])
    end_price = float(df["close"].iloc[-1])
    total_return = (end_price - start_price) / start_price
    return {"total_return_pct": round(total_return * 100, 2)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2014-01-01")
    parser.add_argument("--end", default="2021-12-31")
    parser.add_argument("--label", default="run")
    parser.add_argument("--ticker", default="SPY")
    parser.add_argument(
        "--use-hard-stop",
        action="store_true",
        help="Apply a 5% hard stop (variant for sensitivity testing). Off by default per Connors original.",
    )
    args = parser.parse_args()

    print(f"Fetching {args.ticker} {args.start} -> {args.end}...")
    df = fetch_data(args.ticker, args.start, args.end)
    print(f"Loaded {len(df)} bars")

    print(f"Running backtest (use_hard_stop={args.use_hard_stop})...")
    stats = run_backtest(df, use_hard_stop=args.use_hard_stop)
    bh = benchmark_buy_hold(df)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = {
        "run_id": run_id,
        "label": args.label,
        "ticker": args.ticker,
        "start": args.start,
        "end": args.end,
        "use_hard_stop": args.use_hard_stop,
        "strategy": stats,
        "benchmark_buy_hold": bh,
    }

    out_path = RESULTS_DIR / f"{run_id}_{args.label}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Results ({args.label}) ===")
    print(f"Total return:       {stats['total_return_pct']}%")
    print(f"Annualized return:  {stats['annualized_return_pct']}%")
    print(f"Sharpe ratio:       {stats['sharpe_ratio']}")
    print(f"Max drawdown:       {stats['max_drawdown_pct']}%")
    print(f"Win rate:           {stats['win_rate_pct']}%")
    print(f"Total trades:       {stats['total_trades']}")
    print(f"Trades/year:        {stats['trades_per_year']}")
    print(f"Avg bars held:      {stats['avg_bars_held']}")
    print(f"Exit reasons:       {stats['exit_reasons']}")
    print(f"Benchmark (B&H):    {bh['total_return_pct']}%")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
