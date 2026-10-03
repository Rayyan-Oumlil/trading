"""Thin wrapper around alpaca-py for paper trading operations."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import (
    GetCalendarRequest,
    GetOrdersRequest,
    GetPortfolioHistoryRequest,
    MarketOrderRequest,
)

_VALID_SIDES = {"buy", "sell"}


def is_crypto(symbol: str) -> bool:
    return "/" in symbol


def position_symbol(symbol: str) -> str:
    """Alpaca orders use 'BTC/USD'; positions report 'BTCUSD'."""
    return symbol.replace("/", "")


def _time_in_force(symbol: str) -> TimeInForce:
    # Alpaca rejects DAY for crypto; equities keep DAY so after-hours orders queue for the next open.
    return TimeInForce.GTC if is_crypto(symbol) else TimeInForce.DAY


def _order_qty(order) -> float:
    # Notional (dollar-amount) orders come back with qty=None, even after filling.
    if order.qty is not None:
        return float(order.qty)
    return float(order.filled_qty or 0)


@dataclass(frozen=True)
class OrderResult:
    order_id: str
    status: str
    filled_avg_price: float | None


class AlpacaClient:
    """Stateless Alpaca paper trading client. Always paper=True."""

    def __init__(self) -> None:
        api_key = os.environ["ALPACA_API_KEY"]
        secret_key = os.environ["ALPACA_API_SECRET"]
        self._client = TradingClient(api_key, secret_key, paper=True)

    def get_account(self) -> dict:
        acc = self._client.get_account()
        return {
            "status": str(acc.status),
            "equity": float(acc.equity),
            "buying_power": float(acc.buying_power),
            "cash": float(acc.cash),
        }

    def place_market_order(
        self, symbol: str, qty: float, side: str
    ) -> OrderResult:
        if qty <= 0:
            raise ValueError("qty must be > 0")
        side_lc = side.lower()
        if side_lc not in _VALID_SIDES:
            raise ValueError(f"side must be one of {sorted(_VALID_SIDES)}")
        order_side = OrderSide.BUY if side_lc == "buy" else OrderSide.SELL
        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=_time_in_force(symbol),
        )
        return self._submit(req)

    def place_notional_buy(self, symbol: str, notional: float) -> OrderResult:
        if notional <= 0:
            raise ValueError("notional must be > 0")
        req = MarketOrderRequest(
            symbol=symbol,
            notional=round(notional, 2),
            side=OrderSide.BUY,
            time_in_force=_time_in_force(symbol),
        )
        return self._submit(req)

    def _submit(self, req: MarketOrderRequest) -> OrderResult:
        order = self._client.submit_order(req)
        filled_price: float | None = None
        if order.filled_avg_price is not None:
            filled_price = float(order.filled_avg_price)
        return OrderResult(
            order_id=str(order.id),
            status=str(order.status),
            filled_avg_price=filled_price,
        )

    def get_positions(self) -> list[dict]:
        positions = self._client.get_all_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
            }
            for p in positions
        ]

    def get_calendar(self, start: date, end: date) -> list[tuple[date, time]]:
        days = self._client.get_calendar(GetCalendarRequest(start=start, end=end))
        return [(d.date, d.close.time() if isinstance(d.close, datetime) else d.close) for d in days]

    def get_open_orders(self) -> list[dict]:
        orders = self._client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN))
        return [{"symbol": o.symbol, "side": o.side.value, "qty": _order_qty(o)} for o in orders]

    def has_open_order(self, symbol: str) -> bool:
        orders = self._client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol]))
        return len(orders) > 0

    def get_recent_orders(self, after: datetime) -> list[dict]:
        """All orders (any status) submitted after `after`. Read-only."""
        orders = self._client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, after=after, limit=500))
        return [
            {
                "symbol": o.symbol,
                "side": o.side.value,
                "status": o.status.value,
                "qty": _order_qty(o),
                "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
                "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
                "filled_at": o.filled_at.isoformat() if o.filled_at else None,
            }
            for o in orders
        ]

    def get_equity_history(self, period: str = "1A") -> list[tuple[date, float]]:
        """Daily account equity, dated by New York session. Read-only."""
        hist = self._client.get_portfolio_history(GetPortfolioHistoryRequest(period=period, timeframe="1D"))
        new_york = ZoneInfo("America/New_York")
        return [
            (datetime.fromtimestamp(ts, new_york).date(), float(eq))
            for ts, eq in zip(hist.timestamp, hist.equity)
            if eq
        ]
