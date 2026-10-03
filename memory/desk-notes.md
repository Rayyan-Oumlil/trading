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

- [x] 2026-10-03 — ANSWERED by Rayyan/interactive: the `2026-10-02 | FLAT | … +nan%` line was written by the OLD yfinance code (GHA run 00:46 UTC, before 1ebcce4..165bbe4 deployed). New code raises on NaN instead of logging. Not a regression.
- [x] 2026-10-03 — ANSWERED: the multi-asset scanner (rsi2-multi) is NOT sanctioned — rejected and workflow disabled 2026-10-02. Every `[multi]` log line is historical. The live robot is SPY ma-crossover only, until a crypto-trend sleeve is approved (backtest PASSED 2026-10-03, see research/queue.md).
- [x] 2026-10-03 — The 20:28 ET `daily-trade eod FAILED` was the foreign-position guard refusing to trade while GLD/IWM sells are queued. Expected until Monday's open fills; not a bug.

- [x] 2026-10-02 — Telegram alerts live (@Trader20062_bot); failure-alert fire drill passed 00:02Z 10-03.

- [ ] 2026-10-02 — GLD 6.62 / IWM 8.97 sells queued (rsi2-multi wind-down). Expect fills Mon 2026-10-05 open; expect `foreign_position_closing` alert until then.
- [ ] 2026-10-02 — First EOD after fills should BUY ~95% cash SPY (regime bullish since ~09-24). Confirm it happened once, not twice.
- [ ] 2026-10-02 — Desk 10-02: FLAT log line still prints margin +nan%; confirm it predates the fix. Multi-asset vs STRATEGY.md question open (see brief).
- [ ] 2026-10-02 — Gate 2 clock restarts on the first clean session after 165bbe4. Count clean sessions from there.
- [ ] 2026-10-02 — Deferred from review: next-open order rejections are not detected by the robot (Phase 2 reconciliation).

## Halt log

Format: `<UTC timestamp> | <flag code> | <session> | <detail> | cleared by / when`

(none yet)
