# Lessons

## 2026-04-19

- If the user changes a destructive or cleanup instruction mid-task, stop that step immediately and preserve the source material unless they restate deletion explicitly.

## 2026-04-23

- **Backtest accounting:** always track `cash` and `position` separately. On entry, `cash -= shares * fill`. On exit, `cash += shares * fill`. Mark-to-market as `cash + position * close`. Never use a single `equity` variable that doubles as both cash and position value — you will double-count. Verify with identity `starting_cash + sum(pnl) == final_cash`. Symptom: implausibly deep drawdown vs stop-loss setting.

## 2026-05-07

- **Stale-clone trap.** Before declaring "the routine is broken" or "memory is empty," run `git fetch && git log origin/master ^master` to see what is on remote that you have not pulled. A local working tree where `git status` shows `deleted: .github/workflows/<name>.yml` looks identical to a real automation outage but may just be an uncommitted local deletion of a file that is alive and well on origin. Symptoms that this is happening: portfolio-state.md timestamp is days old, journal/ has no recent entries, but the broker account state has clearly evolved. Always check the remote first. The correct first command of any "is the loop alive?" diagnosis is `git fetch`, not `git log` of the local branch.

- **Pre-committed decision rules save money.** The VIX25 gate experiment had a written rule before any backtest ran: *"keep if Sharpe up AND drawdown down AND trades/year ≥ 3."* Result: the gate filtered out exactly one OOS trade and that trade was a +$1,763 winner. Without the pre-committed rule it would have been tempting to ship the filter (the metrics looked roughly equivalent at a glance). The rule made the discard decision automatic, no negotiation. Always write the keep/discard rule before you run the experiment, and put it in the journal in the same paragraph as the hypothesis.
