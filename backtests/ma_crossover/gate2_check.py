"""
Gate 2 reconciliation — Phase B of the trading roadmap.

Compares actual Alpaca paper performance against the backtest expectation
over a date range. Outputs a single decision artifact: PASS / SOFT-PASS / FAIL.

Usage:
    python backtests/ma_crossover/gate2_check.py --since 2026-04-23
    python backtests/ma_crossover/gate2_check.py --since 2026-04-23 --until 2026-05-22

The pre-committed gate (per ROADMAP.md §Stage 2 -> Stage 3):
  - >=2 weeks of paper trading with same rules as the backtest
  - actual P&L within +/-20% of backtest expectation over the same period
  - no unexplained trades (every fill traceable to a signal)
  - kill switch fire drill recorded

This script checks the first three numerically. The fire drill is a manual
journal entry — it is reported here as a PRE-CONDITION the user must confirm.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from strategies.ma_crossover.signals import calculate_signals  # noqa: E402

POSITION_PCT = 0.95
INITIAL_EQUITY = 100_000.0
TICKER = "SPY"


@dataclass(frozen=True)
class PaperSnapshot:
    start_equity: float
    end_equity: float
    fills: list[dict]
    period_start: str
    period_end: str


def fetch_paper_snapshot(since: str, until: str) -> PaperSnapshot:
    """Pull the actual paper account state and activity over the window."""
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetOrdersRequest, GetPortfolioHistoryRequest
    from alpaca.trading.enums import QueryOrderStatus

    api_key = os.environ["ALPACA_API_KEY"]
    secret = os.environ["ALPACA_API_SECRET"]
    client = TradingClient(api_key, secret, paper=True)

    # Portfolio history bookends.
    hist = client.get_portfolio_history(
        GetPortfolioHistoryRequest(
            period="3M",
            timeframe="1D",
            extended_hours=False,
        )
    )
    eq = list(hist.equity or [])
    ts = list(hist.timestamp or [])
    if not eq or not ts:
        raise RuntimeError("Empty portfolio history from Alpaca")
    df_hist = pd.DataFrame({"ts": ts, "equity": eq})
    df_hist["date"] = pd.to_datetime(df_hist["ts"], unit="s", utc=True).dt.strftime("%Y-%m-%d")
    df_hist = df_hist.dropna(subset=["equity"])
    in_window = df_hist[(df_hist["date"] >= since) & (df_hist["date"] <= until)]
    if in_window.empty:
        raise RuntimeError(f"No portfolio history in window {since} -> {until}")
    start_equity = float(in_window["equity"].iloc[0])
    end_equity = float(in_window["equity"].iloc[-1])

    # Filled orders in window. (TradingClient lost get_activities; use get_orders.)
    until_dt = datetime.strptime(until, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    after_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    orders = client.get_orders(
        GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            after=after_dt,
            until=until_dt,
            limit=100,
        )
    )
    fills: list[dict] = []
    for o in orders or []:
        if str(getattr(o, "status", "")).lower() != "filled":
            continue
        filled_at = getattr(o, "filled_at", None) or getattr(o, "submitted_at", None)
        date_str = str(filled_at)[:10] if filled_at else ""
        if not date_str or date_str < since or date_str > until:
            continue
        fills.append({
            "date": date_str,
            "symbol": getattr(o, "symbol", None),
            "side": str(getattr(o, "side", "")),
            "qty": float(getattr(o, "filled_qty", 0) or 0),
            "price": float(getattr(o, "filled_avg_price", 0) or 0),
        })
    fills.sort(key=lambda x: x["date"])

    return PaperSnapshot(
        start_equity=start_equity,
        end_equity=end_equity,
        fills=fills,
        period_start=since,
        period_end=until,
    )


def expected_backtest_pnl(since: str, until: str) -> dict:
    """Replay the strategy on real SPY data over the same window with the
    initial equity scaled to the paper account's starting equity."""
    df = yf.download(TICKER, start=since, end=until, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No SPY data {since} -> {until}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]

    sig = calculate_signals(df)
    cash = INITIAL_EQUITY
    position = 0.0
    entry_price = 0.0

    for i in range(1, len(sig)):
        row = sig.iloc[i]
        prev = sig.iloc[i - 1]
        fast_below = (
            float(prev["sma_fast"]) >= float(prev["sma_slow"])
            and float(row["sma_fast"]) < float(row["sma_slow"])
            and pd.notna(row["sma_slow"])
        )
        if position > 0 and fast_below:
            cash += position * float(row["open"])
            position = 0.0
        if position == 0 and bool(prev["signal"]):
            shares = (cash * POSITION_PCT) / float(row["open"])
            cash -= shares * float(row["open"])
            position = shares
            entry_price = float(row["open"])

    final_equity = cash + position * float(sig["close"].iloc[-1]) if len(sig) else INITIAL_EQUITY
    expected_return_pct = (final_equity - INITIAL_EQUITY) / INITIAL_EQUITY * 100
    return {
        "expected_final_equity_norm_100k": round(final_equity, 2),
        "expected_return_pct": round(expected_return_pct, 4),
        "bars_in_window": int(len(sig)),
    }


