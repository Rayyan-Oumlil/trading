from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "daily-trade.yml"


def test_trade_alert_only_fires_in_eod_mode():
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["run"]["steps"]
    alert = next(s for s in steps if s["name"] == "Alert on trade or halt")
    assert "mode == 'eod'" in alert["if"]
