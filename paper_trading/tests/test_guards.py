import pytest

from paper_trading.guards import assert_only_expected_positions, order_failed


@pytest.mark.parametrize("status", ["OrderStatus.REJECTED", "rejected", "OrderStatus.CANCELED", "expired"])
def test_failed_statuses(status):
    assert order_failed(status)


@pytest.mark.parametrize("status", ["OrderStatus.ACCEPTED", "new", "filled", "OrderStatus.PENDING_NEW"])
def test_live_statuses(status):
    assert not order_failed(status)


def test_foreign_position_raises():
    with pytest.raises(RuntimeError, match="GLD"):
        assert_only_expected_positions([{"symbol": "SPY"}, {"symbol": "GLD"}], allowed={"SPY"})


def test_expected_positions_pass():
    assert_only_expected_positions([{"symbol": "SPY"}], allowed={"SPY"})
    assert_only_expected_positions([], allowed={"SPY"})


def test_foreign_position_fully_covered_by_open_sell_is_allowed():
    positions = [{"symbol": "SPY", "qty": 1.0}, {"symbol": "GLD", "qty": 6.62}]
    open_orders = [{"symbol": "GLD", "side": "sell", "qty": 6.62}]
    assert_only_expected_positions(positions, allowed={"SPY"}, open_orders=open_orders)


def test_partial_or_buy_side_cover_still_raises():
    positions = [{"symbol": "GLD", "qty": 6.62}]
    with pytest.raises(RuntimeError, match="GLD"):
        assert_only_expected_positions(positions, {"SPY"}, open_orders=[{"symbol": "GLD", "side": "sell", "qty": 3.0}])
    with pytest.raises(RuntimeError, match="GLD"):
        assert_only_expected_positions(positions, {"SPY"}, open_orders=[{"symbol": "GLD", "side": "buy", "qty": 6.62}])
