from datetime import date

import numpy as np
import pandas as pd
import pytest

from paper_trading.market_data import bars_to_frame


def _raw(days: list[str], closes: list[float]) -> pd.DataFrame:
    # Alpaca stamps daily bars at midnight New York (04:00 UTC during EDT).
    idx = pd.MultiIndex.from_tuples(
        [("SPY", pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=4)) for d in days],
        names=["symbol", "timestamp"],
    )
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes,
         "volume": [1_000.0] * len(days), "trade_count": [1.0] * len(days), "vwap": closes},
        index=idx,
    )


def test_drops_partial_session_after_last_completed():
    raw = _raw(["2026-09-30", "2026-10-01", "2026-10-02"], [760.0, 764.0, 769.0])
    df = bars_to_frame(raw, "SPY", date(2026, 10, 1))
    assert list(df.index.date) == [date(2026, 9, 30), date(2026, 10, 1)]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_drops_nan_close_rows():
    raw = _raw(["2026-09-30", "2026-10-01"], [760.0, 764.0])
    raw.iloc[0, raw.columns.get_loc("close")] = np.nan
    df = bars_to_frame(raw, "SPY", date(2026, 10, 1))
    assert len(df) == 1


def test_raises_when_latest_session_missing():
    raw = _raw(["2026-09-30"], [760.0])
    with pytest.raises(RuntimeError, match="stale"):
        bars_to_frame(raw, "SPY", date(2026, 10, 1))
