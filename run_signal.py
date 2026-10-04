"""
Portfolio executor — the ONE robot that places orders, in the IBKR PAPER account.

Sleeves (strategies/portfolio.py): SPY 85.5%, IBIT 5%, ETHA 5% of equity.
Each sleeve runs SMA(10) > SMA(50) on the series it was backtested on:
  - SPY on completed US sessions
  - IBIT / ETHA on completed UTC days of BTC-USD / ETH-USD
Per symbol it trades only on a flip: flat→long buys weight × equity, long→flat sells all.
Orders are market-on-open, so they fill at the next US session's open.

Refuses to trade (raises) on NaN/stale data, positions outside the sleeves, or a
failed order. A symbol already decided for its session, or with an order
pending, is skipped — so reruns never double-trade.

Alpaca was retired 2026-10-04 (plans/2026-10-04-ibkr-paper.md); its history
stays in memory/confidence-log.md.
"""
from __future__ import annotations

import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from brokers.ibkr import IbkrBroker  # noqa: E402
from paper_trading.guards import assert_only_expected_positions, order_failed  # noqa: E402
from paper_trading.kill_switch import is_halted  # noqa: E402
from paper_trading.yahoo_data import fetch_daily, last_completed_day, last_completed_session, through  # noqa: E402
from strategies.ma_crossover.signals import calculate_signals  # noqa: E402
from strategies.portfolio import ALLOWED_POSITIONS, SLEEVES, Sleeve, already_decided, decide, split_log_lines  # noqa: E402

TICKER = "SPY"
FAST = 10
SLOW = 50
LOOKBACK_DAYS = 120
CASH_USE = 0.99  # leave 1% of cash for fees/slippage
SCORES = {"BUY": 7, "HOLD": 7, "SELL": 6, "FLAT": 5}
REASONS = {
    "BUY": "cross-up confirmed",
    "HOLD": "position aligned with regime",
    "SELL": "regime flipped bearish",
    "FLAT": "awaiting cross-up",
}
CONFIDENCE_LOG = PROJECT_ROOT / "memory" / "confidence-log-ibkr.md"


def make_client() -> IbkrBroker:
    return IbkrBroker.connect()


def append_confidence(session: date, decision: str, score: int, reason: str) -> None:
    """Append one line to the confidence log, dated by US trading session."""
    line = f"{session.isoformat()} | {decision} | {score}/10 | {reason}\n"
    CONFIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONFIDENCE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)


def clean_bars(df: pd.DataFrame, symbol: str = TICKER) -> pd.DataFrame:
    """Drop incomplete rows (NaN close) and require a full SMA window."""
    cleaned = df.dropna(subset=["close"])
    if len(cleaned) < SLOW:
        raise RuntimeError(f"Only {len(cleaned)} valid bars for {symbol}; need {SLOW}")
    return cleaned


def current_regime(df: pd.DataFrame) -> tuple[float, float, bool]:
    """Return (sma_fast, sma_slow, should_be_long) based on the latest bar."""
    out = calculate_signals(df, fast_period=FAST, slow_period=SLOW)
    last = out.iloc[-1]
    sma_fast = float(last["sma_fast"])
    sma_slow = float(last["sma_slow"])
    # NaN compares False, which used to read as "bearish" and liquidate the position.
    if math.isnan(sma_fast) or math.isnan(sma_slow):
        raise RuntimeError(f"SMA is NaN (fast={sma_fast}, slow={sma_slow}); refusing to trade")
    return sma_fast, sma_slow, sma_fast > sma_slow


def place_checked(client: IbkrBroker, symbol: str, action: str, shares: float) -> None:
    result = client.place_market_order(symbol, shares, "buy" if action == "BUY" else "sell")
    print(f"  Order ID: {result.order_id}  Status: {result.status}")
    if order_failed(result.status):
        raise RuntimeError(f"{symbol} {action} order {result.order_id} failed with status {result.status}")


