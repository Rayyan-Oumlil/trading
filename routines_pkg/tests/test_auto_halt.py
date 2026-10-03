from routines_pkg.auto_halt import halt_message, unacknowledged_halts

ACK = """## Acknowledged (halt flags already reviewed — do not re-halt on these)

- nan_in_log | 2026-10-02 | old code | interactive
"""


def _snap(*flags):
    return {"session": "2026-10-02", "flags": list(flags)}


def test_acknowledged_halt_flag_is_ignored():
    snap = _snap({"code": "nan_in_log", "severity": "halt", "detail": "x"})
    assert unacknowledged_halts(snap, ACK) == []


def test_new_halt_flag_fires():
    flag = {"code": "foreign_position", "severity": "halt", "detail": "positions outside the strategy: ['TSLA']"}
    assert unacknowledged_halts(_snap(flag), ACK) == [flag]


def test_same_code_on_another_session_is_not_acknowledged():
    snap = {"session": "2026-10-05", "flags": [{"code": "nan_in_log", "severity": "halt", "detail": "x"}]}
    assert len(unacknowledged_halts(snap, ACK)) == 1


def test_alerts_never_halt():
    assert unacknowledged_halts(_snap({"code": "robot_silent", "severity": "alert", "detail": "x"}), ACK) == []


def test_halt_message_names_every_flag_and_the_fix():
    msg = halt_message("2026-10-05", [{"code": "drawdown_kill", "severity": "halt", "detail": "dd -26%"}])
    assert msg.startswith("🔴 HALTED")
    assert "drawdown_kill" in msg and "dd -26%" in msg and ".HALT" in msg
