"""
One-off: convert the paper account's CAD cash to USD so the robot can buy US-listed ETFs.

The IBKR paper account starts with 1,000,000 CAD and the robot can only pay in USD
(brokers/ibkr.py). Converts 98% of the CAD and keeps the rest as a fee buffer.
Does nothing if the account already holds USD, so a second run is harmless.
Forex (IDEALPRO) is closed from Friday 17:00 to Sunday 17:15 New York time.

Usage (GitHub): daily-trade workflow, mode fx-convert. Locally: python -m brokers.fx_convert
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brokers.ibkr import IbkrBroker  # noqa: E402
from paper_trading.yahoo_data import fetch_daily  # noqa: E402

KEEP_CAD = 0.02  # fee buffer left in CAD
LOT = 1_000  # round the USD amount down to this
PLAUSIBLE_CAD_PER_USD = (1.0, 2.0)


def plan_usd_purchase(cash: dict[str, float], cad_per_usd: float) -> int:
    """USD to buy with CAD cash; 0 when USD is already held or there is no CAD."""
    low, high = PLAUSIBLE_CAD_PER_USD
    if not low <= cad_per_usd <= high:
        raise RuntimeError(f"{cad_per_usd} CAD per USD is outside {low}–{high}; refusing to convert")
    if cash.get("USD", 0.0) > 0 or cash.get("CAD", 0.0) <= 0:
        return 0
    usd = cash["CAD"] * (1 - KEEP_CAD) / cad_per_usd
    return math.floor(usd / LOT) * LOT


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    broker = IbkrBroker.connect()
    try:
        cash = broker.cash_by_currency()
        print(f"Account {broker.account_id} cash before: {cash}")
        cad_per_usd = float(fetch_daily("CAD=X", 10)["close"].iloc[-1])  # Yahoo: CAD per 1 USD
        usd = plan_usd_purchase(cash, cad_per_usd)
        if usd == 0:
            print("Nothing to convert (USD already held, or no CAD).")
            return 0
        print(f"Buying {usd:,} USD with CAD at ~{cad_per_usd:.4f} CAD/USD (market order, IDEALPRO)")
        result = broker.buy_usd_with_cad(usd)
        print(f"Order {result.order_id}: {result.status}, avg price {result.filled_avg_price}")
        broker.wait(5)
        print(f"Account cash after: {broker.cash_by_currency()}")
        return 0 if result.status in {"filled", "accepted"} else 1
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