def buy_shares(sleeve: Sleeve, equity: float, price: float, budget: dict[str, float]) -> tuple[int, str]:
    """Whole shares for weight × equity, capped at USD cash (never borrow). Returns (shares, log note)."""
    notional = equity * sleeve.weight
    spendable = budget["cash"] * CASH_USE
    note = ""
    if notional > spendable:
        note = f"; capped at USD cash ${spendable:,.2f} (wanted ${notional:,.2f})"
        notional = spendable
    shares = math.floor(notional / price)
    if shares < 1:
        raise RuntimeError(
            f"{sleeve.symbol}: USD cash ${budget['cash']:,.2f} buys no share at ${price:,.2f}. "
            "Convert CAD to USD in the paper account (the robot never borrows)."
        )
    budget["cash"] -= shares * price
    return shares, note


def run_sleeve(client: IbkrBroker, sleeve: Sleeve, days: dict[str, date], equity: float, held: dict[str, float],
               log_lines: list[str], budget: dict[str, float]) -> None:
    symbol, session = sleeve.symbol, days["us_session"]
    if already_decided(log_lines, session, symbol):
        print(f"\n{symbol}: already decided for {session}. Skipping.")
        return

    signal = clean_bars(through(fetch_daily(sleeve.signal, LOOKBACK_DAYS), days[sleeve.clock], sleeve.signal), sleeve.signal)
    sma_fast, sma_slow, want_long = current_regime(signal)
    margin = f"fast-slow margin {(sma_fast - sma_slow) / sma_slow * 100:+.2f}%"
    print(f"\n{symbol} ({sleeve.signal} as of {signal.index[-1].date()}): SMA({FAST}) {sma_fast:,.2f}  "
          f"SMA({SLOW}) {sma_slow:,.2f}  -> {'LONG' if want_long else 'FLAT'}")

    if client.has_open_order(symbol):
        print(f"  PENDING — an order for {symbol} is already queued.")
        append_confidence(session, "PENDING", 6, f"{symbol}: open order exists; duplicate run skipped")
        return

    held_qty = held.get(symbol, 0.0)
    action = decide(want_long, held_qty)
    note = ""
    if action == "BUY":
        price = float(through(fetch_daily(symbol, 10), session, symbol)["close"].iloc[-1])
        shares, note = buy_shares(sleeve, equity, price, budget)
        print(f"  BUY {symbol}: {shares} sh (~${shares * price:,.2f} at last close ${price:,.2f})")
        place_checked(client, symbol, action, shares)
        note = f"; {shares} sh at open{note}"
    elif action == "SELL":
        print(f"  SELL {symbol}: {held_qty:g} sh")
        place_checked(client, symbol, action, held_qty)
        note = f"; {held_qty:g} sh at open"
    append_confidence(session, action, SCORES[action], f"{symbol}: {REASONS[action]}; {margin}{note}")


def read_log_lines() -> list[str]:
    return split_log_lines(CONFIDENCE_LOG.read_text(encoding="utf-8")) if CONFIDENCE_LOG.exists() else []


def main() -> int:
    now = datetime.now(timezone.utc)
    days = {
        "us_session": last_completed_session(fetch_daily(TICKER, 10).index, now),
        "utc_day": last_completed_day(now),
    }
    if is_halted():
        print("HALTED — kill switch active. No orders placed.")
        append_confidence(days["us_session"], "HALT", 0, "kill switch active")
        return 0

    client = make_client()
    errors: list[str] = []
    try:
        account = client.get_account()
        positions = client.get_positions()
        assert_only_expected_positions(positions, allowed=ALLOWED_POSITIONS, open_orders=client.get_open_orders())
        held = {p["symbol"]: p["qty"] for p in positions}
        print(f"Account {client.account_id}: equity ${account['equity']:,.2f}   USD cash ${account['cash']:,.2f}   "
              f"Positions: {held or 'none'}")
        budget = {"cash": account["cash"]}
        for sleeve in SLEEVES:
            try:  # one sleeve's failure (e.g. no USD for a buy) must not skip another sleeve's sell
                run_sleeve(client, sleeve, days, account["equity"], held, read_log_lines(), budget)
            except Exception as exc:  # noqa: BLE001 — collected and re-raised below
                print(f"  ERROR {sleeve.symbol}: {exc}")
                errors.append(f"{sleeve.symbol}: {exc}")
    finally:
        client.disconnect()
    if errors:
        raise RuntimeError("; ".join(errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
