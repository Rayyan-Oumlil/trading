from datetime import date

import pandas as pd

from routines_pkg.desk_snapshot import fill_deviations, integrity_flags, performance

SESSION = date(2026, 10, 2)


def _codes(flags):
    return {(f["code"], f["severity"]) for f in flags}


def test_clean_day_has_no_flags():
    lines = ["2026-10-02 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.75%"]
    assert integrity_flags(lines, [{"symbol": "SPY"}], {"SPY"}, SESSION) == []


def test_nan_in_latest_session_is_halt():
    lines = ["2026-10-02 | SELL | 6/10 | regime flipped bearish; fast-slow margin +nan%"]
    assert ("nan_in_log", "halt") in _codes(integrity_flags(lines, [], {"SPY"}, SESSION))


def test_conflicting_decisions_same_session_is_halt():
    lines = ["2026-10-02 | HOLD | 7/10 | aligned", "2026-10-02 | SELL | 6/10 | flipped"]
    assert ("conflicting_decisions", "halt") in _codes(integrity_flags(lines, [{"symbol": "SPY"}], {"SPY"}, SESSION))


def test_multi_strategy_lines_are_ignored():
    lines = ["2026-10-02 | HOLD | 7/10 | aligned", "2026-10-02 | SCAN | 6/10 | entries=[] [multi]"]
    assert integrity_flags(lines, [{"symbol": "SPY"}], {"SPY"}, SESSION) == []


def test_pending_does_not_conflict_with_a_trade():
    lines = ["2026-10-02 | BUY | 7/10 | cross-up", "2026-10-02 | PENDING | 6/10 | duplicate run skipped"]
    assert integrity_flags(lines, [], {"SPY"}, SESSION) == []


def test_foreign_position_is_halt():
    flags = integrity_flags(["2026-10-02 | HOLD | 7/10 | x"], [{"symbol": "SPY"}, {"symbol": "GLD"}], {"SPY"}, SESSION)
    assert ("foreign_position", "halt") in _codes(flags)


def test_robot_silent_for_latest_session_is_alert():
    flags = integrity_flags(["2026-10-01 | HOLD | 7/10 | x"], [], {"SPY"}, SESSION)
    assert ("robot_silent", "alert") in _codes(flags)


def test_performance_vs_spy_and_drawdown():
    equity = [(date(2026, 4, 23), 100_000.0), (date(2026, 6, 3), 110_000.0), (date(2026, 10, 2), 99_000.0)]
    spy = pd.Series([700.0, 735.0, 770.0], index=pd.to_datetime(["2026-04-23", "2026-06-03", "2026-10-02"]))
    perf = performance(equity, spy)
    assert round(perf["account_return_pct"], 2) == -1.0
    assert round(perf["spy_return_pct"], 2) == 10.0
    assert round(perf["vs_spy_pct"], 2) == -11.0
    assert round(perf["current_drawdown_pct"], 2) == -10.0
    assert round(perf["max_drawdown_pct"], 2) == -10.0


def test_fill_deviation_over_2pct_is_reported():
    closes = pd.Series([760.0, 770.0], index=pd.to_datetime(["2026-09-30", "2026-10-01"]))
    orders = [
        {"symbol": "SPY", "status": "filled", "filled_avg_price": 786.0, "filled_at": "2026-10-02T13:30:00+00:00"},
        {"symbol": "SPY", "status": "filled", "filled_avg_price": 771.0, "filled_at": "2026-10-01T13:30:00+00:00"},
    ]
    devs = fill_deviations(orders, closes, "SPY", limit_pct=2.0)
    assert [round(d["deviation_pct"], 2) for d in devs] == [2.08]


def test_two_trades_same_session_is_halt():
    lines = ["2026-10-02 | BUY | 7/10 | cross-up", "2026-10-02 | BUY | 7/10 | cross-up"]
    assert ("conflicting_decisions", "halt") in _codes(integrity_flags(lines, [], {"SPY"}, SESSION))


