"""
The account's sleeves. One robot (run_signal.py) owns every order; each sleeve
only says "long or flat". See plans/2026-10-03-crypto-sleeve.md and
plans/2026-10-04-ibkr-paper.md (crypto now held through US spot ETFs).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from paper_trading.order_types import position_symbol


@dataclass(frozen=True)
class Sleeve:
    symbol: str  # what the robot buys (a US-listed ETF)
    weight: float  # fraction of account equity bought on a flat->long flip
    signal: str  # whose SMA(10/50) decides: the backtested series, not the ETF
    clock: str  # last bar the signal reads: "us_session" (stocks) or "utc_day" (crypto)


SLEEVES = (
    Sleeve("SPY", 0.855, "SPY", "us_session"),  # 90% sleeve x 95% invested (old 5% cash buffer kept)
    Sleeve("IBIT", 0.05, "BTC-USD", "utc_day"),  # iShares Bitcoin Trust
    Sleeve("ETHA", 0.05, "ETH-USD", "utc_day"),  # iShares Ethereum Trust
)
ALLOWED_POSITIONS = {position_symbol(s.symbol) for s in SLEEVES}
_NOT_A_DECISION = {"HALT"}
_ENTRY = re.compile(r"\d{4}-\d{2}-\d{2} \|.*?(?=\d{4}-\d{2}-\d{2} \||\n|$)")


def split_log_lines(text: str) -> list[str]:
    """Confidence-log entries, including ones glued together by the old multi writer."""
    return [m.group(0).strip() for m in _ENTRY.finditer(text)]


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
