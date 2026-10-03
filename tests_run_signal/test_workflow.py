from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "daily-trade.yml"


def test_trade_alert_only_fires_in_eod_mode():
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["run"]["steps"]
    alert = next(s for s in steps if s["name"] == "Alert on trade or halt")
    assert "mode == 'eod'" in alert["if"]


def _steps(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"]["run"]["steps"]


def test_eod_builds_desk_snapshot_even_when_signal_fails():
    steps = _steps(WORKFLOW)
    names = [s["name"] for s in steps]
    snap = steps[names.index("Build desk snapshot")]
    assert "always()" in snap["if"] and "mode == 'eod'" in snap["if"]
    assert "routines_pkg.desk_snapshot" in snap["run"]
    assert names.index("Build desk snapshot") < names.index("Commit memory + journal updates")


def test_desk_alert_file_is_forwarded_to_telegram():
    path = WORKFLOW.parent / "desk-notify.yml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    on = doc[True] if True in doc else doc["on"]  # PyYAML parses bare `on` as True
    assert on["push"]["paths"] == ["memory/desk-alert.txt"]
    assert any("paper_trading.notify" in s.get("run", "") for s in _steps(path))
