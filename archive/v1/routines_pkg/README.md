# Routines Package

Python scripts the `daily-trade` GitHub workflow runs after `run_signal.py`. No AI involved.

| File | Purpose |
|------|---------|
| `desk_snapshot.py` | Builds the account snapshot, halt flags and the daily report |
| `auto_halt.py` | Writes `.HALT` on any unacknowledged halt flag and texts Rayyan |
| `send_report.py` | Sends the daily report to Telegram once per evening |

The local Windows routines (`premarket.py`, `eod_close.py`) and the trading-desk merge guard were
removed on 2026-10-18. They live in the git tag `archive/v1-2026-10-18`.
