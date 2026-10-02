"""Hard pre/post-trade checks. Each one raises or returns a bool — never logs and continues."""
from __future__ import annotations

_FAILED = {"rejected", "canceled", "expired", "suspended"}


def order_failed(status: str) -> bool:
    return status.lower().rsplit(".", 1)[-1] in _FAILED


def assert_only_expected_positions(positions: list[dict], allowed: set[str]) -> None:
    foreign = sorted(p["symbol"] for p in positions if p["symbol"] not in allowed)
    if foreign:
        raise RuntimeError(f"Unexpected positions {foreign}: another strategy or a manual trade is in this account")
