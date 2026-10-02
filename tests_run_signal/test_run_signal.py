import math
from datetime import date, time

import numpy as np
import pandas as pd
import pytest

import run_signal
from paper_trading.alpaca_client import OrderResult


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



class FakeClient:
    def __init__(self, positions=(), open_order=False, status="OrderStatus.ACCEPTED"):
        self.positions = list(positions)
        self.open_order = open_order
        self.status = status
        self.orders: list[tuple[str, float, str]] = []

    def get_calendar(self, start, end):
        return [(date(2026, 10, 1), time(16, 0)), (date(2026, 10, 2), time(16, 0))]

    def get_account(self):
        return {"status": "ACTIVE", "equity": 100_000.0, "buying_power": 100_000.0, "cash": 100_000.0}

    def get_positions(self):
        return self.positions

    def has_open_order(self, symbol):
        return self.open_order

    def place_market_order(self, symbol, qty, side):
        self.orders.append((symbol, qty, side))
        return OrderResult(order_id="o-1", status=self.status, filled_avg_price=None)


@pytest.fixture
def wired(monkeypatch, tmp_path):
    def _wire(client):
        log = tmp_path / "confidence-log.md"
        monkeypatch.setattr(run_signal, "CONFIDENCE_LOG", log)
        monkeypatch.setattr(run_signal, "is_halted", lambda: False)
        monkeypatch.setattr(run_signal, "AlpacaClient", lambda: client)
        monkeypatch.setattr(run_signal, "get_daily_bars", lambda symbol, lookback_days, last_session: _bars())
        return log
    return _wire


def test_main_buys_and_dates_log_by_session(wired):
    client = FakeClient()
    log = wired(client)
    assert run_signal.main() == 0
    assert client.orders and client.orders[0][2] == "buy"
    assert log.read_text().startswith("2026-10-02 | BUY |")


def test_main_skips_duplicate_run_when_order_pending(wired):
    client = FakeClient(open_order=True)
    log = wired(client)
    assert run_signal.main() == 0
    assert client.orders == []
    assert "| PENDING |" in log.read_text()


def test_main_raises_on_rejected_order(wired):
    wired(FakeClient(status="OrderStatus.REJECTED"))
    with pytest.raises(RuntimeError, match="REJECTED"):
        run_signal.main()


def test_main_refuses_foreign_positions(wired):
    client = FakeClient(positions=[{"symbol": "GLD", "qty": 1.0, "market_value": 1.0, "unrealized_pl": 0.0}])
    wired(client)
    with pytest.raises(RuntimeError, match="GLD"):
        run_signal.main()
    assert client.orders == []


def test_run_just_after_close_uses_previous_session_not_partial_bar(wired, monkeypatch):
    from datetime import datetime, timezone

    class JustAfterClose(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 2, 20, 10, tzinfo=timezone.utc)  # 16:10 EDT, inside SIP delay

    seen = {}

    def fake_bars(symbol, lookback_days, last_session):
        seen["session"] = last_session
        return _bars()

    wired(FakeClient())
    monkeypatch.setattr(run_signal, "datetime", JustAfterClose)
    monkeypatch.setattr(run_signal, "get_daily_bars", fake_bars)
    run_signal.main()
    assert seen["session"] == date(2026, 10, 1)
