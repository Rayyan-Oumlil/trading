# Operating Manual

The routine system exists to help with disciplined research, paper execution, journaling, and review. It does not override [../ROADMAP.md](../ROADMAP.md), and it does not weaken the paper-before-live gate.

## Default mode

- Stage 0-2 default = research and paper-first.
- New routines assume `paper` unless a file explicitly says otherwise.
- If there is any conflict between a routine prompt and [../CLAUDE.md](../CLAUDE.md), follow `CLAUDE.md`.

## Routine loop

1. Read the memory files in the order listed in [README.md](README.md).
2. Read the latest relevant journal entry.
3. Pull live context only for the current task.
4. Make the smallest necessary change.
5. Write back the outcome.
6. If remote, commit and push the updated files.

## What routines may do

- Research catalysts and narrative risk.
- Draft trade plans.
- Execute approved paper trades.
- Tighten stops or close trades within pre-written risk rules.
- Write logs, reviews, and summaries.

## What routines may not do

- Skip the kill switch check.
- Override stage gates.
- Trade live by default.
- Invent broker state instead of checking it.
- Spam notifications for non-events.

## Exact-environment rule

If a prompt references `ALPACA_API_SECRET`, `PERPLEXITY_API_KEY`, or `TELEGRAM_BOT_TOKEN`, those names must exist exactly in the Claude environment. Remote routines do not read my local `.env` file.
