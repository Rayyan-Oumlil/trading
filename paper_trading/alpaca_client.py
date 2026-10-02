"""Thin wrapper around alpaca-py for paper trading operations."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, time

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetCalendarRequest, GetOrdersRequest, MarketOrderRequest

_VALID_SIDES = {"buy", "sell"}


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
            time_in_force=TimeInForce.DAY,
        )
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

    def has_open_order(self, symbol: str) -> bool:
        orders = self._client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol]))
        return len(orders) > 0
