# Routines

This folder is the schedule-facing layer for the workspace.

The exact routine prompts live in [../prompts/](../prompts/), but this folder documents how the schedule is meant to behave as a system.

## Default weekday cadence

- `06:00` pre-market research and catalyst scan
- `08:30` market-open execution and stop placement
- `12:00` midday risk check
- `15:00` close review and write-back
- `Friday 16:00` weekly review

## Local vs remote

- Local routines are for fast testing and dry runs.
- Remote routines are for dependable automation, but they only persist memory if they push changes back to GitHub.

## Non-negotiables

- Every routine reads the memory files first.
- Every routine checks the kill switch before any execution.
- Every routine writes back outcomes before it exits.
- Every new routine gets tested with `Run now`.

## Precise trigger (cron-job.org → workflow_dispatch) — added 2026-10-02

GitHub's scheduled cron fired 3–5 h late (EOD at ~00:30 UTC, "premarket" mid-session). cron-job.org calls GitHub's `workflow_dispatch` on time and handles DST because it schedules in `America/New_York`. The GHA `schedule:` crons stay as a late fallback; a second run the same evening is a no-op because `run_signal.py` sees the pending order and logs `PENDING`.

| Job | Time (America/New_York, Mon–Fri) | Body |
|---|---|---|
| premarket | 07:00 | `{"ref":"master","inputs":{"mode":"premarket"}}` |
| eod | 16:20 | `{"ref":"master","inputs":{"mode":"eod"}}` |

- URL: `POST https://api.github.com/repos/Rayyan-Oumlil/trading/actions/workflows/daily-trade.yml/dispatches`
- Headers: `Authorization: Bearer <PAT>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`
- PAT: fine-grained, this repo only, **Actions: Read and write**, 1-year expiry. Lives only in cron-job.org. **Expiry: record date here → ____.** Rotate by creating a new PAT and pasting it into both jobs.
- Verify: `gh run list -L 3 --json event,createdAt` shows `workflow_dispatch` within a minute of the scheduled time.

### Active trigger (2026-10-02): Windows Task Scheduler instead of cron-job.org

Registered on Rayyan's PC (timezone Eastern, DST-aware): `ClaudeTrading-Dispatch-EOD` (`ClaudeTrading-Dispatch-Premarket` deleted 2026-10-04 with the Alpaca premarket routine) (**daily 20:10**, since 2026-10-03 — after the 00:00 UTC crypto close), each running `gh workflow run daily-trade.yml -R Rayyan-Oumlil/trading -f mode=<mode>` with the local `gh` login — no PAT. `StartWhenAvailable` catches up after sleep. If the PC is off, the GHA cron fallback still runs (late); a duplicate the same evening logs `PENDING`. Move to cron-job.org (above) if the PC is often off at 16:20.
Remove: `Unregister-ScheduledTask -TaskName 'ClaudeTrading-Dispatch-*' -Confirm:$false`
