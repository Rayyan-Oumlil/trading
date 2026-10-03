"""
The account's sleeves. One robot (run_signal.py) owns every order; each sleeve
only says "long or flat". See plans/2026-10-03-crypto-sleeve.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from paper_trading.alpaca_client import position_symbol


@dataclass(frozen=True)
class Sleeve:
    symbol: str  # order symbol ("BTC/USD")
    weight: float  # fraction of account equity bought on a flat->long flip
    clock: str  # "us_session" (SPY) or "utc_day" (crypto)


SLEEVES = (
    Sleeve("SPY", 0.855, "us_session"),  # 90% sleeve x 95% invested (old 5% cash buffer kept)
    Sleeve("BTC/USD", 0.05, "utc_day"),
    Sleeve("ETH/USD", 0.05, "utc_day"),
)
ALLOWED_POSITIONS = {position_symbol(s.symbol) for s in SLEEVES}
_NOT_A_DECISION = {"HALT"}


def decide(want_long: bool, held_qty: float) -> str:
    """Trade only on a state flip; never rebalance drift (matches both backtests)."""
    if want_long:
        return "HOLD" if held_qty > 0 else "BUY"
    return "SELL" if held_qty > 0 else "FLAT"


def log_symbol(line: str) -> str | None:
    """Symbol a confidence-log line is about. Unprefixed lines predate sleeves and are SPY."""
    if "[multi]" in line:
        return None
    reason = line.split("|", 3)[-1].strip()
    head = reason.split(":", 1)[0]
    return head if any(head == s.symbol for s in SLEEVES) else "SPY"


def already_decided(log_lines: list[str], day: date, symbol: str) -> bool:
    for line in log_lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and parts[0] == day.isoformat() and parts[1] not in _NOT_A_DECISION:
            if log_symbol(line) == symbol:
                return True
    return False
