"""1-minute regular-session bars from Alpaca SIP (data-only key), cached per symbol-year."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
CACHE = Path(__file__).resolve().parent / "cache"  # gitignored: ~100 MB
FIRST_YEAR = 2016


def _download(symbol: str, year: int) -> pd.DataFrame:
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    client = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_API_SECRET"])
    end = min(pd.Timestamp(f"{year + 1}-01-01", tz="UTC"), pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=20))
    raw = client.get_stock_bars(StockBarsRequest(
        symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, start=pd.Timestamp(f"{year}-01-01", tz="UTC"),
        end=end, feed=DataFeed.SIP, adjustment=Adjustment.RAW,
    )).df
    df = raw.xs(symbol, level="symbol")[["open", "high", "low", "close", "volume"]]
    df.index = df.index.tz_convert("America/New_York")
    t = df.index.time
    return df[(t >= pd.Timestamp("09:30").time()) & (t < pd.Timestamp("16:00").time())]


def load(symbol: str) -> pd.DataFrame:
    """All regular-session minutes, FIRST_YEAR → now. Past years are cached; the current year is refreshed."""
    CACHE.mkdir(exist_ok=True)
    frames = []
    this_year = pd.Timestamp.now().year
    for year in range(FIRST_YEAR, this_year + 1):
        path = CACHE / f"{symbol}-{year}.pkl"
        if path.exists() and year < this_year:
            frames.append(pd.read_pickle(path))
            continue
        print(f"  downloading {symbol} {year}…", file=sys.stderr)
        df = _download(symbol, year)
        df.to_pickle(path)
        frames.append(df)
    return pd.concat(frames)


def by_day(df: pd.DataFrame) -> dict[pd.Timestamp, pd.DataFrame]:
    """Full 390-minute grid per session (bar start 09:30…15:59), forward-filled; zero volume on filled minutes."""
    out = {}
    for day, g in df.groupby(df.index.date):
        # Localize 09:30 itself: midnight + 9h30 lands on 10:30 on the spring DST day.
        grid = pd.date_range(pd.Timestamp(f"{day} 09:30").tz_localize("America/New_York"), periods=390, freq="min")
        g = g.reindex(grid)
        prices = ["open", "high", "low", "close"]
        g[prices] = g[prices].ffill().bfill()  # bfill only touches a missing 09:30 bar
        g["volume"] = g["volume"].fillna(0.0)
        if g["close"].isna().any() or g["volume"].sum() == 0:
            continue
        out[pd.Timestamp(day)] = g
    return out
