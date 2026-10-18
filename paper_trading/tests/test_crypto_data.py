from datetime import date

import numpy as np
import pandas as pd
import pytest

from paper_trading.crypto_data import crypto_bars_to_frame, last_completed_day


def _raw(days: list[str], closes: list[float], symbol: str = "BTC/USD") -> pd.DataFrame:
    idx = pd.MultiIndex.from_tuples([(symbol, pd.Timestamp(d, tz="UTC")) for d in days], names=["symbol", "timestamp"])
    return pd.DataFrame({"open": closes, "high": closes, "low": closes, "close": closes,
                         "volume": [1.0] * len(days)}, index=idx)


def test_last_completed_day_is_yesterday_utc():
    from datetime import datetime, timezone
    assert last_completed_day(datetime(2026, 10, 3, 0, 10, tzinfo=timezone.utc)) == date(2026, 10, 2)


def test_drops_in_progress_day():
    raw = _raw(["2026-10-01", "2026-10-02", "2026-10-03"], [1.0, 2.0, 3.0])
    df = crypto_bars_to_frame(raw, "BTC/USD", date(2026, 10, 2))
    assert list(df.index.date) == [date(2026, 10, 1), date(2026, 10, 2)]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_drops_nan_close():
    raw = _raw(["2026-10-01", "2026-10-02"], [1.0, 2.0])
    raw.iloc[0, raw.columns.get_loc("close")] = np.nan
    assert len(crypto_bars_to_frame(raw, "BTC/USD", date(2026, 10, 2))) == 1


def test_raises_when_latest_day_missing():
    with pytest.raises(RuntimeError, match="stale"):
        crypto_bars_to_frame(_raw(["2026-10-01"], [1.0]), "BTC/USD", date(2026, 10, 2))
