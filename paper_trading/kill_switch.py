"""Kill switch: halt trading by creating a .HALT file in the project root.

The project root is detected relative to this file so the kill switch behaves
consistently whether it's invoked from a routine cwd or directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HALT_FILE = PROJECT_ROOT / ".HALT"


def is_halted() -> bool:
    return HALT_FILE.exists()


def create_halt(reason: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    HALT_FILE.write_text(f"HALTED at {timestamp}\nReason: {reason}\n")


def remove_halt() -> None:
    if HALT_FILE.exists():
        HALT_FILE.unlink()


def halt_reason() -> str | None:
    if not HALT_FILE.exists():
        return None
    return HALT_FILE.read_text()
