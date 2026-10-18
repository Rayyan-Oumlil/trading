"""
Daily bars from Yahoo Finance (yfinance), split-and-dividend adjusted.

US symbols: one bar per NYSE session; today's bar only counts once the session
has closed. Crypto (BTC-USD): one bar per UTC day; only completed days count.
Holidays need no calendar: a closed exchange simply has no bar.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

NEW_YORK = ZoneInfo("America/New_York")
SESSION_FINAL = time(16, 30)  # Yahoo's daily bar is final a few minutes after the 16:00 close
MAX_SESSION_GAP = timedelta(days=5)  # longest real gap: holiday + weekend
OHLCV = ["open", "high", "low", "close", "volume"]


def fetch_daily(symbol: str, lookback_days: int) -> pd.DataFrame:
    raw = yf.Ticker(symbol).history(period=f"{lookback_days}d", interval="1d", auto_adjust=True)
    if raw.empty:
        raise RuntimeError(f"Yahoo returned no bars for {symbol}")
    return to_frame(raw)


def to_frame(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns=str.lower)[OHLCV].copy()
    df.index = pd.DatetimeIndex(df.index.date)  # exchange-local date (NY for US, UTC for crypto)
    return df


def last_completed_session(bar_dates: pd.DatetimeIndex, now_utc: datetime) -> date:
    """Latest session whose bar is final. Raises if the data is stale."""
    now_ny = now_utc.astimezone(NEW_YORK)
    today = now_ny.date()
    final = [d.date() for d in bar_dates if d.date() < today or (d.date() == today and now_ny.time() >= SESSION_FINAL)]
    if not final:
        raise RuntimeError(f"No completed session in data as of {now_ny.isoformat()}")
    session = max(final)
    if today - session > MAX_SESSION_GAP:
        raise RuntimeError(f"Data stale: latest completed session {session}, today {today}")
    return session


def last_completed_day(now_utc: datetime) -> date:
    return now_utc.date() - timedelta(days=1)


def through(df: pd.DataFrame, last_day: date, symbol: str) -> pd.DataFrame:
    """Bars up to last_day, which must itself be present (no silent use of an older bar)."""
    out = df[df.index.date <= last_day].dropna(subset=["close"])
    if out.empty or out.index[-1].date() != last_day:
        latest = out.index[-1].date() if not out.empty else None
        raise RuntimeError(f"{symbol} data stale: latest bar {latest}, expected {last_day}")
    return out
