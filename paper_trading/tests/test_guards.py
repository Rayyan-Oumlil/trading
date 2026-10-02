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
