"""Broker-neutral order vocabulary shared by every adapter and guard."""
from __future__ import annotations

from dataclasses import dataclass


def is_crypto(symbol: str) -> bool:
    return "/" in symbol


def position_symbol(symbol: str) -> str:
    """Alpaca orders use 'BTC/USD'; positions report 'BTCUSD'."""
    return symbol.replace("/", "")


@dataclass(frozen=True)
class OrderResult:
    order_id: str
    status: str
    filled_avg_price: float | None
