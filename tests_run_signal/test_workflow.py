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


def test_desk_merge_runs_masters_definition_not_the_branch():
    path = WORKFLOW.parent / "desk-merge.yml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    on = doc[True] if True in doc else doc["on"]
    assert "push" not in on, "push-triggered workflows run the pushed branch's YAML"
    assert on["workflow_run"]["workflows"] == ["desk-branch-pushed"]
    runs = " ".join(s.get("run", "") for s in _steps(path))
    assert "--no-renames" in runs
    assert "routines_pkg.desk_merge_guard" in runs and "paper_trading.notify" in runs
    checkout = next(s for s in _steps(path) if s.get("uses", "").startswith("actions/checkout"))
    assert checkout["with"]["ref"] == "master"


def test_eod_sends_daily_pnl_report():
    steps = _steps(WORKFLOW)
    names = [s["name"] for s in steps]
    report = steps[names.index("Send daily P&L report")]
    assert "mode == 'eod'" in report["if"] and "always()" in report["if"]
    assert "paper_trading.notify" in report["run"]
    assert "--report" in steps[names.index("Build desk snapshot")]["run"]


def test_eod_runs_every_day_for_crypto():
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    on = doc[True] if True in doc else doc["on"]
    crons = [c["cron"] for c in on["schedule"]]
    assert "20 0 * * *" in crons  # daily, after the 00:00 UTC crypto close


def test_trade_alert_covers_only_lines_written_this_run():
    steps = _steps(WORKFLOW)
    names = [s["name"] for s in steps]
    mark = steps[names.index("Mark confidence-log length")]
    assert names.index("Mark confidence-log length") < names.index("Run signal then EOD routine")
    assert "GITHUB_OUTPUT" in mark["run"]
    alert = steps[names.index("Alert on trade or halt")]
    assert "steps.logmark.outputs.lines" in alert["run"] and "tail -n 1" not in alert["run"]


def test_runs_sync_to_latest_master_before_trading():
    steps = _steps(WORKFLOW)
    names = [s["name"] for s in steps]
    sync = steps[names.index("Sync to latest master")]
    assert "git pull --ff-only" in sync["run"]
    assert names.index("Sync to latest master") < names.index("Run signal then EOD routine")
