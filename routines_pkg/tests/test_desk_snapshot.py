from datetime import date

import pandas as pd

from routines_pkg.desk_snapshot import fill_deviations, integrity_flags, performance

SESSION = date(2026, 10, 2)


def _codes(flags):
    return {(f["code"], f["severity"]) for f in flags}


def test_clean_day_has_no_flags():
    lines = ["2026-10-02 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.75%"]
    assert _quiet(integrity_flags(lines, [{"symbol": "SPY"}], {"SPY"}, SESSION)) == []


def test_nan_in_latest_session_is_halt():
    lines = ["2026-10-02 | SELL | 6/10 | regime flipped bearish; fast-slow margin +nan%"]
    assert ("nan_in_log", "halt") in _codes(integrity_flags(lines, [], {"SPY"}, SESSION))


def test_conflicting_decisions_same_session_is_halt():
    lines = ["2026-10-02 | HOLD | 7/10 | aligned", "2026-10-02 | SELL | 6/10 | flipped"]
    assert ("conflicting_decisions", "halt") in _codes(integrity_flags(lines, [{"symbol": "SPY"}], {"SPY"}, SESSION))


def test_multi_strategy_lines_are_ignored():
    lines = ["2026-10-02 | HOLD | 7/10 | aligned", "2026-10-02 | SCAN | 6/10 | entries=[] [multi]"]
    assert _quiet(integrity_flags(lines, [{"symbol": "SPY"}], {"SPY"}, SESSION)) == []


def test_pending_does_not_conflict_with_a_trade():
    lines = ["2026-10-02 | BUY | 7/10 | cross-up", "2026-10-02 | PENDING | 6/10 | duplicate run skipped"]
    assert _quiet(integrity_flags(lines, [], {"SPY"}, SESSION)) == []


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
    flags = _quiet(integrity_flags(["2026-10-02 | HOLD | 7/10 | x"], positions, {"SPY"}, SESSION, closing={"GLD"}))
    assert _codes(flags) == {("foreign_position_closing", "alert")}




def test_performance_includes_day_change():
    equity = [(date(2026, 10, 1), 100_000.0), (date(2026, 10, 2), 101_000.0)]
    spy = pd.Series([700.0, 707.0], index=pd.to_datetime(["2026-10-01", "2026-10-02"]))
    perf = performance(equity, spy)
    assert perf["day_change"] == 1000.0 and round(perf["day_change_pct"], 2) == 1.0


FULL_DAY = ["2026-10-02 | HOLD | 7/10 | SPY: aligned", "2026-10-02 | BUY | 7/10 | IBIT: cross-up",
            "2026-10-02 | FLAT | 5/10 | ETHA: awaiting"]


def _quiet(flags):
    return [f for f in flags if f["code"] != "robot_silent"]


def test_different_symbols_same_session_are_not_a_conflict():
    positions = [{"symbol": "SPY"}, {"symbol": "IBIT"}]
    assert integrity_flags(FULL_DAY, positions, {"SPY", "IBIT", "ETHA"}, SESSION) == []


def test_same_etf_two_decisions_is_halt():
    lines = FULL_DAY + ["2026-10-02 | SELL | 6/10 | IBIT: y"]
    assert ("conflicting_decisions", "halt") in _codes(integrity_flags(lines, [], {"SPY"}, SESSION))


def test_every_sleeve_must_log_its_session():
    flags = integrity_flags(FULL_DAY[:2], [], {"SPY"}, SESSION)
    assert [f["detail"] for f in flags] == ["no ETHA entry for session 2026-10-02"]


def test_halted_day_is_not_robot_silent():
    assert integrity_flags(["2026-10-02 | HALT | 0/10 | kill switch active"], [], {"SPY"}, SESSION) == []


def test_snapshot_allows_every_sleeve_symbol():
    from routines_pkg.desk_snapshot import ALLOWED
    assert ALLOWED == {"SPY", "IBIT", "ETHA"}


