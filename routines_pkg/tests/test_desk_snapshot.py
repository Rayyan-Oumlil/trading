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
