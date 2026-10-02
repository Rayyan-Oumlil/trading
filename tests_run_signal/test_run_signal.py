import math

import numpy as np
import pandas as pd
import pytest

import run_signal


def _bars(n: int = 80, last_close_nan: bool = False) -> pd.DataFrame:
    idx = pd.bdate_range("2026-06-01", periods=n)
    close = np.linspace(700, 770, n)
    df = pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": 1_000_000},
        index=idx,
    )
    if last_close_nan:
        df.iloc[-1, df.columns.get_loc("close")] = np.nan
    return df


def test_clean_bars_drops_trailing_nan_row():
    cleaned = run_signal.clean_bars(_bars(last_close_nan=True))
    assert not cleaned["close"].isna().any()
    assert len(cleaned) == 79


def test_clean_bars_raises_when_too_few_bars():
    with pytest.raises(RuntimeError):
        run_signal.clean_bars(_bars(n=40))


def test_current_regime_is_finite_and_bullish_after_nan_row_dropped():
    sma_fast, sma_slow, long_ = run_signal.current_regime(run_signal.clean_bars(_bars(last_close_nan=True)))
    assert math.isfinite(sma_fast) and math.isfinite(sma_slow)
    assert long_ is True


def test_current_regime_refuses_nan_instead_of_reporting_bearish():
    with pytest.raises(RuntimeError):
        run_signal.current_regime(_bars(last_close_nan=True))
