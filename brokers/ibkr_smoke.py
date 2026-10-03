"""
Read-only IBKR connection check. NEVER places orders.

Prereq: IB Gateway running on this PC, logged into the PAPER account,
API socket enabled on port 4002 (see brokers/README.md).
Usage: python -m brokers.ibkr_smoke
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from brokers.ibkr import PAPER_PREFIXES, IbkrBroker  # noqa: E402
from paper_trading.alpaca_client import AlpacaClient  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    broker = IbkrBroker.connect(calendar_source=AlpacaClient().get_calendar)
    account_id = broker._ib.managedAccounts()[0]
    kind = "PAPER" if account_id.startswith(PAPER_PREFIXES) else "LIVE (armed)"
    account = broker.get_account()
    print(f"Connected: {account_id} [{kind}]")
    print(f"Equity (USD): {account['equity']:,.2f}   USD cash: {account['cash']:,.2f}")
    print(f"Positions:    {broker.get_positions() or 'none'}")
    print(f"Open orders:  {broker.get_open_orders() or 'none'}")
    if account["cash"] == 0:
        print("Note: no USD cash yet — convert CAD to USD in IBKR before the robot can buy SPY.")
    broker._ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