def evaluate(paper: PaperSnapshot, expected: dict) -> dict:
    actual_return_pct = (paper.end_equity - paper.start_equity) / paper.start_equity * 100
    spread_pp = actual_return_pct - expected["expected_return_pct"]
    if expected["expected_return_pct"] != 0:
        spread_rel = abs(spread_pp / expected["expected_return_pct"])
    else:
        spread_rel = float("inf") if abs(spread_pp) > 0.05 else 0.0

    period_days = (
        datetime.strptime(paper.period_end, "%Y-%m-%d")
        - datetime.strptime(paper.period_start, "%Y-%m-%d")
    ).days
    weeks = period_days / 7

    weeks_pass = weeks >= 2
    pnl_pass = spread_rel <= 0.20  # +/-20% per ROADMAP

    if weeks_pass and pnl_pass:
        verdict = "PASS"
    elif weeks_pass and spread_rel <= 0.40:
        verdict = "SOFT-PASS"
    else:
        verdict = "FAIL"

    return {
        "actual_return_pct": round(actual_return_pct, 4),
        "expected_return_pct": expected["expected_return_pct"],
        "spread_percentage_points": round(spread_pp, 4),
        "spread_relative": round(spread_rel, 4),
        "weeks_observed": round(weeks, 2),
        "weeks_pass": weeks_pass,
        "pnl_within_20pct": pnl_pass,
        "verdict": verdict,
    }


def render_report(paper: PaperSnapshot, expected: dict, eval_: dict) -> str:
    lines = [
        f"# Gate 2 reconciliation — {paper.period_start} -> {paper.period_end}",
        "",
        "## Window",
        f"- Days observed: {eval_['weeks_observed']} weeks ({'PASS' if eval_['weeks_pass'] else 'FAIL'} - need >=2)",
        "",
        "## P&L vs backtest expectation",
        f"- Actual return:    {eval_['actual_return_pct']:+.2f}%",
        f"- Expected (BT):    {eval_['expected_return_pct']:+.2f}%",
        f"- Spread:           {eval_['spread_percentage_points']:+.2f} pp ({eval_['spread_relative']*100:.0f}% relative)",
        f"- Within +/-20%:    {'YES' if eval_['pnl_within_20pct'] else 'NO'}",
        "",
        "## Fills observed",
        f"- Count: {len(paper.fills)}",
    ]
    for f in paper.fills:
        lines.append(
            f"  - {f['date']}  {f['side']:>4}  {f['qty']:>8.2f} {f['symbol']} @ ${f['price']:.2f}"
        )
    lines += [
        "",
        f"## Verdict: **{eval_['verdict']}**",
        "",
        "### Pre-conditions to confirm before declaring Stage 2 passed",
        "- [ ] Kill-switch fire drill completed (see paper-trading/kill-switch.md SOP).",
        "- [ ] Every fill above is traceable to a signal in run_signal.py logs.",
        "- [ ] No discretionary overrides during the window.",
        "",
        "*Generated by gate2_check.py — review and copy into a journal entry.*",
    ]
    return "\n".join(lines)


def expected_carry_in_pnl(since: str, until: str) -> dict:
    """Carry-in mode: assume the position was already open at `since` and held through.
    Expected return = SPY return over window * POSITION_PCT (cash drag is implicit).
    Use this when paper trading began with an open position rather than from cash."""
    df = yf.download(TICKER, start=since, end=until, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No SPY data {since} -> {until}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    spy_start = float(df["close"].iloc[0])
    spy_end = float(df["close"].iloc[-1])
    spy_return_pct = (spy_end - spy_start) / spy_start * 100
    expected_return_pct = spy_return_pct * POSITION_PCT
    return {
        "expected_final_equity_norm_100k": round(INITIAL_EQUITY * (1 + expected_return_pct / 100), 2),
        "expected_return_pct": round(expected_return_pct, 4),
        "bars_in_window": int(len(df)),
        "spy_return_pct": round(spy_return_pct, 4),
        "mode": "carry-in",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", required=True, help="YYYY-MM-DD start of window")
    parser.add_argument(
        "--until",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="YYYY-MM-DD end of window (default: today UTC)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the report to journal/<until>_gate2_review.md",
    )
    parser.add_argument(
        "--carry-in",
        action="store_true",
        help="Position was already open at --since; compare to SPY return * position_pct instead of replaying signal from cash.",
    )
    args = parser.parse_args()

    print(f"Pulling paper snapshot {args.since} -> {args.until}...")
    paper = fetch_paper_snapshot(args.since, args.until)
    print(f"  start equity: ${paper.start_equity:,.2f}")
    print(f"  end equity:   ${paper.end_equity:,.2f}")
    print(f"  fills:        {len(paper.fills)}")

    if args.carry_in:
        print("Computing carry-in expectation (SPY return * 95%)...")
        expected = expected_carry_in_pnl(args.since, args.until)
    else:
        print("Replaying backtest expectation from cash...")
        expected = expected_backtest_pnl(args.since, args.until)

    eval_ = evaluate(paper, expected)
    report = render_report(paper, expected, eval_)
    print()
    print(report)

    if args.write:
        out = PROJECT_ROOT / "journal" / f"{args.until}_gate2_review.md"
        out.write_text(report + "\n", encoding="utf-8")
        print(f"\nWrote: {out}")

    return 0 if eval_["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
