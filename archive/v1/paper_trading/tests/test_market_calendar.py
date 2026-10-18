from datetime import date, datetime, time, timezone

import pytest

from paper_trading.market_calendar import last_completed_session

REGULAR = [(date(2026, 10, 1), time(16, 0)), (date(2026, 10, 2), time(16, 0))]


def test_after_close_returns_today():
    now = datetime(2026, 10, 2, 20, 30, tzinfo=timezone.utc)  # 16:30 EDT
    assert last_completed_session(now, REGULAR) == date(2026, 10, 2)


def test_during_session_returns_previous_session():
    now = datetime(2026, 10, 2, 19, 0, tzinfo=timezone.utc)  # 15:00 EDT
    assert last_completed_session(now, REGULAR) == date(2026, 10, 1)


def test_late_gha_run_after_midnight_utc_keeps_session_date():
    now = datetime(2026, 10, 3, 0, 45, tzinfo=timezone.utc)  # 20:45 EDT 10-02
    assert last_completed_session(now, REGULAR) == date(2026, 10, 2)


def test_half_day_close_counts_after_1pm():
    sessions = [(date(2026, 11, 25), time(16, 0)), (date(2026, 11, 27), time(13, 0))]
    now = datetime(2026, 11, 27, 18, 30, tzinfo=timezone.utc)  # 13:30 EST
    assert last_completed_session(now, sessions) == date(2026, 11, 27)


def test_raises_when_no_session_completed():
    now = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(RuntimeError):
        last_completed_session(now, REGULAR)
