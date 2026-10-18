"""MA crossover signal generator. Returns a new DataFrame — does not mutate input."""
from __future__ import annotations

import pandas as pd


def calculate_signals(
    df: pd.DataFrame,
    fast_period: int = 10,
    slow_period: int = 50,
    vix: pd.Series | None = None,
    vix_max: float | None = None,
) -> pd.DataFrame:
    """
    Compute entry signals for the MA crossover strategy.

    Parameters
    ----------
    df : OHLCV DataFrame with columns [open, high, low, close, volume].
         Index must be a DatetimeIndex.
    fast_period : lookback for fast SMA.
    slow_period : lookback for slow SMA.
    vix : optional daily VIX close series, indexed by date. When provided
          together with `vix_max`, signals only fire on bars where
          VIX[t] < vix_max (regime gate). The series is reindexed onto
          ``df.index`` and forward-filled to handle the rare missing day.
    vix_max : optional VIX threshold. Ignored unless `vix` is provided.

    Returns
    -------
    New DataFrame with original columns plus [sma_fast, sma_slow, signal]
    (and [vix, vix_ok] when the gate is active).
    signal=True means: enter long at next-day open.
    Does NOT mutate df.
    """
    out = df.copy()
    out["sma_fast"] = out["close"].rolling(fast_period).mean()
    out["sma_slow"] = out["close"].rolling(slow_period).mean()

    fast_above = (out["sma_fast"] > out["sma_slow"]).fillna(False).astype(bool)
    prev_fast_above = fast_above.shift(1, fill_value=False)

    cross_up = fast_above & ~prev_fast_above
    volume_ok = out["volume"] > 0
    has_both_smas = out["sma_fast"].notna() & out["sma_slow"].notna()

    raw_signal = cross_up & volume_ok & has_both_smas

    if vix is not None and vix_max is not None:
        vix_aligned = vix.reindex(out.index).ffill()
        out["vix"] = vix_aligned
        vix_ok = (vix_aligned < vix_max).fillna(False).astype(bool)
        out["vix_ok"] = vix_ok
        raw_signal = raw_signal & vix_ok

    out["signal"] = raw_signal.astype(bool)
    return out
