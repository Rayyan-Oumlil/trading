from types import SimpleNamespace

import pytest
from ib_async import AccountValue, OrderStatus, PortfolioItem, Stock, Trade

from brokers.ibkr import IbkrBroker
from paper_trading.guards import order_failed

ACCT = "DU123"


def _values(net_cad="13700", usd_rate="1.37", usd_cash="2500"):
    vals = [
        AccountValue(ACCT, "NetLiquidation", net_cad, "CAD", ""),
        AccountValue(ACCT, "ExchangeRate", "1.00", "CAD", ""),
        AccountValue(ACCT, "ExchangeRate", usd_rate, "USD", ""),
        AccountValue(ACCT, "TotalCashValue", "13700", "BASE", ""),
    ]
    if usd_cash is not None:
        vals.append(AccountValue(ACCT, "TotalCashValue", usd_cash, "USD", ""))
    return vals


class FakeIB:
    def __init__(self, values=(), portfolio=(), trades=(), status="PreSubmitted"):
        self._values, self._portfolio, self._trades = list(values), list(portfolio), list(trades)
        self.status = status
        self.placed = []

    def accountValues(self):
        return self._values

    def portfolio(self):
        return self._portfolio

    def openTrades(self):
        return self._trades

    def qualifyContracts(self, *contracts):
        return [] if contracts[0].symbol == "NOPE" else list(contracts)

    def placeOrder(self, contract, order):
        order.orderId = 7
        self.placed.append((contract, order))
        return Trade(contract=contract, order=order, orderStatus=OrderStatus(orderId=7, status=self.status))

    def sleep(self, seconds):
        pass


def _broker(ib):
    return IbkrBroker(ib)


def test_account_is_converted_to_usd_and_uses_only_usd_cash():
    acct = _broker(FakeIB(values=_values())).get_account()
    assert acct["equity"] == pytest.approx(10_000.0)  # 13 700 CAD / 1.37
    assert acct["cash"] == 2_500.0  # CAD cash cannot buy SPY until converted


def test_no_usd_cash_means_zero_buying_cash():
    assert _broker(FakeIB(values=_values(usd_cash=None))).get_account()["cash"] == 0.0


def test_missing_exchange_rate_fails_loudly():
    values = [v for v in _values() if v.tag != "ExchangeRate"]
    with pytest.raises(RuntimeError, match="exchange rate"):
        _broker(FakeIB(values=values)).get_account()


def test_positions_are_normalized():
    item = PortfolioItem(Stock("SPY", "SMART", "USD"), 5.0, 770.0, 3850.0, 760.0, 50.0, 0.0, ACCT)
    flat = PortfolioItem(Stock("QQQ", "SMART", "USD"), 0.0, 700.0, 0.0, 0.0, 0.0, 12.0, ACCT)
    assert _broker(FakeIB(portfolio=[item, flat])).get_positions() == [
        {"symbol": "SPY", "qty": 5.0, "market_value": 3850.0, "unrealized_pl": 50.0}
    ]


def test_equity_orders_are_market_on_open_in_whole_shares():
    ib = FakeIB()
    result = _broker(ib).place_market_order("SPY", 5.7, "buy")
    contract, order = ib.placed[0]
    assert (contract.symbol, contract.currency) == ("SPY", "USD")
    assert (order.action, order.orderType, order.tif, order.totalQuantity) == ("BUY", "MKT", "OPG", 5)
    assert result.order_id == "7" and result.status == "accepted" and not order_failed(result.status)


def test_less_than_one_share_fails_loudly():
    with pytest.raises(RuntimeError, match="whole shares"):
        _broker(FakeIB()).place_market_order("SPY", 0.6, "buy")


@pytest.mark.parametrize("ib_status,expected", [("Inactive", "rejected"), ("Cancelled", "canceled"), ("ApiCancelled", "canceled")])
def test_ib_rejections_are_failures_for_the_guards(ib_status, expected):
    result = _broker(FakeIB(status=ib_status)).place_market_order("SPY", 3, "sell")
    assert result.status == expected and order_failed(result.status)


def test_open_orders_and_pending_check():
    trade = Trade(contract=Stock("SPY", "SMART", "USD"), order=SimpleNamespace(action="SELL", totalQuantity=5.0),
                  orderStatus=OrderStatus(status="PreSubmitted"))
    broker = _broker(FakeIB(trades=[trade]))
    assert broker.get_open_orders() == [{"symbol": "SPY", "side": "sell", "qty": 5.0}]
    assert broker.has_open_order("SPY") and not broker.has_open_order("QQQ")


def test_fills_are_reported_in_the_snapshot_order_shape():
    from datetime import datetime, timezone
    fill = SimpleNamespace(contract=Stock("IBIT", "SMART", "USD"),
                           execution=SimpleNamespace(side="BOT", shares=100.0, price=47.9),
                           time=datetime(2026, 10, 6, 13, 30, tzinfo=timezone.utc))
    ib = FakeIB()
    ib.fills = lambda: [fill]
    assert _broker(ib).get_fills() == [{"symbol": "IBIT", "side": "buy", "qty": 100.0, "status": "filled",
                                        "filled_avg_price": 47.9, "filled_at": "2026-10-06T13:30:00+00:00"}]


def test_the_real_paper_account_id_passes_the_live_gate():
    from brokers.ibkr import check_live_gate
    check_live_gate("DUR239224", live_flag=None, armed=False)


def test_paper_accounts_always_pass_the_live_gate():
    from brokers.ibkr import check_live_gate
    check_live_gate("DU1234567", live_flag=None, armed=False)


@pytest.mark.parametrize("flag,armed", [(None, False), ("1", False), (None, True), ("yes", True)])
def test_live_account_needs_both_keys(flag, armed):
    from brokers.ibkr import check_live_gate
    with pytest.raises(RuntimeError, match="LIVE"):
        check_live_gate("U1234567", live_flag=flag, armed=armed)


def test_live_account_with_both_keys_passes():
    from brokers.ibkr import check_live_gate
    check_live_gate("U1234567", live_flag="1", armed=True)


def test_unknown_symbol_fails_before_ordering():
    ib = FakeIB()
    with pytest.raises(RuntimeError, match="does not recognise"):
        _broker(ib).place_market_order("NOPE", 3, "buy")
    assert ib.placed == []


def test_order_stuck_in_flight_fails_loudly():
    with pytest.raises(RuntimeError, match="unacknowledged"):
        _broker(FakeIB(status="PendingSubmit")).place_market_order("SPY", 3, "buy")
