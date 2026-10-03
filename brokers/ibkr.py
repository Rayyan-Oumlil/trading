"""
Interactive Brokers execution adapter (IBKR Canada, via IB Gateway + ib_async).

Same methods as paper_trading.alpaca_client.AlpacaClient for everything
run_signal.py needs, so the robot can execute on either broker.

- US-listed equities/ETFs only. Canadian residents may not send API orders for
  Canadian-listed products (CIRO rule) — and we don't need them.
- Orders are market-on-open (MKT, TIF=OPG): the robot runs after the close and
  the backtests fill at the next open.
- Whole shares only: fractional API orders are not verified yet.
- Account values are reported in USD: the account's base currency is CAD,
  orders are priced in USD, and only USD cash can pay for them.
- Crypto sleeves are refused until the crypto-via-ETF test (roadmap idea 0) passes.
"""
from __future__ import annotations

import math
import os
from datetime import date, time
from pathlib import Path
from typing import Callable

from ib_async import IB, MarketOrder, Stock

from paper_trading.alpaca_client import OrderResult, is_crypto

ARMED_FILE = Path(__file__).resolve().parents[1] / "live-trading" / "ARMED"
PAPER_PREFIXES = ("DU", "DF")  # IBKR paper account ids
SETTLE_SECONDS = 2.0  # let IB report the first order status (or a rejection) before we read it
_STATUS = {  # IB order states -> the vocabulary paper_trading.guards understands
    "PendingSubmit": "pending_new",
    "ApiPending": "pending_new",
    "PreSubmitted": "accepted",
    "Submitted": "accepted",
    "ApiUpdate": "accepted",
    "Filled": "filled",
    "Cancelled": "canceled",
    "ApiCancelled": "canceled",
    "Inactive": "rejected",
    "ValidationError": "rejected",
}

CalendarSource = Callable[[date, date], list[tuple[date, time]]]


def check_live_gate(account_id: str, live_flag: str | None, armed: bool) -> None:
    """Paper accounts always pass. A LIVE account needs LIVE_TRADING=1 AND the live-trading/ARMED file."""
    if account_id.startswith(PAPER_PREFIXES):
        return
    if live_flag != "1" or not armed:
        raise RuntimeError(
            f"{account_id} is a LIVE IBKR account. Refusing to trade: needs LIVE_TRADING=1 and live-trading/ARMED "
            "(see plans/2026-10-03-roadmap-to-live.md §5–§6)."
        )


class IbkrBroker:
    def __init__(self, ib: IB, calendar_source: CalendarSource) -> None:
        self._ib = ib
        self._calendar = calendar_source

    @classmethod
    def connect(cls, calendar_source: CalendarSource) -> "IbkrBroker":
        """Connect to a running IB Gateway. Paper Gateway listens on 4002 by default."""
        ib = IB()
        ib.connect(
            os.environ.get("IBKR_HOST", "127.0.0.1"),
            int(os.environ.get("IBKR_PORT", "4002")),
            clientId=int(os.environ.get("IBKR_CLIENT_ID", "17")),
            timeout=15,
        )
        account_id = ib.managedAccounts()[0]
        try:
            check_live_gate(account_id, os.environ.get("LIVE_TRADING"), ARMED_FILE.exists())
        except RuntimeError:
            ib.disconnect()
            raise
        return cls(ib, calendar_source)

    def supports(self, symbol: str) -> bool:
        return not is_crypto(symbol)

    def get_calendar(self, start: date, end: date) -> list[tuple[date, time]]:
        return self._calendar(start, end)

    def get_account(self) -> dict:
        values = self._ib.accountValues()
        rates = {v.currency: float(v.value) for v in values if v.tag == "ExchangeRate"}  # base units per 1 currency
        net = next((v for v in values if v.tag == "NetLiquidation" and v.currency != "BASE"), None)
        if net is None or "USD" not in rates:
            raise RuntimeError("IBKR account values lack NetLiquidation or the USD exchange rate")
        usd_cash = next((float(v.value) for v in values if v.tag == "TotalCashValue" and v.currency == "USD"), 0.0)
        return {
            "status": "ACTIVE",
            "equity": float(net.value) * rates.get(net.currency, 1.0) / rates["USD"],
            "cash": usd_cash,
            "buying_power": usd_cash,
        }

    def get_positions(self) -> list[dict]:
        return [
            {
                "symbol": p.contract.symbol,
                "qty": float(p.position),
                "market_value": float(p.marketValue),
                "unrealized_pl": float(p.unrealizedPNL),
            }
            for p in self._ib.portfolio()
            if p.position
        ]

    def get_open_orders(self) -> list[dict]:
        return [
            {"symbol": t.contract.symbol, "side": t.order.action.lower(), "qty": float(t.order.totalQuantity)}
            for t in self._ib.openTrades()
        ]

    def has_open_order(self, symbol: str) -> bool:
        return any(o["symbol"] == symbol for o in self.get_open_orders())

    def place_market_order(self, symbol: str, qty: float, side: str) -> OrderResult:
        if is_crypto(symbol):
            raise NotImplementedError(f"{symbol}: crypto on IBKR waits for the crypto-via-ETF test (roadmap idea 0)")
        if side.lower() not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        shares = math.floor(qty)
        if shares < 1:
            raise RuntimeError(f"{symbol}: {qty} is less than one share — the IBKR adapter trades whole shares only")
        contract = Stock(symbol, "SMART", "USD")
        self._ib.qualifyContracts(contract)
        trade = self._ib.placeOrder(contract, MarketOrder(side.upper(), shares, tif="OPG"))
        self._ib.sleep(SETTLE_SECONDS)
        return _result(trade)

    def place_notional_buy(self, symbol: str, notional: float) -> OrderResult:
        raise NotImplementedError(f"{symbol}: crypto on IBKR waits for the crypto-via-ETF test (roadmap idea 0)")


def _result(trade) -> OrderResult:
    status = trade.orderStatus.status
    price = trade.orderStatus.avgFillPrice
    return OrderResult(
        order_id=str(trade.order.orderId),
        status=_STATUS.get(status, status.lower()),
        filled_avg_price=float(price) if price else None,
    )
