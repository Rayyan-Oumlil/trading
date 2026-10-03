"""
Portfolio executor — the ONE robot that places orders in the Alpaca paper account.

Sleeves (strategies/portfolio.py): SPY 85.5%, BTC/USD 5%, ETH/USD 5% of equity.
Each sleeve runs SMA(10) > SMA(50) on completed bars:
  - SPY on completed US sessions (orders queue for the next open)
  - crypto on completed UTC days (orders fill immediately, 24/7)
Per symbol it trades only on a flip: flat→long buys weight × equity, long→flat sells all.

Refuses to trade (raises) on NaN/stale data, positions outside the sleeves, or a
failed order. A symbol already decided for its session/day, or with an order
pending, is skipped — so reruns never double-trade.

Paper trading only. Never touches live account.
"""
from __future__ import annotations

import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from paper_trading.alpaca_client import AlpacaClient, is_crypto, position_symbol  # noqa: E402
from paper_trading.crypto_data import get_crypto_daily_bars, last_completed_day  # noqa: E402
from paper_trading.guards import assert_only_expected_positions, order_failed  # noqa: E402
from paper_trading.kill_switch import is_halted       # noqa: E402
from paper_trading.market_calendar import last_completed_session  # noqa: E402
from paper_trading.market_data import SIP_DELAY, get_daily_bars  # noqa: E402
from strategies.ma_crossover.signals import calculate_signals  # noqa: E402
from strategies.portfolio import ALLOWED_POSITIONS, SLEEVES, Sleeve, already_decided, decide, split_log_lines  # noqa: E402

TICKER = "SPY"
FAST = 10
SLOW = 50
LOOKBACK_DAYS = 120
CALENDAR_WINDOW = timedelta(days=10)
SCORES = {"BUY": 7, "HOLD": 7, "SELL": 6, "FLAT": 5}
REASONS = {
    "BUY": "cross-up confirmed",
    "HOLD": "position aligned with regime",
    "SELL": "regime flipped bearish",
    "FLAT": "awaiting cross-up",
}

CONFIDENCE_LOG = PROJECT_ROOT / "memory" / "confidence-log.md"


def append_confidence(session: date, decision: str, score: int, reason: str) -> None:
    """Append one line to memory/confidence-log.md, dated by trading session/day."""
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


def fetch_bars(sleeve: Sleeve, day: date) -> pd.DataFrame:
    if sleeve.clock == "utc_day":
        return get_crypto_daily_bars(sleeve.symbol, lookback_days=LOOKBACK_DAYS, last_day=day)
    return get_daily_bars(sleeve.symbol, lookback_days=LOOKBACK_DAYS, last_session=day)


def place_checked(client: AlpacaClient, symbol: str, action: str, size: float) -> None:
    if action == "BUY" and is_crypto(symbol):
        result = client.place_notional_buy(symbol, size)
    else:
        result = client.place_market_order(symbol, size, "buy" if action == "BUY" else "sell")
    print(f"  Order ID: {result.order_id}  Status: {result.status}")
    if order_failed(result.status):
        raise RuntimeError(f"{symbol} {action} order {result.order_id} failed with status {result.status}")


def run_sleeve(client: AlpacaClient, sleeve: Sleeve, day: date, equity: float, held: dict[str, float],
               log_lines: list[str]) -> None:
    symbol = sleeve.symbol
    if already_decided(log_lines, day, symbol):
        print(f"\n{symbol}: already decided for {day}. Skipping.")
        return

    df = clean_bars(fetch_bars(sleeve, day), symbol)
    sma_fast, sma_slow, want_long = current_regime(df)
    last_close = float(df["close"].iloc[-1])
    margin = f"fast-slow margin {(sma_fast - sma_slow) / sma_slow * 100:+.2f}%"
    print(f"\n{symbol} as of {df.index[-1].date()}: close ${last_close:,.2f}  "
          f"SMA({FAST}) {sma_fast:,.2f}  SMA({SLOW}) {sma_slow:,.2f}  -> {'LONG' if want_long else 'FLAT'}")

    if client.has_open_order(symbol):
        print(f"  PENDING — an order for {symbol} is already queued.")
        append_confidence(day, "PENDING", 6, f"{symbol}: open order exists; duplicate run skipped")
        return

    held_qty = held.get(position_symbol(symbol), 0.0)
    action = decide(want_long, held_qty)
    if action == "BUY":
        notional = equity * sleeve.weight
        size = notional if is_crypto(symbol) else round(notional / last_close, 2)
        print(f"  BUY {symbol}: {'$' + format(size, ',.2f') if is_crypto(symbol) else str(size) + ' sh'}")
        place_checked(client, symbol, action, size)
    elif action == "SELL":
        print(f"  SELL {symbol}: {held_qty}")
        place_checked(client, symbol, action, held_qty)
    append_confidence(day, action, SCORES[action], f"{symbol}: {REASONS[action]}; {margin}")


def read_log_lines() -> list[str]:
    return split_log_lines(CONFIDENCE_LOG.read_text(encoding="utf-8")) if CONFIDENCE_LOG.exists() else []


def main() -> int:
    if is_halted():
        print("HALTED — kill switch active. No orders placed.")
        append_confidence(datetime.now(timezone.utc).date(), "HALT", 0, "kill switch active")
        return 0

    client = AlpacaClient()
    now = datetime.now(timezone.utc)
    # A session only counts once its full bar is servable (SIP data lags 16 min); otherwise we'd trade a partial bar.
    days = {
        "us_session": last_completed_session(now - SIP_DELAY, client.get_calendar(now.date() - CALENDAR_WINDOW, now.date())),
        "utc_day": last_completed_day(now),
    }

    account = client.get_account()
    positions = client.get_positions()
    assert_only_expected_positions(positions, allowed=ALLOWED_POSITIONS, open_orders=client.get_open_orders())
    held = {p["symbol"]: p["qty"] for p in positions}
    print(f"Account equity: ${account['equity']:,.2f}   Cash: ${account['cash']:,.2f}   Positions: {held or 'none'}")

    for sleeve in SLEEVES:
        run_sleeve(client, sleeve, days[sleeve.clock], account["equity"], held, read_log_lines())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
