"""Tests for the Alpaca paper client wrapper."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from paper_trading.alpaca_client import AlpacaClient, OrderResult


class TestAlpacaClientInit:
    def test_raises_if_env_vars_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ALPACA_API_KEY", raising=False)
        monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
        with pytest.raises(KeyError):
            AlpacaClient()

    def test_paper_mode_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_API_SECRET", "test_secret")
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            AlpacaClient()
            mock_tc.assert_called_once_with("test_key", "test_secret", paper=True)


class TestGetAccount:
    def test_returns_dict_with_expected_keys(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        mock_account = MagicMock()
        mock_account.status = "ACTIVE"
        mock_account.buying_power = "95000.00"
        mock_account.equity = "100000.00"
        mock_account.cash = "50000.00"
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_account.return_value = mock_account
            client = AlpacaClient()
            result = client.get_account()
        assert result["status"] == "ACTIVE"
        assert result["equity"] == 100000.0
        assert result["buying_power"] == 95000.0
        assert result["cash"] == 50000.0


class TestPlaceMarketOrder:
    def test_returns_order_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        mock_order = MagicMock()
        mock_order.id = "order-123"
        mock_order.status = "accepted"
        mock_order.filled_avg_price = "450.00"
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.submit_order.return_value = mock_order
            client = AlpacaClient()
            result = client.place_market_order("SPY", qty=10, side="buy")
        assert isinstance(result, OrderResult)
        assert result.order_id == "order-123"
        assert result.status == "accepted"
        assert result.filled_avg_price == 450.0

    def test_rejects_zero_qty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("paper_trading.alpaca_client.TradingClient"):
            client = AlpacaClient()
            with pytest.raises(ValueError, match="qty must be > 0"):
                client.place_market_order("SPY", qty=0, side="buy")

    def test_rejects_invalid_side(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("paper_trading.alpaca_client.TradingClient"):
            client = AlpacaClient()
            with pytest.raises(ValueError, match="side must be"):
                client.place_market_order("SPY", qty=1, side="nonsense")


class TestGetPositions:
    def test_returns_empty_list_when_no_positions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_all_positions.return_value = []
            client = AlpacaClient()
            assert client.get_positions() == []

    def test_formats_positions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        mock_pos = MagicMock()
        mock_pos.symbol = "SPY"
        mock_pos.qty = "10"
        mock_pos.market_value = "4500.00"
        mock_pos.unrealized_pl = "50.00"
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_all_positions.return_value = [mock_pos]
            client = AlpacaClient()
            positions = client.get_positions()
        assert len(positions) == 1
        assert positions[0]["symbol"] == "SPY"
        assert positions[0]["qty"] == 10.0
        assert positions[0]["market_value"] == 4500.0


class TestGetCalendar:
    def test_returns_date_and_close_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from datetime import date, datetime, time
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        day = MagicMock()
        day.date = date(2026, 11, 27)
        day.close = datetime(2026, 11, 27, 13, 0)
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_calendar.return_value = [day]
            result = AlpacaClient().get_calendar(date(2026, 11, 20), date(2026, 11, 27))
        assert result == [(date(2026, 11, 27), time(13, 0))]


class TestHasOpenOrder:
    def test_true_when_open_order_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_orders.return_value = [MagicMock()]
            assert AlpacaClient().has_open_order("SPY") is True

    def test_false_when_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_orders.return_value = []
            assert AlpacaClient().has_open_order("SPY") is False


class TestReadOnlyHistory:
    def _client(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")

    def test_recent_orders_normalized(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from datetime import datetime, timezone
        from alpaca.trading.enums import OrderSide, OrderStatus
        self._client(monkeypatch)
        o = MagicMock()
        o.symbol, o.side, o.status = "SPY", OrderSide.BUY, OrderStatus.FILLED
        o.qty, o.filled_qty, o.filled_avg_price = "125.05", "125.05", "772.66"
        o.submitted_at = datetime(2026, 9, 23, 8, 0, tzinfo=timezone.utc)
        o.filled_at = datetime(2026, 9, 23, 13, 31, tzinfo=timezone.utc)
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_orders.return_value = [o]
            [row] = AlpacaClient().get_recent_orders(after=datetime(2026, 9, 20, tzinfo=timezone.utc))
        assert row == {"symbol": "SPY", "side": "buy", "status": "filled", "qty": 125.05,
                       "filled_avg_price": 772.66, "submitted_at": "2026-09-23T08:00:00+00:00",
                       "filled_at": "2026-09-23T13:31:00+00:00"}

    def test_equity_history_skips_empty_points(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from datetime import date
        self._client(monkeypatch)
        hist = MagicMock()
        hist.timestamp = [1782360000, 1782446400]  # 2026-06-25, 2026-06-26 04:00 UTC
        hist.equity = [None, 103000.0]
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_portfolio_history.return_value = hist
            assert AlpacaClient().get_equity_history() == [(date(2026, 6, 26), 103000.0)]


class TestCryptoOrders:
    def _setup(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        order = MagicMock()
        order.id, order.status, order.filled_avg_price = "o-1", "accepted", None
        return order

    def test_crypto_order_uses_gtc_equity_uses_day(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from alpaca.trading.enums import TimeInForce
        order = self._setup(monkeypatch)
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.submit_order.return_value = order
            client = AlpacaClient()
            client.place_market_order("BTC/USD", qty=0.01, side="sell")
            client.place_market_order("SPY", qty=1, side="buy")
            reqs = [c.args[0] for c in mock_tc.return_value.submit_order.call_args_list]
        assert reqs[0].time_in_force == TimeInForce.GTC
        assert reqs[1].time_in_force == TimeInForce.DAY

    def test_notional_buy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        order = self._setup(monkeypatch)
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.submit_order.return_value = order
            client = AlpacaClient()
            result = client.place_notional_buy("ETH/USD", 5172.38)
            req = mock_tc.return_value.submit_order.call_args.args[0]
            with pytest.raises(ValueError, match="notional must be > 0"):
                client.place_notional_buy("ETH/USD", 0)
        assert req.notional == 5172.38 and req.symbol == "ETH/USD"
        assert result.order_id == "o-1"


def test_position_symbol_strips_crypto_slash():
    from paper_trading.alpaca_client import position_symbol
    assert position_symbol("BTC/USD") == "BTCUSD"
    assert position_symbol("SPY") == "SPY"


def test_get_open_orders_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    from alpaca.trading.enums import OrderSide
    monkeypatch.setenv("ALPACA_API_KEY", "k")
    monkeypatch.setenv("ALPACA_API_SECRET", "s")
    o = MagicMock()
    o.symbol, o.side, o.qty = "GLD", OrderSide.SELL, "6.62"
    with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
        mock_tc.return_value.get_orders.return_value = [o]
        assert AlpacaClient().get_open_orders() == [{"symbol": "GLD", "side": "sell", "qty": 6.62}]
