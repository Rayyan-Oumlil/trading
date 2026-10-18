"""Unit tests for MA crossover signal function."""
from __future__ import annotations

import pandas as pd
import pytest

from strategies.ma_crossover.signals import calculate_signals


def _make_ohlcv(closes: list[float]) -> pd.DataFrame:
    """Build minimal OHLCV dataframe from a list of close prices."""
    n = len(closes)
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c * 1.01 for c in closes],
            "low": [c * 0.99 for c in closes],
            "close": closes,
            "volume": [1_000_000] * n,
        },
        index=pd.date_range("2020-01-01", periods=n, freq="D"),
    )


class TestCalculateSignals:
    def test_returns_dataframe_with_required_columns(self) -> None:
        df = _make_ohlcv([100.0] * 60)
        result = calculate_signals(df)
        assert "sma_fast" in result.columns
        assert "sma_slow" in result.columns
        assert "signal" in result.columns

    def test_signal_is_boolean(self) -> None:
        df = _make_ohlcv([100.0] * 60)
        result = calculate_signals(df)
        assert result["signal"].dtype == bool

    def test_no_signal_before_slow_period_bars(self) -> None:
        df = _make_ohlcv(list(range(1, 61)))
        result = calculate_signals(df)
        assert not result["signal"].iloc[:49].any()

    def test_rising_cross_produces_signal(self) -> None:
        closes = [100.0] * 50 + [110.0 + i for i in range(10)]
        df = _make_ohlcv(closes)
        result = calculate_signals(df)
        assert result["signal"].iloc[50:].any()

    def test_no_signal_when_fast_already_above_slow(self) -> None:
        closes = list(range(100, 170))
        df = _make_ohlcv([float(c) for c in closes])
        result = calculate_signals(df)
        assert result["signal"].sum() <= 2

    def test_zero_volume_bars_suppressed(self) -> None:
        closes = [100.0] * 50 + [110.0 + i for i in range(10)]
        df = _make_ohlcv(closes)
        df.loc[df.index[55], "volume"] = 0
        result = calculate_signals(df)
        assert not bool(result["signal"].iloc[55])

    def test_immutability(self) -> None:
        closes = [100.0] * 60
        df = _make_ohlcv(closes)
        original_close = df["close"].copy()
        calculate_signals(df)
        pd.testing.assert_series_equal(df["close"], original_close)

    def test_custom_periods(self) -> None:
        closes = [100.0] * 30 + [110.0 + i for i in range(15)]
        df = _make_ohlcv(closes)
        result = calculate_signals(df, fast_period=5, slow_period=20)
        assert result["signal"].any()
