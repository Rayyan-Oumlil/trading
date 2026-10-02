"""Trading-session dates from the exchange calendar, not the UTC wall clock."""
from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")


def last_completed_session(now_utc: datetime, sessions: list[tuple[date, time]]) -> date:
    completed = [d for d, close in sessions if datetime.combine(d, close, tzinfo=NEW_YORK) <= now_utc]
    if not completed:
        raise RuntimeError(f"No completed session at {now_utc.isoformat()} in calendar window")
    return max(completed)
