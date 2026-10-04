from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "daily-trade.yml"


def _doc(path: Path = WORKFLOW) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _steps(path: Path = WORKFLOW) -> list[dict]:
    return _doc(path)["jobs"]["run"]["steps"]


def _named() -> tuple[list[str], list[dict]]:
    steps = _steps()
    return [s["name"] for s in steps], steps


def test_desk_alert_file_is_forwarded_to_telegram():
    path = WORKFLOW.parent / "desk-notify.yml"
    doc = _doc(path)
    on = doc[True] if True in doc else doc["on"]  # PyYAML parses bare `on` as True
    assert on["push"]["paths"] == ["memory/desk-alert.txt"]
    assert any("paper_trading.notify" in s.get("run", "") for s in _steps(path))


def test_desk_merge_runs_masters_definition_not_the_branch():
    path = WORKFLOW.parent / "desk-merge.yml"
    doc = _doc(path)
    on = doc[True] if True in doc else doc["on"]
    assert "push" not in on, "push-triggered workflows run the pushed branch's YAML"
    assert on["workflow_run"]["workflows"] == ["desk-branch-pushed"]
    runs = " ".join(s.get("run", "") for s in _steps(path))
    assert "--no-renames" in runs
    assert "routines_pkg.desk_merge_guard" in runs and "paper_trading.notify" in runs
    checkout = next(s for s in _steps(path) if s.get("uses", "").startswith("actions/checkout"))
    assert checkout["with"]["ref"] == "master"


def test_runs_every_evening():
    doc = _doc()
    on = doc[True] if True in doc else doc["on"]
    assert [c["cron"] for c in on["schedule"]] == ["20 0 * * *"]


def test_no_alpaca_anywhere_in_the_run():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "ALPACA_" not in text and "routines_pkg.premarket" not in text


def test_gateway_is_paper_only_and_always_stopped():
    names, steps = _named()
    start = steps[names.index("Start IB Gateway (paper)")]["run"]
    assert "TRADING_MODE=paper" in start and "4002:4004" in start and "127.0.0.1:" in start
    assert "always()" in steps[names.index("Stop IB Gateway")]["if"]


def test_gateway_image_is_pinned_and_password_not_on_the_command_line():
    names, steps = _named()
    start = steps[names.index("Start IB Gateway (paper)")]["run"]
    assert "ib-gateway@sha256:" in start and ":stable" not in start
    assert "--env-file" in start and '-e TWS_PASSWORD' not in start


def test_order_of_operations():
    names, _ = _named()
    order = ["Sync to latest master", "Run tests (no trading on a red suite)", "Run the robot",
             "Build snapshot + daily report", "Auto-halt (deterministic brake)",
             "Send the daily report (once per evening)", "Commit memory + journal updates"]
    assert [names.index(n) for n in order] == sorted(names.index(n) for n in order)


def test_snapshot_and_report_run_even_when_the_robot_fails():
    names, steps = _named()
    assert "always()" in steps[names.index("Build snapshot + daily report")]["if"]
    send = steps[names.index("Send the daily report (once per evening)")]
    assert "steps.snapshot.outcome == 'success'" in send["if"]
    assert send["env"]["ROBOT_OK"] == "${{ steps.robot.outcome == 'success' }}"


def test_brake_commits_halt():
    names, steps = _named()
    assert "steps.snapshot.outcome == 'success'" in steps[names.index("Auto-halt (deterministic brake)")]["if"]
    assert ".HALT" in steps[names.index("Commit memory + journal updates")]["run"]


def test_failure_or_timeout_alerts():
    names, steps = _named()
    assert steps[names.index("Alert on failure")]["if"] == "failure() || cancelled()"
