# Desk Notes — trading-desk routine memory

The trading-desk routine reads this file first and rewrites it last, every run.
Humans may edit any section. The routine may edit **Open threads** and **Halt log** only;
**Acknowledged** is written by Rayyan (or an interactive session) — the routine never adds to it.

## Acknowledged (halt flags already reviewed — do not re-halt on these)

Format: `<flag code> | <session> | <why it is safe> | <who/when>`

- nan_in_log | 2026-10-02 | Old yfinance code logged a NaN FLAT; fixed and deployed in 1ebcce4..165bbe4 (Alpaca bars + NaN guard) | interactive session 2026-10-02
- nan_in_log | 2026-09-29 | Same root cause as above | interactive session 2026-10-02
- nan_in_log | 2026-09-22 | Same root cause as above | interactive session 2026-10-02

## Open threads

- [ ] 2026-10-03 — TODO Rayyan: set up cron-job.org dispatch (steps in routines/README.md) so the 20:10 ET robot run never depends on the PC. Until then: PC task on time, GHA cron is a late backup.

- [ ] 2026-10-03 — crypto-trend sleeves on paper (BTC 5%, ETH 5%). First buys expected at the Sat 10-03 20:10 ET run. Confirm each happens exactly once.
- [ ] 2026-10-02 — GLD 6.62 / IWM 8.97 sells queued (rsi2-multi wind-down). Expect fills Mon 10-05 open; `foreign_position_closing` alert until then.
- [ ] 2026-10-02 — SPY re-entry with session 10-05 (Mon 20:10 ET run, fills Tue 10-06), sized at 85.5% of equity. Confirm exactly one BUY and that cash stays >= 0 after crypto + SPY.
- [ ] 2026-10-02 — Gate 2 clock restarts on the first clean session after 165bbe4. 0 counted as of 10-02; first candidate is session 10-05.
- [ ] 2026-10-02 — Deferred from review: the robot does not detect a next-open order rejection (Phase 2 reconciliation).
- [x] 2026-10-03 — Closed: the 10-02 `+nan%` FLAT line was written by the old yfinance code, before the fix (acknowledged). Multi-asset question answered: rsi2-multi rejected; `[multi]` lines are historical. 20:28 ET `eod FAILED` was the foreign-position guard (expected).
- [x] 2026-10-03 — Note: desk fired twice for session 10-02 (00:26Z, 00:57Z). The second run appended only an update.

## Halt log

Format: `<UTC timestamp> | <flag code> | <session> | <detail> | cleared by / when`

(none yet)
