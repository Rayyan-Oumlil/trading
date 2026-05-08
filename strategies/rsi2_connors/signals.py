"""RSI(2) Connors mean-reversion signal generator with 200-DMA regime filter.

Returns a new DataFrame — does not mutate input.

Spec: strategies/rsi2_connors/STRATEGY.md (literature defaults, no tuning).
"""
from __future__ import annotations

import pandas as pd


def wilder_rsi(close: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothed RSI (the textbook Connors uses).

    Parameters
    ----------
    close : Series of closing prices.
    period : RSI lookback (typically 2 for Connors).

    Returns
    -------
    Series of RSI values in [0, 100], NaN for the first `period` bars.
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    # Wilder's smoothing: an EMA with alpha = 1/period.
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    # When avg_loss is 0 (no down days in window) RSI is 100; pandas returns inf, clip it.
    rsi = rsi.where(~rsi.isna(), other=pd.NA)
    return rsi


def calculate_signals(
    df: pd.DataFrame,
    rsi_period: int = 2,
    oversold_threshold: float = 10.0,
    overbought_threshold: float = 70.0,
    regime_filter_period: int = 200,
    short_ma_exit: int = 5,
) -> pd.DataFrame:
    """
    Compute entry and exit signals for the RSI(2) Connors strategy.

    Entry rule (long_entry=True means: enter long at next-day open):
        rsi(2)[t] < oversold_threshold
        AND close[t] > sma(close, regime_filter_period)[t]
        AND volume[t] > 0

    Exit rule (long_exit=True means: exit at next-day open):
        rsi(2)[t] > overbought_threshold
        OR close[t] > sma(close, short_ma_exit)[t]

    Parameters
    ----------
    df : OHLCV DataFrame with columns [open, high, low, close, volume].
         Index must be a DatetimeIndex.

    Returns
    -------
    New DataFrame with original columns plus
    [rsi, sma_regime, sma_short, regime_ok, long_entry, long_exit].
    Does NOT mutate df.
    """
    out = df.copy()
    out["rsi"] = wilder_rsi(out["close"], rsi_period)
    out["sma_regime"] = out["close"].rolling(regime_filter_period).mean()
    out["sma_short"] = out["close"].rolling(short_ma_exit).mean()

    regime_ok = (out["close"] > out["sma_regime"]).fillna(False).astype(bool)
    out["regime_ok"] = regime_ok

    rsi_oversold = (out["rsi"] < oversold_threshold).fillna(False).astype(bool)
    rsi_overbought = (out["rsi"] > overbought_threshold).fillna(False).astype(bool)
    above_short_ma = (out["close"] > out["sma_short"]).fillna(False).astype(bool)
    volume_ok = (out["volume"] > 0).fillna(False).astype(bool)
    has_warmup = out["sma_regime"].notna() & out["rsi"].notna() & out["sma_short"].notna()

    out["long_entry"] = (rsi_oversold & regime_ok & volume_ok & has_warmup).astype(bool)
    out["long_exit"] = (rsi_overbought | above_short_ma).fillna(False).astype(bool)

    return out
