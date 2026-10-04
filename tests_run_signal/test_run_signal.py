import math
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
import pytest

import run_signal
from paper_trading.order_types import OrderResult

SESSION = date(2026, 10, 2)


def _bars(n: int = 80, last_close_nan: bool = False, end: str = "2026-10-02", price: float = 700) -> pd.DataFrame:
    idx = pd.bdate_range(end=end, periods=n)
    close = np.linspace(price, price * 1.1, n)
    df = pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": 1_000_000},
        index=idx,
    )
    if last_close_nan:
        df.iloc[-1, df.columns.get_loc("close")] = np.nan
    return df


def _daily(n: int = 80, end: str = "2026-10-03", falling: bool = False, price: float = 80_000) -> pd.DataFrame:
    idx = pd.date_range(end=end, periods=n, freq="D")
    close = np.linspace(price, price * 1.1, n)
    df = pd.DataFrame({"open": close, "high": close, "low": close, "close": close, "volume": 1.0}, index=idx)
    return df.assign(close=df["close"].values[::-1]) if falling else df


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
    def __init__(self, positions=(), open_order=False, status="accepted", cash=100_000.0):
        self.positions = list(positions)
        self.open_order = open_order
        self.status = status
        self.cash = cash
        self.orders: list[tuple[str, float, str]] = []
        self.open_orders: list[dict] = []
        self.disconnected = False
        self.account_id = "DUR239224"

    def get_account(self):
        return {"status": "ACTIVE", "equity": 100_000.0, "buying_power": self.cash, "cash": self.cash}

    def get_positions(self):
        return self.positions

    def has_open_order(self, symbol):
        return self.open_order

    def get_open_orders(self):
        return list(self.open_orders)

    def place_market_order(self, symbol, qty, side):
        self.orders.append((symbol, qty, side))
        return OrderResult(order_id="o-1", status=self.status, filled_avg_price=None)

    def disconnect(self):
        self.disconnected = True


PRICES = {"SPY": 700.0, "IBIT": 48.0, "ETHA": 20.0}
coin = {"falling": False}


@pytest.fixture(autouse=True)
def _rising_coins():
    coin["falling"] = False


class AfterClose(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 10, 3, 0, 20, tzinfo=timezone.utc)  # Fri 2 Oct, 20:20 EDT


@pytest.fixture
def wired(monkeypatch, tmp_path):
    def fake_fetch(symbol, lookback_days):
        if symbol.endswith("-USD"):
            return _daily(falling=coin["falling"])
        return _bars(price=PRICES[symbol])

    def _wire(client):
        log = tmp_path / "confidence-log-ibkr.md"
        monkeypatch.setattr(run_signal, "CONFIDENCE_LOG", log)
        monkeypatch.setattr(run_signal, "is_halted", lambda: False)
        monkeypatch.setattr(run_signal, "make_client", lambda: client)
        monkeypatch.setattr(run_signal, "fetch_daily", fake_fetch)
        monkeypatch.setattr(run_signal, "datetime", AfterClose)
        return log
    return _wire


def _last(symbol):
    return _bars(price=PRICES[symbol])["close"].iloc[-1]


def test_main_buys_whole_shares_and_dates_log_by_session(wired):
    client = FakeClient()
    log = wired(client)
    assert run_signal.main() == 0
    assert client.orders[0] == ("SPY", math.floor(100_000 * 0.855 / _last("SPY")), "buy")
    assert log.read_text().startswith("2026-10-02 | BUY |")
    assert client.disconnected


def test_crypto_etfs_buy_5pct_each_from_the_coin_signal(wired):
    client = FakeClient()
    log = wired(client)
    run_signal.main()
    assert ("IBIT", math.floor(5_000 / _last("IBIT")), "buy") in client.orders
    assert ("ETHA", math.floor(5_000 / _last("ETHA")), "buy") in client.orders
    assert "| BUY | 7/10 | IBIT:" in log.read_text()


def test_coin_downtrend_sells_the_etf(wired):
    coin["falling"] = True
    held = [{"symbol": "SPY", "qty": 100.0, "market_value": 1.0, "unrealized_pl": 0.0},
            {"symbol": "IBIT", "qty": 104.0, "market_value": 1.0, "unrealized_pl": 0.0}]
    client = FakeClient(positions=held)
    log = wired(client)
    run_signal.main()
    assert client.orders == [("IBIT", 104.0, "sell")]
    text = log.read_text()
    assert "| SELL | 6/10 | IBIT:" in text and "| FLAT | 5/10 | ETHA:" in text and "| HOLD | 7/10 | SPY:" in text


def test_coin_signal_uses_the_last_completed_utc_day(wired, monkeypatch):
    seen = []

    def fetch(symbol, lookback_days):
        seen.append(symbol)
        if symbol.endswith("-USD"):
            return _daily(end="2026-10-01")  # missing 2 Oct: stale
        return _bars(price=PRICES[symbol])

    wired(FakeClient())
    monkeypatch.setattr(run_signal, "fetch_daily", fetch)
    with pytest.raises(RuntimeError, match="BTC-USD data stale"):
        run_signal.main()


def test_main_skips_duplicate_run_when_order_pending(wired):
    client = FakeClient(open_order=True)
    log = wired(client)
    assert run_signal.main() == 0
    assert client.orders == []
    assert "| PENDING |" in log.read_text()


def test_main_raises_on_rejected_order_and_still_disconnects(wired):
    client = FakeClient(status="rejected")
    wired(client)
    with pytest.raises(RuntimeError, match="rejected"):
        run_signal.main()
    assert client.disconnected


def test_main_refuses_foreign_positions(wired):
    client = FakeClient(positions=[{"symbol": "GLD", "qty": 1.0, "market_value": 1.0, "unrealized_pl": 0.0}])
    wired(client)
    with pytest.raises(RuntimeError, match="GLD"):
        run_signal.main()
    assert client.orders == []


def test_second_run_same_day_places_nothing(wired):
    client = FakeClient()
    wired(client)
    run_signal.main()
    first = list(client.orders)
    run_signal.main()
    assert client.orders == first


def test_spy_buy_is_capped_at_usd_cash_and_says_so(wired):
    client = FakeClient(cash=50_000.0)
    log = wired(client)
    run_signal.main()
    spy = next(o for o in client.orders if o[0] == "SPY")
    assert spy[1] == math.floor(50_000 * 0.99 / _last("SPY"))
    assert "capped at USD cash" in log.read_text()


def test_no_usd_cash_tells_rayyan_to_convert(wired):
    wired(FakeClient(cash=0.0))
    with pytest.raises(RuntimeError, match="Convert CAD to USD"):
        run_signal.main()


def test_halt_places_nothing_and_never_connects(wired, monkeypatch):
    log = wired(FakeClient())
    monkeypatch.setattr(run_signal, "is_halted", lambda: True)
    monkeypatch.setattr(run_signal, "make_client", lambda: pytest.fail("connected while halted"))
    assert run_signal.main() == 0
    assert "| HALT |" in log.read_text()


def test_failed_buy_does_not_skip_another_sleeves_sell(wired):
    coin["falling"] = True
    held = [{"symbol": "IBIT", "qty": 104.0, "market_value": 1.0, "unrealized_pl": 0.0}]
    client = FakeClient(positions=held, cash=0.0)
    wired(client)
    with pytest.raises(RuntimeError, match="SPY: USD cash"):
        run_signal.main()
    assert ("IBIT", 104.0, "sell") in client.orders