def test_split_log_lines_handles_joined_entries():
    from routines_pkg.desk_snapshot import split_log_lines
    text = "2026-10-01 | SCAN | 6/10 | x [multi] [multi]2026-10-02 | FLAT | 5/10 | y\n2026-10-02 | HOLD | 7/10 | z\n"
    assert split_log_lines(text) == [
        "2026-10-01 | SCAN | 6/10 | x [multi] [multi]",
        "2026-10-02 | FLAT | 5/10 | y",
        "2026-10-02 | HOLD | 7/10 | z",
    ]


def test_foreign_position_being_closed_is_alert_not_halt():
    positions = [{"symbol": "SPY"}, {"symbol": "GLD"}]
    flags = integrity_flags(["2026-10-02 | HOLD | 7/10 | x"], positions, {"SPY"}, SESSION, closing={"GLD"})
    assert _codes(flags) == {("foreign_position_closing", "alert")}


def test_daily_report_shows_day_pnl_and_vs_spy():
    from routines_pkg.desk_snapshot import daily_report
    snap = {
        "session": "2026-10-05",
        "account": {"equity": 104_120.50},
        "performance": {"day_change": 683.11, "day_change_pct": 0.66, "account_return_pct": 4.12,
                        "spy_return_pct": 9.50, "vs_spy_pct": -5.38, "current_drawdown_pct": -1.9},
        "positions": [{"symbol": "SPY", "qty": 125.4, "market_value": 96_500.0, "unrealized_pl": 312.4}],
        "flags": [],
    }
    text = daily_report(snap)
    assert text.splitlines()[0] == "📈 2026-10-05 · Equity $104,120.50 · Today +$683.11 (+0.66%)"
    assert "Since start +4.12% vs SPY +9.50% (−5.38 pts)" in text
    assert "SPY 125.4 sh · $96,500 · unrealized +$312" in text


def test_daily_report_red_day_and_flat_book():
    from routines_pkg.desk_snapshot import daily_report
    snap = {
        "session": "2026-10-06", "account": {"equity": 99_000.0},
        "performance": {"day_change": -1000.0, "day_change_pct": -1.0, "account_return_pct": -1.0,
                        "spy_return_pct": -2.0, "vs_spy_pct": 1.0, "current_drawdown_pct": -3.0},
        "positions": [], "flags": [{"code": "x", "severity": "alert", "detail": "d"}],
    }
    text = daily_report(snap)
    assert text.startswith("📉 2026-10-06 · Equity $99,000.00 · Today −$1,000.00 (−1.00%)")
    assert "(+1.00 pts)" in text and "Positions: none (cash)" in text and "⚠️ 1 flag" in text


def test_performance_includes_day_change():
    equity = [(date(2026, 10, 1), 100_000.0), (date(2026, 10, 2), 101_000.0)]
    spy = pd.Series([700.0, 707.0], index=pd.to_datetime(["2026-10-01", "2026-10-02"]))
    perf = performance(equity, spy)
    assert perf["day_change"] == 1000.0 and round(perf["day_change_pct"], 2) == 1.0


def test_different_symbols_same_session_are_not_a_conflict():
    lines = ["2026-10-02 | HOLD | 7/10 | SPY: aligned", "2026-10-02 | BUY | 7/10 | BTC/USD: cross-up",
             "2026-10-02 | FLAT | 5/10 | ETH/USD: awaiting"]
    positions = [{"symbol": "SPY"}, {"symbol": "BTCUSD"}]
    assert integrity_flags(lines, positions, {"SPY", "BTCUSD", "ETHUSD"}, SESSION) == []


def test_same_crypto_symbol_two_decisions_is_halt():
    lines = ["2026-10-02 | HOLD | 7/10 | SPY: aligned", "2026-10-02 | BUY | 7/10 | BTC/USD: x",
             "2026-10-02 | SELL | 6/10 | BTC/USD: y"]
    assert ("conflicting_decisions", "halt") in _codes(integrity_flags(lines, [], {"SPY"}, SESSION))


def test_snapshot_allows_every_sleeve_symbol():
    from routines_pkg.desk_snapshot import ALLOWED
    assert ALLOWED == {"SPY", "BTCUSD", "ETHUSD"}
