from datetime import date, datetime, timezone

from routines_pkg.send_report import evening, should_send


def test_late_cron_after_midnight_is_the_same_evening():
    on_time = datetime(2026, 10, 6, 0, 10, tzinfo=timezone.utc)  # Mon 20:10 EDT
    late = datetime(2026, 10, 6, 5, 20, tzinfo=timezone.utc)  # Tue 01:20 EDT
    assert evening(on_time) == evening(late) == date(2026, 10, 5)


def test_next_evening_sends_again():
    assert not should_send("2026-10-05\n", date(2026, 10, 5))
    assert should_send("2026-10-05\n", date(2026, 10, 6))
    assert should_send(None, date(2026, 10, 5))
