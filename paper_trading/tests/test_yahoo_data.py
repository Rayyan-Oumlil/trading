from datetime import date, datetime, timezone

import pandas as pd
import pytest

from paper_trading.yahoo_data import last_completed_session, through, to_frame

DATES = pd.DatetimeIndex(["2026-10-01", "2026-10-02", "2026-10-05"])


def test_today_bar_is_partial_until_after_the_close():
    during = datetime(2026, 10, 5, 18, 0, tzinfo=timezone.utc)  # 14:00 EDT
    after = datetime(2026, 10, 6, 0, 10, tzinfo=timezone.utc)  # 20:10 EDT
    assert last_completed_session(DATES, during) == date(2026, 10, 2)
    assert last_completed_session(DATES, after) == date(2026, 10, 5)


def test_weekend_run_uses_friday():
    saturday = datetime(2026, 10, 4, 0, 20, tzinfo=timezone.utc)
    assert last_completed_session(DATES[:2], saturday) == date(2026, 10, 2)


def test_stale_data_raises():
    with pytest.raises(RuntimeError, match="stale"):
        last_completed_session(DATES[:2], datetime(2026, 10, 12, 0, 20, tzinfo=timezone.utc))


def test_through_requires_the_expected_last_bar():
    df = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=DATES)
    assert len(through(df, date(2026, 10, 2), "SPY")) == 2
    with pytest.raises(RuntimeError, match="stale"):
        through(df, date(2026, 10, 3), "SPY")


def test_to_frame_keeps_exchange_local_dates():
    idx = pd.DatetimeIndex(["2026-10-02 00:00:00-04:00"]).tz_convert("America/New_York")
    raw = pd.DataFrame({c: [1.0] for c in ["Open", "High", "Low", "Close", "Volume", "Dividends"]}, index=idx)
    df = to_frame(raw)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index[0] == pd.Timestamp("2026-10-02")
