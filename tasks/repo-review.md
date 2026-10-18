# Repo review — 2026-10-18

Goal: decide, folder by folder, what stays in v2. Fill the **Your verdict** column yourself.
Nothing is deleted until the archive tag `archive/v1-2026-10-18` exists.

Verdicts: **KEEP** (core of v2) · **ARCHIVE** (move to `archive/`, keep in git) · **REMOVE** (no value, safe to drop; git history keeps it).

| # | Folder / file | What it is | Used by the robot? | Last change | Claude's suggestion | Your verdict |
|---|---|---|---|---|---|---|
| 1 | `CLAUDE.md` | Master rules, gates, stack | — | 10-04 | KEEP, rewrite for v2 | |
| 2 | `PRINCIPLES.md` | The 7 lessons | — | 04-26 | KEEP | |
| 3 | `ROADMAP.md` | Stage gates | — | 04-26 | KEEP, rewrite for v2 | |
| 4 | `README.md` | Public overview | — | 06-04 | KEEP, rewrite last | |
| 5 | `journal/` (124 files) | Every session's log | — | 10-17 | KEEP (history is data) | |
| 6 | `memory/` (12) | Confidence logs, desk notes | yes (logs) | 10-17 | ARCHIVE old logs, keep the folder | |
| 7 | `research/` (5) | Idea queue + results of tested ideas | — | 10-04 | KEEP `queue.md` (what failed and why) | |
| 8 | `backtests/` (37, 99 MB) | Scripts + saved results | — | 10-04 | ARCHIVE whole; results must never be deleted (§7) | |
| 9 | `strategies/` (16) | Specs + signal code | yes | 10-04 | ARCHIVE; v2 starts with a new strategy | |
| 10 | `run_signal.py` | The robot | yes | 10-04 | ARCHIVE (rebuild once you understand it) | |
| 11 | `run_signal_multi.py` | Rejected rsi2-multi robot | no | 06-01 | REMOVE | |
| 12 | `tests_run_signal/` | Robot tests | yes (CI) | 10-04 | ARCHIVE with the robot | |
| 13 | `brokers/` (8) | IBKR adapter, FX conversion | yes | 10-17 | ARCHIVE; reuse later — the IBKR lessons live here | |
| 14 | `paper_trading/` (19) | Data, guards, kill switch, Alpaca client | yes | 10-04 | ARCHIVE; `alpaca_client.py` is dead | |
| 15 | `paper-trading/` (4) | Old Alpaca setup notes (note the dash vs underscore) | no | 05-07 | REMOVE or merge into journal | |
| 16 | `routines_pkg/` (18) | Snapshot, auto-halt, Telegram report | yes | 10-04 | ARCHIVE | |
| 17 | `routines/` (4) | Routine run-specs (trading-desk, paused) | no | 10-04 | ARCHIVE | |
| 18 | `.github/workflows/` (5) | `daily-trade` (robot), 3× desk, `multi-agent-trade` (disabled) | yes | 10-17 | Disable all; keep files archived | |
| 19 | `plans/` (5) | Dated plans (IBKR, crypto, roadmap to live) | — | 10-04 | ARCHIVE; `2026-10-04-ibkr-paper.md` has the CIRO research | |
| 20 | `tasks/` | `lessons.md` | — | 10-03 | KEEP (rules from past mistakes) | |
| 21 | `knowledge/` (3) | Glossary + concepts | — | 04-26 | KEEP — grow it as you relearn | |
| 22 | `prompts/` (12) | Prompt templates | no | 04-26 | Review: keep the 1–2 you actually use | |
| 23 | `agents/` (8) | Multi-agent role definitions | no | 04-26 | ARCHIVE (never used by the robot) | |
| 24 | `tools/` (10) | Setup notes (Alpaca, Public.com, TradingView, freqtrade…) | no | 04-26 | REMOVE most: Alpaca and Public.com are dead ends for Canada | |
| 25 | `live-trading/` | Empty gate folder | lock file lives here | 04-26 | KEEP (the live lock) | |
| 26 | `freqtrade/` (103 MB) | Cloned crypto framework (git submodule) | no | 04-26 | REMOVE — never used | |
| 27 | `ft_userdata/` (1.4 MB) | Freqtrade config | no | 04-26 | REMOVE with freqtrade | |
| 28 | `claude-trading-skills/` (73 MB) | Cloned skills (submodule) | no | 04-26 | REMOVE — never used | |
| 29 | `TradingAgents/` (9.5 MB) | Multi-LLM framework (submodule, "dormant") | no | 04-26 | REMOVE — also breaks CI checkout cleanup | |
| 30 | `docker-compose.yml` | Freqtrade docker | no | 04-26 | REMOVE with freqtrade | |
| 31 | `requirements.txt`, `pytest.ini` | Python deps, test config | yes | 10-03 | KEEP, trim to what v2 uses | |
| 32 | `.playwright-mcp/`, `__pycache__/` | Browser snapshots, Python cache | no | — | Ignored by git; delete locally anytime | |

## Questions to ask about each folder
1. Can I explain in one sentence what it does?
2. Did I use it in the last 3 months?
3. Does it hold **evidence** (results, failures, decisions)? → never delete, archive.
4. Is it a dead end for a Canadian (Alpaca, Public.com, CAD API orders)? → remove.

## Known issue found 2026-10-17 (keep in mind when archiving)
The ma-crossover robot does not match its backtest: the backtest enters only on the cross day and has a 5% stop-loss; `run_signal.py` holds whenever SMA10 > SMA50 and has no stop. v2 must share one signal module between backtest and robot.
