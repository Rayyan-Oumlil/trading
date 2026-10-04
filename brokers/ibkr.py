"""
Interactive Brokers execution adapter (IBKR Canada, via IB Gateway + ib_async).

The only broker run_signal.py trades through (Alpaca retired 2026-10-04).

- US-listed equities/ETFs only. Canadian residents may not send API orders for
  Canadian-listed products (CIRO rule; IBKR answers "API/CTCI orders for
  canadian stocks are not allowed").
- Orders are market-on-open (MKT, TIF=OPG): the robot runs after the close and
  the backtests fill at the next open.
- Whole shares only: fractional API orders are not verified yet.
- Account values are reported in USD: the account's base currency is CAD,
  orders are priced in USD, and only USD cash can pay for them.
- Crypto exposure goes through US spot ETFs (IBIT, ETHA), which are plain stocks here.
"""
from __future__ import annotations

import math
import os
import time
from pathlib import Path

from ib_async import IB, MarketOrder, Stock

from paper_trading.order_types import OrderResult

ARMED_FILE = Path(__file__).resolve().parents[1] / "live-trading" / "ARMED"
PAPER_PREFIXES = ("DU", "DF")  # IBKR paper account ids
SETTLE_SECONDS = 2.0  # let IB report the first order status (or a rejection) before we read it
SETTLE_MAX_SECONDS = 15.0  # keep waiting while the order is still in flight (PendingSubmit)
_IN_FLIGHT = {"PendingSubmit", "ApiPending"}
CONNECT_WAIT_SECONDS = 240  # a freshly started Gateway container needs a minute or two to log in
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
    def __init__(self, ib: IB) -> None:
        self._ib = ib

    @classmethod
    def connect(cls) -> "IbkrBroker":
        """Connect to a running IB Gateway (paper listens on 4002), retrying while it logs in."""
        ib = IB()
        wait = float(os.environ.get("IBKR_CONNECT_WAIT", CONNECT_WAIT_SECONDS))
        deadline = time.monotonic() + wait
        while True:
            try:
                ib.connect(
                    os.environ.get("IBKR_HOST", "127.0.0.1"),
                    int(os.environ.get("IBKR_PORT", "4002")),
                    clientId=int(os.environ.get("IBKR_CLIENT_ID", "17")),
                    timeout=20,
                    raiseSyncErrors=True,  # a half-synced login must not look like an empty account
                )
                if not ib.managedAccounts():
                    raise ConnectionError("Gateway connected but reports no account yet")
                break
            except (ConnectionError, OSError, TimeoutError) as exc:
                ib.disconnect()
                if time.monotonic() > deadline:
                    raise RuntimeError(f"IB Gateway not reachable after {wait:.0f}s: {exc!r}") from exc
                time.sleep(10)
        try:
            check_live_gate(ib.managedAccounts()[0], os.environ.get("LIVE_TRADING"), ARMED_FILE.exists())
        except RuntimeError:
            ib.disconnect()
            raise
        return cls(ib)

    @property
    def account_id(self) -> str:
        return self._ib.managedAccounts()[0]

    def disconnect(self) -> None:
        self._ib.disconnect()

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

    def get_fills(self) -> list[dict]:
        """Executions IB reports for this login (today's session), in the snapshot's order shape."""
        return [
            {
                "symbol": f.contract.symbol,
                "side": "buy" if f.execution.side == "BOT" else "sell",
                "qty": float(f.execution.shares),
                "status": "filled",
                "filled_avg_price": float(f.execution.price),
                "filled_at": f.time.isoformat(),
            }
            for f in self._ib.fills()
        ]

    def place_market_order(self, symbol: str, qty: float, side: str) -> OrderResult:
        if side.lower() not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        shares = math.floor(qty)
        if shares < 1:
            raise RuntimeError(f"{symbol}: {qty} is less than one share — the IBKR adapter trades whole shares only")
        contract = Stock(symbol, "SMART", "USD")
        if not self._ib.qualifyContracts(contract):
            raise RuntimeError(f"{symbol}: IBKR does not recognise this as a US stock/ETF")
        trade = self._ib.placeOrder(contract, MarketOrder(side.upper(), shares, tif="OPG"))
        waited = 0.0
        while True:
            self._ib.sleep(SETTLE_SECONDS)
            waited += SETTLE_SECONDS
            if trade.orderStatus.status not in _IN_FLIGHT or waited >= SETTLE_MAX_SECONDS:
                break
        if trade.orderStatus.status in _IN_FLIGHT:
            raise RuntimeError(f"{symbol}: order {trade.order.orderId} still unacknowledged after {waited:.0f}s")
        return _result(trade)


def _result(trade) -> OrderResult:
    status = trade.orderStatus.status
    price = trade.orderStatus.avgFillPrice
    return OrderResult(
        order_id=str(trade.order.orderId),
        status=_STATUS.get(status, status.lower()),
        filled_avg_price=float(price) if price else None,
    )
