import numpy as np
import pandas as pd
import pytest

from backtests.candidates.engine import metrics, passes, simulate
from backtests.candidates.strategies import crypto_ma_targets, dual_momentum_targets, sector_momentum_targets

D = pd.bdate_range("2024-01-01", periods=3)


def test_buy_and_hold_without_costs_tracks_price():
    prices = pd.DataFrame({"A": [100.0, 110.0, 121.0]}, index=D)
    targets = pd.DataFrame({"A": [1.0]}, index=D[:1])
    eq = simulate(prices, targets, cost_bps=0)
    assert eq.iloc[-1] == pytest.approx(1.21)


def test_costs_charged_on_traded_notional():
    prices = pd.DataFrame({"A": [100.0] * 3, "B": [50.0] * 3}, index=D)
    targets = pd.DataFrame({"A": [1.0, 0.0], "B": [0.0, 1.0]}, index=D[:2])
    eq = simulate(prices, targets, cost_bps=10)
    assert eq.iloc[-1] == pytest.approx(0.999 * (1 - 0.002))


def test_no_lookahead_decision_day_move_is_not_captured():
    prices = pd.DataFrame({"A": [100.0, 110.0, 121.0]}, index=D)
    targets = pd.DataFrame({"A": [1.0]}, index=D[1:2])
    eq = simulate(prices, targets, cost_bps=0)
    assert eq.iloc[1] == pytest.approx(1.0)
    assert eq.iloc[-1] == pytest.approx(1.1)


def test_metrics_and_drawdown():
    eq = pd.Series([1.0, 1.2, 0.9, 1.08], index=pd.bdate_range("2024-01-01", periods=4))
    m = metrics(eq, periods_per_year=252)
    assert m["max_drawdown_pct"] == pytest.approx(-25.0)


def test_pass_requires_both_windows_and_both_tests():
    good = {"sharpe": 1.0, "max_drawdown_pct": -10.0}
    bench = {"sharpe": 0.8, "max_drawdown_pct": -20.0}
    worse_dd = {"sharpe": 1.0, "max_drawdown_pct": -30.0}
    assert passes({"full": good, "recent": good}, {"full": bench, "recent": bench})
    assert not passes({"full": good, "recent": worse_dd}, {"full": bench, "recent": bench})


def _month_prices(cols, rets_by_col, days=70):
    idx = pd.bdate_range("2024-01-01", periods=days)
    return pd.DataFrame({c: 100 * np.cumprod(1 + np.full(days, r)) for c, r in zip(cols, rets_by_col)}, index=idx)


def test_sector_momentum_holds_top_two_at_month_end():
    prices = _month_prices(["XLK", "XLF", "XLE", "XLV", "XLI"], [0.004, 0.003, -0.001, 0.0, 0.001])
    t = sector_momentum_targets(prices)
    assert all(d == prices.index[prices.index.to_period("M") == d.to_period("M")][-1] for d in t.index)
    last = t.iloc[-1]
    assert last["XLK"] == 0.5 and last["XLF"] == 0.5 and last[["XLE", "XLV", "XLI"]].sum() == 0


def test_dual_momentum_goes_to_bonds_when_stocks_lose_to_tbills():
    prices = _month_prices(["SPY", "EFA", "AGG", "BIL"], [-0.001, -0.0005, 0.0001, 0.0001], days=300)
    assert dual_momentum_targets(prices).iloc[-1].to_dict() == {"SPY": 0.0, "EFA": 0.0, "AGG": 1.0}


def test_dual_momentum_picks_stronger_stock_market():
    prices = _month_prices(["SPY", "EFA", "AGG", "BIL"], [0.001, 0.002, 0.0001, 0.0001], days=300)
    assert dual_momentum_targets(prices).iloc[-1].to_dict() == {"SPY": 0.0, "EFA": 1.0, "AGG": 0.0}


def test_crypto_ma_half_sleeve_when_trending():
    idx = pd.date_range("2024-01-01", periods=60)
    prices = pd.DataFrame({"BTC-USD": np.linspace(100, 200, 60), "ETH-USD": np.linspace(200, 100, 60)}, index=idx)
    last = crypto_ma_targets(prices).iloc[-1]
    assert last["BTC-USD"] == 0.5 and last["ETH-USD"] == 0.0


def test_crypto_trades_only_when_a_signal_flips():
    idx = pd.date_range("2024-01-01", periods=120)
    up_then_down = np.concatenate([np.linspace(100, 200, 80), np.linspace(200, 120, 40)])
    prices = pd.DataFrame({"BTC-USD": up_then_down, "ETH-USD": np.linspace(100, 300, 120)}, index=idx)
    t = crypto_ma_targets(prices)
    assert len(t) <= 4  # warm-up entry rows + one BTC exit, not ~70 daily rebalances
    assert (t.diff().abs().sum(axis=1).iloc[1:] > 0).all()
