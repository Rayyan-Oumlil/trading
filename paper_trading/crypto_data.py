"""Daily crypto bars from Alpaca. A crypto 'day' is a UTC day; only completed days are used."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame

OHLCV = ["open", "high", "low", "close", "volume"]


def last_completed_day(now_utc: datetime) -> date:
    return now_utc.date() - timedelta(days=1)


def crypto_bars_to_frame(raw: pd.DataFrame, symbol: str, last_day: date) -> pd.DataFrame:
    df = raw.xs(symbol, level="symbol") if isinstance(raw.index, pd.MultiIndex) else raw
    df = df[OHLCV].copy()
    df.index = pd.DatetimeIndex(df.index.tz_convert("UTC").date)
    df = df[df.index.date <= last_day].dropna(subset=["close"])
    if df.empty or df.index[-1].date() != last_day:
        latest = df.index[-1].date() if not df.empty else None
        raise RuntimeError(f"{symbol} data stale: latest bar {latest}, expected {last_day}")
    return df


def get_crypto_daily_bars(symbol: str, lookback_days: int, last_day: date) -> pd.DataFrame:
    end = datetime.combine(last_day + timedelta(days=1), datetime.min.time()).replace(tzinfo=None)
    request = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=end - timedelta(days=lookback_days),
        end=end,
    )
    raw = CryptoHistoricalDataClient().get_crypto_bars(request).df
    if raw.empty:
        raise RuntimeError(f"Alpaca returned no bars for {symbol}")
    return crypto_bars_to_frame(raw, symbol, last_day)
