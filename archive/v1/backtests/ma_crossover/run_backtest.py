"""
Backtest runner for MA crossover on SPY.

Usage:
    python backtests/ma_crossover/run_backtest.py --start 2015-01-01 --end 2021-12-31 --label in_sample
    python backtests/ma_crossover/run_backtest.py --start 2022-01-01 --end 2024-12-31 --label out_of_sample
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

from strategies.ma_crossover.signals import calculate_signals  # noqa: E402

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SLIPPAGE_PCT = 0.0005
POSITION_PCT = 0.95
STOP_LOSS_PCT = 0.05


@dataclass(frozen=True)
class BacktestConfig:
    ticker: str
    start: str
    end: str
    label: str
    initial_equity: float = 100_000.0


def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for {ticker} {start} -> {end}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    return df


def fetch_vix(start: str, end: str) -> pd.Series:
    df = yf.download("^VIX", start=start, end=end, auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError(f"No VIX data {start} -> {end}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    return df["close"].rename("vix")


def run_backtest(
    df: pd.DataFrame,
    initial_equity: float = 100_000.0,
    vix: pd.Series | None = None,
    vix_max: float | None = None,
) -> dict:
    signals = calculate_signals(df, vix=vix, vix_max=vix_max)

    cash = initial_equity
    position = 0.0
    entry_price = 0.0
    entry_date: str | None = None
    stop_price = 0.0
    trades: list[dict] = []
    equity_curve: list[dict] = []

    for i in range(1, len(signals)):
        row = signals.iloc[i]
        prev_row = signals.iloc[i - 1]
        date = signals.index[i]

        # Stop loss check (uses bar low; gap-down would fill at open but we simplify)
        if position > 0 and float(row["low"]) <= stop_price:
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
                "exit_reason": "stop_loss",
            })
            position = 0.0

        fast_below = (
            float(prev_row["sma_fast"]) >= float(prev_row["sma_slow"])
            and float(row["sma_fast"]) < float(row["sma_slow"])
            and pd.notna(row["sma_slow"])
        )
        if position > 0 and fast_below:
            fill = float(row["open"]) * (1 + SLIPPAGE_PCT)
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
            })
            position = 0.0

        if position == 0 and bool(prev_row["signal"]):
            fill = float(row["open"]) * (1 + SLIPPAGE_PCT)
            shares = (cash * POSITION_PCT) / fill
            cost = shares * fill
            cash -= cost
            position = shares
            entry_price = fill
            entry_date = str(date.date())
            stop_price = fill * (1 - STOP_LOSS_PCT)

        equity_value = cash + position * float(row["close"])
        equity_curve.append({"date": str(date.date()), "equity": equity_value})

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
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2021-12-31")
    parser.add_argument("--label", default="run")
    parser.add_argument("--ticker", default="SPY")
    parser.add_argument(
        "--vix-gate",
        action="store_true",
        help="Apply VIX regime filter: only take signals when VIX < --vix-max.",
    )
    parser.add_argument(
        "--vix-max",
        type=float,
        default=25.0,
        help="VIX threshold (literature default 25). Ignored unless --vix-gate.",
    )
    args = parser.parse_args()

    print(f"Fetching {args.ticker} {args.start} -> {args.end}...")
    df = fetch_data(args.ticker, args.start, args.end)
    print(f"Loaded {len(df)} bars")

    vix_series: pd.Series | None = None
    vix_max: float | None = None
    if args.vix_gate:
        print(f"Fetching ^VIX (gate threshold {args.vix_max})...")
        vix_series = fetch_vix(args.start, args.end)
        vix_max = args.vix_max

    print("Running backtest...")
    stats = run_backtest(df, vix=vix_series, vix_max=vix_max)
    bh = benchmark_buy_hold(df)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = {
        "run_id": run_id,
        "label": args.label,
        "ticker": args.ticker,
        "start": args.start,
        "end": args.end,
        "vix_gate": args.vix_gate,
        "vix_max": vix_max,
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
    print(f"Benchmark (B&H):    {bh['total_return_pct']}%")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
