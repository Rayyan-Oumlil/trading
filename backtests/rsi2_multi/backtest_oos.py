"""Multi-instrument RSI(2) portfolio backtest — OOS 2022-2024."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from strategies.rsi2_connors.signals import wilder_rsi  # noqa: E402

UNIVERSE = ["SPY", "QQQ", "IWM", "GLD", "TLT", "XLK", "XLE"]
START, END = "2021-01-01", "2024-12-31"
SLIPPAGE = 0.0005
POS_PCT = 0.12
STOP_PCT = 0.03
TIME_STOP = 5
MAX_POS = 5
INITIAL = 100_000.0

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def run() -> None:
    print(f"Downloading {len(UNIVERSE)} tickers {START} -> {END}...")
    raw = yf.download(UNIVERSE, start=START, end=END, auto_adjust=True, progress=False)

    close = raw["Close"].copy()
    opn   = raw["Open"].copy()
    low   = raw["Low"].copy()
    vol   = raw["Volume"].copy()
    close.columns = [str(c) for c in close.columns]
    opn.columns   = [str(c) for c in opn.columns]
    low.columns   = [str(c) for c in low.columns]
    vol.columns   = [str(c) for c in vol.columns]

    rsi  = pd.DataFrame({t: wilder_rsi(close[t].dropna(), 2).reindex(close.index) for t in UNIVERSE})
    sma5 = close.rolling(5).mean()

    cash = INITIAL
    positions: dict = {}
    trades: list[dict] = []
    equity_curve: list[dict] = []

    dates = close.index
    for i in range(1, len(dates)):
        date      = dates[i]
        prev_date = dates[i - 1]

        # ---------- EXIT ----------
        to_close: list[str] = []
        for t, pos in positions.items():
            if pd.isna(close.loc[date, t]):
                continue
            bar_low   = float(low.loc[date, t])
            bar_open  = float(opn.loc[date, t])
            prev_rsi  = rsi.loc[prev_date, t]
            prev_cl   = float(close.loc[prev_date, t])
            prev_sma  = sma5.loc[prev_date, t]

            exit_reason: str | None = None
            exit_price = bar_open * (1 - SLIPPAGE)

            if bar_low <= pos["stop_price"]:
                exit_reason = "stop_loss"
                exit_price  = pos["stop_price"] * (1 - SLIPPAGE)
            elif (not pd.isna(prev_rsi) and float(prev_rsi) > 70) or (
                not pd.isna(prev_sma) and prev_cl > float(prev_sma)
            ):
                exit_reason = "signal"
            elif (i - pos["entry_idx"]) >= TIME_STOP:
                exit_reason = "time_stop"

            if exit_reason:
                pnl = (exit_price - pos["entry_price"]) * pos["qty"]
                cash += pos["qty"] * exit_price
                trades.append({
                    "ticker": t,
                    "entry_date": str(pos["entry_date"].date()),
                    "exit_date": str(date.date()),
                    "entry_price": round(pos["entry_price"], 4),
                    "exit_price": round(exit_price, 4),
                    "qty": round(pos["qty"], 4),
                    "pnl": round(pnl, 2),
                    "reason": exit_reason,
                    "bars_held": i - pos["entry_idx"],
                })
                to_close.append(t)

        for t in to_close:
            del positions[t]

        # ---------- ENTRY ----------
        if len(positions) < MAX_POS:
            candidates: list[tuple[float, str]] = []
            for t in UNIVERSE:
                if t in positions:
                    continue
                r = rsi.loc[prev_date, t]
                v = vol.loc[prev_date, t]
                if pd.isna(r) or pd.isna(v):
                    continue
                if float(r) < 10 and float(v) > 0:
                    candidates.append((float(r), t))

            candidates.sort()
            slots = MAX_POS - len(positions)
            equity_now = cash + sum(
                p["qty"] * float(close.loc[date, t2])
                for t2, p in positions.items()
                if not pd.isna(close.loc[date, t2])
            )
            for _, t in candidates[:slots]:
                fill       = float(opn.loc[date, t]) * (1 + SLIPPAGE)
                allocation = equity_now * POS_PCT
                qty        = allocation / fill
                if qty * fill > cash:
                    continue
                cash -= qty * fill
                positions[t] = {
                    "qty": qty,
                    "entry_price": fill,
                    "stop_price": fill * (1 - STOP_PCT),
                    "entry_date": date,
                    "entry_idx": i,
                }

        # ---------- EQUITY SNAPSHOT ----------
        equity = cash + sum(
            p["qty"] * float(close.loc[date, t])
            for t, p in positions.items()
            if not pd.isna(close.loc[date, t])
        )
        equity_curve.append({"date": str(date.date()), "equity": equity})

    # Liquidate remaining
    for t, pos in positions.items():
        fill = float(close.iloc[-1][t]) * (1 - SLIPPAGE)
        pnl  = (fill - pos["entry_price"]) * pos["qty"]
        cash += pos["qty"] * fill
        trades.append({
            "ticker": t,
            "entry_date": str(pos["entry_date"].date()),
            "exit_date": str(dates[-1].date()),
            "entry_price": round(pos["entry_price"], 4),
            "exit_price": round(fill, 4),
            "qty": round(pos["qty"], 4),
            "pnl": round(pnl, 2),
            "reason": "end_of_period",
            "bars_held": len(dates) - 1 - pos["entry_idx"],
        })

    final_equity = cash
    eq_series = pd.Series(
        [e["equity"] for e in equity_curve],
        index=pd.to_datetime([e["date"] for e in equity_curve]),
    )
    returns   = eq_series.pct_change().dropna()
    total_ret = (final_equity - INITIAL) / INITIAL
    years     = max(len(equity_curve) / 252.0, 1e-9)
    ann_ret   = (1 + total_ret) ** (1 / years) - 1
    sharpe    = float(returns.mean() / returns.std()) * 252**0.5 if returns.std() > 0 else 0.0
    roll_max  = eq_series.cummax()
    max_dd    = float(((eq_series - roll_max) / roll_max).min())
    winners   = [tr for tr in trades if tr["pnl"] > 0]

    print(f"\n=== OOS Results (2022-2024) — RSI(2) Multi-Instrument ===")
    print(f"Total return:   {total_ret*100:.2f}%")
    print(f"Annualized:     {ann_ret*100:.2f}%")
    print(f"Sharpe:         {sharpe:.3f}")
    print(f"Max drawdown:   {max_dd*100:.2f}%")
    print(f"Total trades:   {len(trades)}")
    print(f"Trades/year:    {len(trades)/years:.1f}")
    if trades:
        print(f"Win rate:       {len(winners)/len(trades)*100:.1f}%")
        print(f"Avg bars held: {sum(t['bars_held'] for t in trades)/len(trades):.1f}")

    ticker_trades: dict[str, list] = {}
    for tr in trades:
        ticker_trades.setdefault(tr["ticker"], []).append(tr)

    print("\nPer-ticker breakdown:")
    for t in UNIVERSE:
        trs = ticker_trades.get(t, [])
        if not trs:
            print(f"  {t}: 0 trades")
            continue
        w   = sum(1 for x in trs if x["pnl"] > 0)
        pnl = sum(x["pnl"] for x in trs)
        print(f"  {t}: {len(trs)} trades, win {w/len(trs)*100:.0f}%, P&L ${pnl:+,.0f}")

    spy_bh = (float(close["SPY"].iloc[-1]) / float(close["SPY"].iloc[0]) - 1) * 100
    print(f"\nBenchmark SPY B&H: {spy_bh:.1f}%")

    result = {
        "total_return_pct": round(total_ret * 100, 2),
        "annualized_pct": round(ann_ret * 100, 2),
        "sharpe": round(sharpe, 3),
        "max_dd_pct": round(max_dd * 100, 2),
        "total_trades": len(trades),
        "trades_per_year": round(len(trades) / years, 1),
        "win_rate_pct": round(len(winners) / len(trades) * 100, 1) if trades else 0,
        "trades": trades,
        "equity_curve": equity_curve,
    }
    out = RESULTS_DIR / "oos_2022_2024.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    run()