def test_equity_log_keeps_one_point_per_session(tmp_path):
    from routines_pkg.desk_snapshot import read_equity, record_equity, write_equity
    path = tmp_path / "equity.csv"
    rows = record_equity(read_equity(path), date(2026, 10, 5), 1_000_000.0)
    rows = record_equity(rows, date(2026, 10, 6), 1_002_000.0)
    rows = record_equity(rows, date(2026, 10, 6), 1_003_000.0)  # rerun same session replaces
    write_equity(rows, path)
    assert read_equity(path) == [(date(2026, 10, 5), 1_000_000.0), (date(2026, 10, 6), 1_003_000.0)]


def _snap(**overrides):
    snap = {
        "session": "2026-10-06",
        "account": {"equity": 1_003_000.0, "cash": 900_000.0},
        "performance": {"start": "2026-10-05", "day_change": 3000.0, "day_change_pct": 0.3, "account_return_pct": 0.3,
                        "spy_return_pct": 0.1, "vs_spy_pct": 0.2, "current_drawdown_pct": 0.0},
        "positions": [{"symbol": "SPY", "qty": 1218.0, "market_value": 855_000.0, "unrealized_pl": 1200.4}],
        "robot_log_today": ["2026-10-06 | HOLD | 7/10 | SPY: position aligned with regime; fast-slow margin +1.80%",
                            "2026-10-06 | BUY | 7/10 | IBIT: cross-up confirmed; fast-slow margin +0.40%; 1045 sh at open"],
        "open_orders": [{"symbol": "IBIT", "side": "buy", "qty": 1045.0}],
        "fills": [],
        "flags": [],
        "halted": None,
    }
    return {**snap, **overrides}


def test_daily_report_is_one_message_with_pnl_decisions_and_queue():
    from routines_pkg.desk_snapshot import daily_report
    text = daily_report(_snap())
    assert text.splitlines()[0] == "📈 2026-10-06 · IBKR paper · Equity $1,003,000.00 USD · Today +$3,000.00 (+0.30%)"
    assert "Since 2026-10-05: +0.30% vs SPY +0.10% (+0.20 pts)" in text
    assert "SPY 1218 sh · $855,000 · unrealized +$1,200" in text
    assert "• IBIT BUY · fast-slow margin +0.40% · 1045 sh at open" in text
    assert "⏳ Queued for next open: BUY 1045 IBIT" in text


def test_daily_report_red_day_flags_halt_and_no_usd():
    from routines_pkg.desk_snapshot import daily_report
    snap = _snap(account={"equity": 990_000.0, "cash": 0.0}, positions=[], robot_log_today=[], open_orders=[],
                 performance={"start": "2026-10-05", "day_change": -10_000.0, "day_change_pct": -1.0,
                              "account_return_pct": -1.0, "spy_return_pct": -2.0, "vs_spy_pct": 1.0,
                              "current_drawdown_pct": -1.0},
                 flags=[{"code": "fill_deviation", "severity": "halt", "detail": "d"}], halted="HALTED at x\nReason: y\n")
    text = daily_report(snap)
    assert text.startswith("📉 2026-10-06")
    assert "Today −$10,000.00 (−1.00%)" in text and "(+1.00 pts)" in text
    assert "Positions: none (cash)" in text and "💱 No USD cash" in text
    assert "🚨 fill_deviation: d" in text and "🛑 HALTED" in text


def test_logged_buy_that_never_reached_the_account_is_flagged():
    from routines_pkg.desk_snapshot import order_state_flags
    lines = ["2026-10-05 | BUY | 7/10 | IBIT: cross-up", "2026-10-06 | HOLD | 7/10 | IBIT: aligned"]
    assert order_state_flags(lines, [], []) and order_state_flags(lines, [], [])[0]["code"] == "order_missing"
    assert order_state_flags(lines, [{"symbol": "IBIT"}], []) == []
    assert order_state_flags(lines, [], [{"symbol": "IBIT", "side": "buy", "qty": 1.0}]) == []


def test_logged_sell_with_position_still_held_is_flagged():
    from routines_pkg.desk_snapshot import order_state_flags
    lines = ["2026-10-05 | SELL | 6/10 | SPY: flipped"]
    assert [f["code"] for f in order_state_flags(lines, [{"symbol": "SPY"}], [])] == ["order_missing"]
    assert order_state_flags(lines, [], []) == []
