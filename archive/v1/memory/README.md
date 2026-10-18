# Memory

This folder is the routine-readable state layer.

The key idea from the video research is simple: routines are stateless, files are the memory. A scheduled Claude run should not try to infer state from scratch every time. It should read a small set of durable files, do the work, and write back what changed.

## Read order for routines

1. [operating-manual.md](operating-manual.md)
2. [risk-limits.md](risk-limits.md)
3. [routine-state.md](routine-state.md)
4. [portfolio-state.md](portfolio-state.md)
5. [watchlist.md](watchlist.md)
6. Latest relevant journal entry in [../journal/](../journal/)

## Rules

- Keep these files short enough to fit routine context budgets.
- Write facts, not essays.
- If a routine changes reality, update the relevant file before the run ends.
- Remote routines only remember updates that get committed and pushed.
