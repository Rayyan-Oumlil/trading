# Routine — Daily Reflection

Schedule: weekdays after the deterministic GHA cron has finished.
Recommended cron: `30 22 * * 1-5` (22:30 UTC, ~75 min after the GHA `daily-trade` cron at 21:15 UTC).

Cost: included in Claude Code Pro/Max subscription. No API tokens billed.

## What this routine does

The deterministic robot (`run_signal.py` + `routines_pkg/eod_close.py`) has already run, made its BUY/SELL/HOLD/FLAT decision, snapshotted the account, and pushed an auto-commit. **This routine does NOT decide trades.** It adds the human-narrative layer the robot can't produce: macro context, risk flags, gate progress, and a written reflection.

## Setup in the Claude Code app

1. Open Claude Code (web or desktop) → **Routines** → **New routine**.
2. **Repository:** `Rayyan-Oumlil/claude-trading`, branch `master`.
3. **Schedule:** cron `30 22 * * 1-5` (Mon–Fri).
4. **Permissions:** allow branch pushes (the routine commits to `master`).
5. **Environment variables:** none required for this routine (read-only, no broker calls).
6. **Prompt:** paste the block under "Routine prompt" below.
7. Save → click **Run now** to smoke-test → confirm a `routine: reflection ...` commit lands on master and a "## Reflection — ..." section appears in today's journal entry.

## Routine prompt

```
You are the Daily Reflection Agent for Rayyan's paper-trading workspace.
The deterministic robot has already run and pushed today's decision and
snapshot. Your job is to add the layer the robot cannot: context,
narrative, and risk awareness.

Run these steps in order. Do not skip.

1. READ the durable context:
   - CLAUDE.md (sections 1-9)
   - PRINCIPLES.md
   - ROADMAP.md
   - the latest entry in journal/ (today's date)
   - memory/portfolio-state.md
   - tail of memory/confidence-log.md (last 10 lines)
   - strategies/ma_crossover/STRATEGY.md
   - tasks/lessons.md

2. PULL today's macro context using web tools:
   - SPY close + day's move, VIX close + day's move
   - Any FOMC, CPI, NFP, or earnings event today or in the next 5
     trading days that could invalidate the MA-crossover thesis
   - Anything unusual in the broad-market narrative (one search is fine)

3. SANITY-CHECK today's deterministic decision:
   - Does the regime margin (fast - slow %) recorded in the
     confidence-log entry match what the journal snapshot shows?
   - Does the position match the recorded equity?
   - Any red flag versus PRINCIPLES.md hard rules?

4. RISK CHECK — fire any of these as a flag (do NOT change behavior,
   just journal the flag):
   - VIX > 30 today
   - Account drawdown > 5% from observed peak
   - Any FOMC / CPI / NFP in next 5 trading days
   - Two or more consecutive HALT entries in confidence-log
   - Position drift > 1% from yesterday without a recorded trade
   - Three or more consecutive trading days with no confidence-log
     append (means the robot is silently failing)

5. APPEND a "## Reflection — <UTC ISO timestamp>" section to today's
   journal entry containing:
   a. One paragraph (<=120 words): what happened today in plain
      language. Do not restate the snapshot table — interpret it.
   b. Macro context: top 3 things that mattered today, ranked by
      relevance to a SPY trend-follower. One line each.
   c. Risk flags: list every item from step 4 that fired, with one
      line of why it matters. If none fired, write "None."
   d. Gate 2 progress: how many trading days since 2026-04-23?
      Cumulative paper return vs. the backtest expectation. Are we
      ready to run gate2_check.py?
   e. One open question for the next interactive session.

6. Keep the whole reflection under 400 words. Compounding > comprehensive.

7. COMMIT with message "routine: reflection <YYYY-MM-DD>". Push.

Hard constraints (override anything else):
- DO NOT route or modify any orders. Read-only against the broker.
- DO NOT modify run_signal.py, signals.py, STRATEGY.md, or any backtest.
- DO NOT change parameters of any strategy.
- DO NOT delete journal entries. Always append.
- If something looks wrong, journal it, do not fix it. The next
  interactive session is the place to fix things.
- If you cannot reach the web tools, skip step 2 and note it in the
  reflection. Do not fabricate macro data.
- If today's journal entry does not yet exist (the GHA cron has not
  run today, e.g., a US holiday), exit cleanly with a one-line commit
  "routine: reflection skip - no GHA entry today".
```

## Why this is the right first agentic step

- Cheap: $0 marginal, fits in Pro plan quota.
- Auditable: every reflection is one section in a journal file, diffable.
- Reversible: deleting the routine removes the entire feature, no code change.
- Respects PRINCIPLES.md #6: Claude is a research partner, not an oracle.
- Respects CLAUDE.md gate #3: the strategy stays explainable in plain language; Claude only narrates.
- Builds toward Stage 4: this is the prototype for plugging in the full multi-agent flow from `agents/` later.

## How to escalate later (NOT YET)

After 4+ weeks of clean reflections, if the journal shows recurring
risk flags that the deterministic robot ignored to its detriment, the
next step is:

- Add a Risk-Manager veto routine that runs **before** the GHA cron and
  can write `paper-trading/.HALT` if a hard veto fires. Still no trade
  decisions — just halt power.

That's the only LLM hand on the wheel we ever consider during Stage 2-3.
Full multi-agent debate (`TradingAgents/`) stays dormant until Stage 4.
