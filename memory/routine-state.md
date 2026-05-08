# Routine State

Last updated: 2026-05-07T16:30:00Z

## Last Close

Weekly close routine ran: 2026-05-07T16:30:00Z
Decision: HOLD | Confidence: 7/10

## Weekly review complete: 2026-05-07T16:30:00Z (W19)

## Pre-Market Snapshot

| Symbol | Close | Volume | Timestamp |
|--------|-------|--------|-----------|
| SPY | 733.83 | 53,373,841 | 2026-05-06T04:00:00Z |
| QQQ | 695.77 | 38,924,917 | 2026-05-06T04:00:00Z |

## Action items for next session

- [x] Add ALPACA_PAPER_TRADE=true to GHA secrets — DONE 2026-05-07 (also workflow now hard-fails if ≠ "true")
- [x] Phase B Gate 2 evaluation — DONE 2026-05-07. Verdict SOFT-PASS (21% spread, carry-in mode). Report: `journal/2026-05-07_gate2_review.md`
- [x] Phase A "3 consecutive green GHA runs" — DONE many times over (10 consecutive greens 2026-04-26 → 2026-05-07). Phase A declared complete.
- [x] RSI overbought watch rule — DONE 2026-05-07. Added to STRATEGY.md §10.5 (non-actionable; journal flags only at RSI > 78 / > 85)
- [x] RSI(2) Connors strategy spec — DONE 2026-05-07. New strategy at `strategies/rsi2_connors/STRATEGY.md`, stage `research`

## Open items (not deferred — concrete next dates)

- 2026-05-21: re-run `gate2_check.py --carry-in` for tighter sample (target: clean PASS, ≤20% spread)
- ~~Before any Stage 3 promotion: write `paper-trading/kill-switch.md` SOP and run a fire drill~~ — DONE 2026-05-07 (drill PASSED)
- ~~Pending: backtest RSI(2) Connors IS+OOS once ma-crossover hits clean Gate 2 PASS~~ — done 2026-05-07; strategy REJECTED, see `strategies/rsi2_connors/STRATEGY.md §12.1`

## Daily-reflection routine — known issues (file before next manual session)

The Claude `daily-reflection` routine (scheduled weekdays 6:00 PM EDT) has two structural problems surfaced 2026-05-07:

1. **Sequencing:** routine fires at 6:00 PM EDT but GHA EOD bot is scheduled for 5:15 PM EDT and lags ~1h on free tier — actually fires ~6:15 PM. So the reflection routine often runs BEFORE the bot pushes today's decision.
   - **Fix:** move routine schedule to 7:00 PM EDT (1h buffer over the lagging cron).

2. **Push permission:** routine commits to an auto-named `claude/<random>` branch. The token in the routine env doesn't have write access to that branch namespace, so push fails with 403 and the work is lost when the env tears down.
   - **Fix:** configure routine to push directly to `master` (same model as the GHA bot), OR set up a `claude/*` branch protection that auto-merges to master after CI green.

Both are routine-config-level fixes (not code). Action required from Rayyan in the Claude routine UI.

The 2026-05-07 reflection content was reconstructed manually from the routine's session summary. See `journal/2026-05-07_gate2_review.md` § Reflection.
