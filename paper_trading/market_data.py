"""Daily OHLCV from Alpaca (same vendor as the broker). Completed sessions only."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

SIP_DELAY = timedelta(minutes=16)  # free plan serves SIP data older than 15 min
OHLCV = ["open", "high", "low", "close", "volume"]


def bars_to_frame(raw: pd.DataFrame, symbol: str, last_session: date) -> pd.DataFrame:
    df = raw.xs(symbol, level="symbol") if isinstance(raw.index, pd.MultiIndex) else raw
    df = df[OHLCV].copy()
    df.index = pd.DatetimeIndex(df.index.tz_convert("America/New_York").date)
    df = df[df.index.date <= last_session].dropna(subset=["close"])
    if df.empty or df.index[-1].date() != last_session:
        latest = df.index[-1].date() if not df.empty else None
        raise RuntimeError(f"{symbol} data stale: latest bar {latest}, expected {last_session}")
    return df


def get_daily_bars(symbol: str, lookback_days: int, last_session: date) -> pd.DataFrame:
    client = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_API_SECRET"])
    end = datetime.now(timezone.utc) - SIP_DELAY
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=end - timedelta(days=lookback_days),
        end=end,
        feed=DataFeed.SIP,
        adjustment=Adjustment.ALL,
    )
    raw = client.get_stock_bars(request).df
    if raw.empty:
        raise RuntimeError(f"Alpaca returned no bars for {symbol}")
    return bars_to_frame(raw, symbol, last_session)
