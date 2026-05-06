"""
MA crossover signal executor — run this once per trading day after market close.

Logic:
  - Fetch last 60 daily bars for SPY
  - Compute SMA(10) and SMA(50)
  - If sma_fast > sma_slow  AND no position  → BUY  (95% of cash)
  - If sma_fast <= sma_slow AND has position → SELL (full position)
  - Otherwise → nothing to do

Paper trading only. Never touches live account.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from paper_trading.alpaca_client import AlpacaClient  # noqa: E402
from paper_trading.kill_switch import is_halted       # noqa: E402
from strategies.ma_crossover.signals import calculate_signals  # noqa: E402

TICKER = "SPY"
POSITION_PCT = 0.95
FAST = 10
SLOW = 50

CONFIDENCE_LOG = PROJECT_ROOT / "memory" / "confidence-log.md"


def append_confidence(decision: str, score: int, reason: str) -> None:
    """Append one line to memory/confidence-log.md. Routine self-test signal."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line = f"{date_str} | {decision} | {score}/10 | {reason}\n"
    CONFIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONFIDENCE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)


def fetch_bars(ticker: str, lookback: int = 120) -> pd.DataFrame:
    df = yf.download(ticker, period=f"{lookback}d", auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No data returned for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    return df


def current_regime(df: pd.DataFrame) -> tuple[float, float, bool]:
    """Return (sma_fast, sma_slow, should_be_long) based on the latest bar."""
    out = calculate_signals(df, fast_period=FAST, slow_period=SLOW)
    last = out.iloc[-1]
    sma_fast = float(last["sma_fast"])
    sma_slow = float(last["sma_slow"])
    return sma_fast, sma_slow, sma_fast > sma_slow


def main() -> int:
    if is_halted():
        print("HALTED — kill switch active. No orders placed.")
        append_confidence("HALT", 0, "kill switch active")
        return 0

    print(f"Fetching {TICKER} bars...")
    df = fetch_bars(TICKER)
    sma_fast, sma_slow, should_be_long = current_regime(df)
    last_close = float(df["close"].iloc[-1])
    last_date = str(df.index[-1].date())

    print(f"\n{TICKER} as of {last_date}")
    print(f"  Close:     ${last_close:.2f}")
    print(f"  SMA({FAST}):   ${sma_fast:.2f}")
    print(f"  SMA({SLOW}):   ${sma_slow:.2f}")
    print(f"  Regime:    {'BULLISH (fast > slow)' if should_be_long else 'BEARISH (fast <= slow)'}")

    client = AlpacaClient()
    account = client.get_account()
    positions = client.get_positions()
    spy_pos = next((p for p in positions if p["symbol"] == TICKER), None)

    print(f"\nAccount equity: ${account['equity']:,.2f}")
    print(f"Cash:           ${account['cash']:,.2f}")
    spy_pos_str = f"qty={spy_pos['qty']:.2f}" if spy_pos else "none"
    print(f"SPY position:   {spy_pos_str}")

    regime_margin_pct = (sma_fast - sma_slow) / sma_slow * 100 if sma_slow else 0.0
    margin_phrase = f"fast-slow margin {regime_margin_pct:+.2f}%"

    # --- Decision ---
    if should_be_long and spy_pos is None:
        cash = account["cash"]
        qty = round((cash * POSITION_PCT) / last_close, 2)
        if qty < 0.01:
            print("\nNot enough cash to open a position. No order placed.")
            append_confidence("FLAT", 4, f"insufficient cash; {margin_phrase}")
            return 0
        print(f"\nSIGNAL: BUY — placing market order for {qty} shares of {TICKER}...")
        result = client.place_market_order(TICKER, qty, "buy")
        print(f"  Order ID: {result.order_id}")
        print(f"  Status:   {result.status}")
        if result.filled_avg_price:
            print(f"  Filled:   ${result.filled_avg_price:.2f}")
        append_confidence("BUY", 7, f"cross-up confirmed; {margin_phrase}")

    elif not should_be_long and spy_pos is not None:
        qty = spy_pos["qty"]
        print(f"\nSIGNAL: SELL — closing {qty} shares of {TICKER}...")
        result = client.place_market_order(TICKER, qty, "sell")
        print(f"  Order ID: {result.order_id}")
        print(f"  Status:   {result.status}")
        if result.filled_avg_price:
            print(f"  Filled:   ${result.filled_avg_price:.2f}")
        append_confidence("SELL", 6, f"regime flipped bearish; {margin_phrase}")

    else:
        if should_be_long and spy_pos is not None:
            print(f"\nHOLD — already long {spy_pos['qty']} shares. Nothing to do.")
            append_confidence("HOLD", 7, f"position aligned with regime; {margin_phrase}")
        else:
            print("\nFLAT — bearish regime, no position. Nothing to do.")
            append_confidence("FLAT", 5, f"awaiting cross-up; {margin_phrase}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
