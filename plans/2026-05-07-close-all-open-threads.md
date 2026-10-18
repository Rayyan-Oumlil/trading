---
created: 2026-05-07
objective: Close out all 5 open threads from W19 weekly review tonight, no deferrals
mode: direct (single session, no branch/PR — small atomic edits to a workspace, not a feature)
---

# Plan — Close All Open Threads Tonight

## Context (cold-start brief)

Today (2026-05-07) the weekly close routine ran and produced a HOLD 7/10 decision. The review surfaced 5 open threads. Rayyan's directive: **stop deferring, run everything tonight, confirm everything**. This plan executes them in dependency order.

State at plan start:
- Equity $102,625, SPY 133.13 shares @ avg $713.62, +2.76% unrealized
- 10 consecutive green GHA runs since 2026-04-26 (Phase A bar was 3 — done many times over)
- Alpaca secrets (`ALPACA_API_KEY`, `ALPACA_API_SECRET`) present in repo. `ALPACA_PAPER_TRADE` is NOT set. The workflow does not actually check for it; paper mode is hardcoded in the alpaca-py client. So the "missing env var" is documentation drift, not a real safety hole.
- Gate 2 tool exists at `backtests/ma_crossover/gate2_check.py`. Window 2026-04-23 → 2026-05-07 = 14 calendar days = 2 weeks. Eligible.
- Strategy candidate research: A (RSI(2) Connors mean-reversion) is the recommended next strategy.

## Step Graph

```
Step 1 (Gate 2 run) ───┐
Step 2 (Phase A done) ──┼──> Step 6 (commit/push everything)
Step 3 (env var)  ──────┤
Step 4 (RSI rule) ──────┤
Step 5 (RSI(2) spec) ───┘
```

Steps 1–5 are independent (different files). Execute in series for atomic commits, but they could parallelize if needed.

---

## Step 1 — Gate 2 evaluation (write report to journal/)

**Goal:** Determine whether ~14 days of paper trading match the backtest expectation within ±20%.

**Action:**
```bash
python backtests/ma_crossover/gate2_check.py --since 2026-04-23 --until 2026-05-07 --write
```

**Outputs:**
- New file: `journal/2026-05-07_gate2_review.md` containing PASS/SOFT-PASS/FAIL verdict
- stdout report

**Exit criteria:**
- File exists and has the verdict line
- Update `strategies/ma_crossover/STRATEGY.md` §12 Runs table with the result
- Update `memory/routine-state.md` to note Gate 2 outcome

**Failure mode:** If env vars `ALPACA_API_KEY`/`SECRET` are missing locally, the script throws KeyError. Fall back: pull portfolio history via gh actions log + the journal equity snapshots already recorded.

---

## Step 2 — Declare Phase A complete

**Goal:** Mark Phase A (automation loop restored) as DONE in ROADMAP.

**Evidence:** 10 consecutive successful GHA `daily-trade` runs from 2026-04-26 to 2026-05-07 (verified by `gh run list`).

**Action:** Edit `ROADMAP.md` to mark Phase A complete. Add a Phase A close-out note to the journal.

**Exit criteria:** ROADMAP.md reflects Phase A done with date and run count.

---

## Step 3 — ALPACA_PAPER_TRADE: add secret + harden workflow check

**Goal:** Eliminate the soft drift between routine prompt ("verify ALPACA_PAPER_TRADE=true") and reality (no such env var exists).

**Two-part fix:**
1. Add `ALPACA_PAPER_TRADE=true` as a repo secret via `gh secret set`.
2. Update `.github/workflows/daily-trade.yml` to expose the env var AND verify it equals "true". Bake this into the existing "Verify required secrets" step.

**Action:**
```bash
echo "true" | gh secret set ALPACA_PAPER_TRADE --repo Rayyan-Oumlil/claude-trading
```
+ edit workflow to reference and verify it.

**Exit criteria:**
- `gh secret list` shows ALPACA_PAPER_TRADE
- workflow file fails fast if it's ever set to anything other than "true"
- Local `.env` does not need it (the routine prompt's check is for remote runs only)

---

## Step 4 — RSI overbought monitoring rule

**Goal:** Codify the RSI watch flag observed today (RSI 74.8). NOT an action rule — only a journal flag.

**Two parts:**
1. Add a "Watch flags" section to `strategies/ma_crossover/STRATEGY.md` between §10 (Kill Conditions) and §11 (Parameters). Threshold: RSI(14) > 78 = log a warning in the journal entry. Threshold: RSI(14) > 85 = require a daily journal sentence justifying continued hold.
2. Add a 1-line RSI computation + warning emission to whichever routine produces journal output. Defer the code change if the routine's source isn't trivially obvious — the rule lives in STRATEGY.md regardless.

**Exit criteria:**
- STRATEGY.md has the new "Watch flags" section
- Rule is non-actionable (no automated SELL on RSI alone) — preserves spec-purity

---

## Step 5 — RSI(2) Connors strategy: STRATEGY.md spec stub

**Goal:** Convert "candidate" → "specced and ready for backtest" so it's not stuck in research limbo. Backtest itself is NOT in tonight's scope (per CLAUDE.md: spec first, code second).

**Action:** Create `strategies/rsi2_connors/STRATEGY.md` from the same template as `ma_crossover/STRATEGY.md`. Stage: `research`. Universe: SPY daily. Entry: RSI(2) < 10 above 200-DMA. Exit: RSI(2) > 70 OR close > 5-day MA. No tuning, literature defaults only.

**Update `research/strategy-candidates.md`** to mark A as "specced 2026-05-07" with link to the new STRATEGY.md.

**Exit criteria:**
- `strategies/rsi2_connors/STRATEGY.md` exists with all 13 sections from the template
- `research/strategy-candidates.md` updated
- `CLAUDE.md` §6 active strategies table updated to list rsi2_connors at stage `research`

---

## Step 6 — Commit + push everything

**Goal:** Persist the night's work to GitHub so the GHA loop and future sessions see it.

**Action:**
```bash
git add -A
git commit -m "close-out W19: Gate 2 + Phase A done + RSI rule + RSI(2) spec"
git push origin master
```

**Exit criteria:**
- Push succeeds
- `git status` clean

---

## Invariants to preserve

- No live orders. (Already enforced — paper account; nothing in this plan executes a trade.)
- No deletion of journal entries. (No deletes anywhere in this plan.)
- No re-tuning of MA crossover parameters. (No parameter touches.)
- No change to the kill conditions in STRATEGY.md §10. (Adding §10.5 watch flags, leaving §10 untouched.)

## Rollback

Each step writes to a different file/section. If Step N goes wrong:
- `git stash` undo before commit
- After commit: `git revert <sha>` for that step's commit (keep them atomic per step if needed)
