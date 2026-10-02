"""
MA crossover signal executor — run this once per trading day after market close.

Logic:
  - Fetch daily bars for SPY from Alpaca through the last completed session
  - Compute SMA(10) and SMA(50)
  - If sma_fast > sma_slow  AND no position  → BUY  (95% of cash)
  - If sma_fast <= sma_slow AND has position → SELL (full position)
  - Otherwise → nothing to do

Refuses to trade (raises) on NaN/stale data, foreign positions in the account,
or a rejected order. A second run while an order is pending is a no-op.

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

from paper_trading.alpaca_client import AlpacaClient  # noqa: E402
from paper_trading.guards import assert_only_expected_positions, order_failed  # noqa: E402
from paper_trading.kill_switch import is_halted       # noqa: E402
from paper_trading.market_calendar import last_completed_session  # noqa: E402
from paper_trading.market_data import get_daily_bars  # noqa: E402
from strategies.ma_crossover.signals import calculate_signals  # noqa: E402

TICKER = "SPY"
POSITION_PCT = 0.95
FAST = 10
SLOW = 50
LOOKBACK_DAYS = 120
CALENDAR_WINDOW = timedelta(days=10)

CONFIDENCE_LOG = PROJECT_ROOT / "memory" / "confidence-log.md"


def append_confidence(session: date, decision: str, score: int, reason: str) -> None:
    """Append one line to memory/confidence-log.md, dated by trading session."""
    line = f"{session.isoformat()} | {decision} | {score}/10 | {reason}\n"
    CONFIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONFIDENCE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)


def clean_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Drop incomplete rows (NaN close) and require a full SMA window."""
    cleaned = df.dropna(subset=["close"])
    if len(cleaned) < SLOW:
        raise RuntimeError(f"Only {len(cleaned)} valid bars for {TICKER}; need {SLOW}")
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


def place_checked(client: AlpacaClient, qty: float, side: str) -> None:
    result = client.place_market_order(TICKER, qty, side)
    print(f"  Order ID: {result.order_id}")
    print(f"  Status:   {result.status}")
    if order_failed(result.status):
        raise RuntimeError(f"{TICKER} {side} order {result.order_id} failed with status {result.status}")
    if result.filled_avg_price:
        print(f"  Filled:   ${result.filled_avg_price:.2f}")


def main() -> int:
    if is_halted():
        print("HALTED — kill switch active. No orders placed.")
        append_confidence(datetime.now(timezone.utc).date(), "HALT", 0, "kill switch active")
        return 0

    client = AlpacaClient()
    now = datetime.now(timezone.utc)
    session = last_completed_session(now, client.get_calendar(now.date() - CALENDAR_WINDOW, now.date()))

    print(f"Fetching {TICKER} bars through session {session}...")
    df = clean_bars(get_daily_bars(TICKER, lookback_days=LOOKBACK_DAYS, last_session=session))
    sma_fast, sma_slow, should_be_long = current_regime(df)
    last_close = float(df["close"].iloc[-1])
    last_date = str(df.index[-1].date())

    print(f"\n{TICKER} as of {last_date}")
    print(f"  Close:     ${last_close:.2f}")
    print(f"  SMA({FAST}):   ${sma_fast:.2f}")
    print(f"  SMA({SLOW}):   ${sma_slow:.2f}")
    print(f"  Regime:    {'BULLISH (fast > slow)' if should_be_long else 'BEARISH (fast <= slow)'}")

    account = client.get_account()
    positions = client.get_positions()
    assert_only_expected_positions(positions, allowed={TICKER})
    spy_pos = next((p for p in positions if p["symbol"] == TICKER), None)

    print(f"\nAccount equity: ${account['equity']:,.2f}")
    print(f"Cash:           ${account['cash']:,.2f}")
    spy_pos_str = f"qty={spy_pos['qty']:.2f}" if spy_pos else "none"
    print(f"SPY position:   {spy_pos_str}")

    if client.has_open_order(TICKER):
        print("\nPENDING — an order for this session is already queued. Nothing to do.")
        append_confidence(session, "PENDING", 6, "open order exists; duplicate run skipped")
        return 0

    regime_margin_pct = (sma_fast - sma_slow) / sma_slow * 100
    margin_phrase = f"fast-slow margin {regime_margin_pct:+.2f}%"

    # --- Decision ---
    if should_be_long and spy_pos is None:
        cash = account["cash"]
        qty = round((cash * POSITION_PCT) / last_close, 2)
        if qty < 0.01:
            print("\nNot enough cash to open a position. No order placed.")
            append_confidence(session, "FLAT", 4, f"insufficient cash; {margin_phrase}")
            return 0
        print(f"\nSIGNAL: BUY — placing market order for {qty} shares of {TICKER}...")
        place_checked(client, qty, "buy")
        append_confidence(session, "BUY", 7, f"cross-up confirmed; {margin_phrase}")

    elif not should_be_long and spy_pos is not None:
        qty = spy_pos["qty"]
        print(f"\nSIGNAL: SELL — closing {qty} shares of {TICKER}...")
        place_checked(client, qty, "sell")
        append_confidence(session, "SELL", 6, f"regime flipped bearish; {margin_phrase}")

    elif should_be_long:
        print(f"\nHOLD — already long {spy_pos['qty']} shares. Nothing to do.")
        append_confidence(session, "HOLD", 7, f"position aligned with regime; {margin_phrase}")
    else:
        print("\nFLAT — bearish regime, no position. Nothing to do.")
        append_confidence(session, "FLAT", 5, f"awaiting cross-up; {margin_phrase}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
