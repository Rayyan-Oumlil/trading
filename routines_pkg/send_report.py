"""
Send the daily Telegram report at most once per trading evening.

The robot can run twice an evening (Windows task + GitHub cron fallback); the
second run must stay silent. An evening runs noon-to-noon New York time, so a
cron run that slips past midnight still counts as the same evening.

If the robot failed (ROBOT_OK != "true") the report is still sent but the
evening is not marked done, so a successful rerun sends the complete one.

Usage: ROBOT_OK=true python -m routines_pkg.send_report <report-file>
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from paper_trading.notify import send_telegram  # noqa: E402
from paper_trading.yahoo_data import NEW_YORK  # noqa: E402

MARKER = PROJECT_ROOT / "memory" / "last-report.txt"


def evening(now_utc: datetime) -> date:
    return (now_utc.astimezone(NEW_YORK) - timedelta(hours=12)).date()


def should_send(marker_text: str | None, today: date) -> bool:
    return (marker_text or "").strip() != today.isoformat()


def main() -> int:
    today = evening(datetime.now(timezone.utc))
    marker = MARKER.read_text(encoding="utf-8") if MARKER.exists() else None
    if not should_send(marker, today):
        print(f"Report for the evening of {today} already sent; staying silent.")
        return 0
    send_telegram(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if os.environ.get("ROBOT_OK") == "true":
        MARKER.write_text(today.isoformat() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
