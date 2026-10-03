"""Hard pre/post-trade checks. Each one raises or returns a bool — never logs and continues."""
from __future__ import annotations

from paper_trading.alpaca_client import position_symbol

_FAILED = {"rejected", "canceled", "expired", "suspended"}


def order_failed(status: str) -> bool:
    return status.lower().rsplit(".", 1)[-1] in _FAILED


def assert_only_expected_positions(positions: list[dict], allowed: set[str], open_orders: list[dict] = ()) -> None:
    """Raise on any position outside `allowed`, unless an open sell order covers its full quantity (wind-down)."""
    selling: dict[str, float] = {}
    for o in open_orders:
        if o["side"] == "sell":
            sym = position_symbol(o["symbol"])  # orders say BTC/USD, positions say BTCUSD
            selling[sym] = selling.get(sym, 0.0) + o["qty"]
    foreign = sorted(
        p["symbol"] for p in positions
        if p["symbol"] not in allowed and selling.get(p["symbol"], 0.0) < p.get("qty", float("inf"))
    )
    if foreign:
        raise RuntimeError(f"Unexpected positions {foreign}: another strategy or a manual trade is in this account")
