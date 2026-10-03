"""
Deterministic brake. Runs on GitHub right after the desk snapshot.

Any "halt" flag in memory/desk-snapshot.json that is not listed under
Acknowledged in memory/desk-notes.md writes .HALT (robot stops next run) and
texts Rayyan. No AI involved. Clearing .HALT is always a human decision.

Usage: python -m routines_pkg.auto_halt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from paper_trading.kill_switch import create_halt, is_halted  # noqa: E402
from paper_trading.notify import send_telegram  # noqa: E402

SNAPSHOT_FILE = PROJECT_ROOT / "memory" / "desk-snapshot.json"
NOTES_FILE = PROJECT_ROOT / "memory" / "desk-notes.md"


def unacknowledged_halts(snapshot: dict, notes_text: str) -> list[dict]:
    acked = {
        tuple(part.strip() for part in line.lstrip("- ").split("|")[:2])
        for line in notes_text.splitlines()
        if line.startswith("- ") and line.count("|") >= 2
    }
    return [
        f for f in snapshot["flags"]
        if f["severity"] == "halt" and (f["code"], snapshot["session"]) not in acked
    ]


def halt_message(session: str, flags: list[dict]) -> str:
    lines = [f"🔴 HALTED after session {session} — the robot will not trade until you clear .HALT."]
    lines += [f"• {f['code']}: {f['detail']}" for f in flags]
    lines.append("To resume: fix or acknowledge (memory/desk-notes.md), then delete .HALT and push.")
    return "\n".join(lines)


def main() -> int:
    snapshot = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    fired = unacknowledged_halts(snapshot, NOTES_FILE.read_text(encoding="utf-8"))
    if not fired:
        print("No unacknowledged halt flags.")
        return 0
    if is_halted():
        print("Already halted; not re-alerting.")
        return 0
    message = halt_message(snapshot["session"], fired)
    create_halt("; ".join(f"{f['code']}: {f['detail']}" for f in fired))
    print(message)
    send_telegram(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
