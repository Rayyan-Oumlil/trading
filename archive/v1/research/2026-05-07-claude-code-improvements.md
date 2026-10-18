---
date: 2026-05-07
type: tooling-research
agent: general-purpose subagent (background)
---

# Claude Code Improvements for This Workspace — 10 Concrete Suggestions

Research conducted by background subagent on 2026-05-07 evening. The subagent found 10 concrete, source-cited improvements scoped to the workspace's current state (ma-crossover paper, rsi2-connors specced, GHA cron loop, .HALT kill switch, append-only confidence log).

> **Filter applied to suggestions:** prefer real repos and blog posts with recent activity over generic patterns. Each item below has at least one URL.

---

## 1. PreToolUse hook that blocks tool calls when `.HALT` exists

**Source:** [karanb192/claude-code-hooks](https://github.com/karanb192/claude-code-hooks), [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)

**Why:** Today the `.HALT` check lives inside Python (`run_signal.py`, `eod_close.py`, `premarket.py`). A bash-level PreToolUse hook in `~/.claude/settings.json` matching `mcp__alpaca-mcp__place_order|Bash(*alpaca*place_order*)` and exiting 2 if `Path('.HALT').exists()` makes the kill switch enforced by the harness — a bug in the strategy or a misrouted MCP call cannot bypass it.

**Effort:** S (~8 lines in settings.json + a 5-line bash script).
**Risk:** over-broad matcher could block safe research calls. Test against a dummy `.HALT` and a `read_account` call to confirm only order-placement is denied.

---

## 2. Stop hook that forces journal write before exit

**Source:** [Embedding Memory into Claude Code (DEV)](https://dev.to/shimo4228/embedding-memory-into-claude-code-from-session-loss-to-persistent-context-54d8), [rajeevramani gist](https://gist.github.com/rajeevramani/cb6b6bacb1a01a1fcfbea344d2440c8d)

**Why:** PRINCIPLES.md says "statistical logs are the deliverable" but enforcement is by convention. A Stop hook that requires fields (`request | investigated | learned | completed | next_steps`) before letting the session end would make journaling a hard contract. Especially valuable for the GHA cron — workflow_dispatch sessions can otherwise exit clean and silent on bad days.

**Effort:** M (toggle-file logic + GHA-aware path so it works headless).
**Risk:** a hung Stop hook can wedge `claude` exit. Always include a 30-second timeout fallback.

---

## 3. Deny rules for live-broker endpoints in `settings.json`

**Source:** [trailofbits/claude-code-config — Permission Deny Rules](https://deepwiki.com/trailofbits/claude-code-config/3.1-permission-deny-rules), [Claude Code Permissions guide](https://claudefa.st/blog/guide/development/permission-management)

**Why:** ROADMAP says no live until 3 gates pass. Today nothing structurally prevents a misclick. Add at workspace level:
- `Bash(*api.alpaca.markets*)` — denied (live host)
- `Bash(*public.com/api*)` — denied until gate 3
- `Read(./live-trading/*.env)` — denied
- `Bash(git push * --force *)` — denied

Keep `paper-api.alpaca.markets` allowed. Structural complement to CLAUDE.md §7 hard rules.

**Effort:** S.
**Risk:** false sense of safety if API host string drifts. Add a startup check that pings paper host and refuses to load if response domain is anything but `paper-api.alpaca.markets`.

---

## 4. Financial Datasets MCP for fundamentals beside Alpaca

**Source:** [financial-datasets/mcp-server](https://github.com/financial-datasets/mcp-server) (free tier sufficient for SPY/QQQ + ~20 names)

**Why:** Alpaca-mcp gives bars + orders, not fundamentals. RSI(2)-Connors uses SPY only, but if screening scales (sector rotation candidate D from `strategy-candidates.md`), need P/E, sector, earnings dates without scraping. Avoids hand-rolled HTTP. EODHD is the heavier alternative if outgrown.

**Effort:** S (env var + `claude mcp add`).
**Risk:** free-tier rate limits. Wrap calls in routine cache; don't call per-bar.

---

## 5. Perplexity MCP for catalyst/news research

**Source:** [perplexityai/modelcontextprotocol](https://github.com/perplexityai/modelcontextprotocol)

**Why:** CLAUDE.md already lists Perplexity as preferred for narrative research. The official MCP turns it into a first-class tool the sentiment subagent can call without HTTP wiring. Pairs with the existing EOD multi-agent pattern.

**Effort:** S.
**Risk:** cost creep if subagents call it per-ticker per-day. Cap with daily budget env var.

---

## 6. TradingView MCP for chart-image-grounded analysis

**Source:** [tradesdontlie/tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp) (CDP, local-only) or [ertugrul59/tradingview-chart-mcp](https://github.com/ertugrul59/tradingview-chart-mcp)

**Why:** Technical agent today reasons over OHLCV numbers only. Letting it actually see the chart catches things bar-arrays miss: trendlines, gaps, range structure. CDP variant runs against existing TV Desktop install — no new accounts.

**DO NOT use:** [jackson-video-resources/claude-tradingview-mcp-trading](https://github.com/jackson-video-resources/claude-tradingview-mcp-trading) — auto-executes on BitGet, contradicts gate gates.

**Effort:** M (Chrome DevTools wiring + working TV Desktop session).
**Risk:** brittle to TV UI changes. Pin a known-good version. **Defer** until a real reason — numbers are sufficient for the two current strategies.

---

## 7. Contrarian / devil's-advocate subagent in the EOD workflow

**Source:** [aaddrick/contrarian](https://github.com/aaddrick/contrarian), [Anthropic agent-teams docs](https://code.claude.com/docs/en/agent-teams)

**Why:** Three current agents (technical/sentiment/risk) all *support* the trade. Adding a 4th whose job is "what would make this trade lose money?" before the confidence-log entry is the institutional "second-set-of-eyes" check. Ties to PRINCIPLES.md "AI is research partner, not oracle."

**Effort:** S (one agent file in `agents/`).
**Risk:** it will sometimes be right when you don't want it to be — that is the point. Log overrides in confidence-log.

---

## 8. Deterministic regime classifier as a sub-agent (not LLM-based)

**Source:** [QuantTradingOS/Market-Regime-Agent](https://github.com/QuantTradingOS/Market-Regime-Agent) — explicitly: "LLMs, if used later, are limited to optional narration, never classification."

**Why:** VIX25 rejection on 2026-05-05 was the right call: regime gates need to be derived, not bolted on. This repo gives a deterministic skeleton (200-DMA, ADX, realized vol) you can adopt. Run once daily, write to `memory/regime.md`, and let strategies *read* the regime rather than each re-deriving it. RSI2-Connors uses 200-DMA already — extracting that into a shared regime file prevents drift.

**Effort:** M (port classifier, wire to memory pattern).
**Risk:** becomes a new overfitting surface if you start "tuning" thresholds per strategy. Freeze the regime spec before any strategy uses it.

---

## 9. VectorBT skills pack for parameterized backtests — **HIGH RISK**

**Source:** [marketcalls/vectorbt-backtesting-skills](https://github.com/marketcalls/vectorbt-backtesting-skills)

**Why:** VectorBT runs 1000+ param combos in the time backtrader runs 1. Tearsheet output (Sharpe, MAR, DD, trades/year) matches existing IS/OOS reporting.

**Risk (highest on this list):** the same strength that makes it fast also makes it the perfect overfitting tool. Use ONLY for **regime sensitivity** and **walk-forward validation**, never for parameter sweeps. Document this constraint in any strategy's STRATEGY.md before installing the pack.

**Effort:** M.

---

## 10. Confidence log → calibrated Brier-score schema

**Source:** Tetlock superforecasting + [claude-mem hooks-architecture](https://docs.claude-mem.ai/hooks-architecture)

**Why:** Current 1-10 confidence is ordinal. Convert each entry to a probability ("65% this trade closes green within 10 days") and at trade close auto-compute Brier score. After 50 trades, will know whether "8" actually means 80% or 55%. Same file format, two new fields (`p_target`, `outcome`, `brier`), one Stop-hook script that closes-out scored entries from Alpaca trade history.

**Effort:** S (schema change + closeout script).
**Risk:** tiny. Only risk is reading scores before N=30 closed trades — single-digit samples mean nothing. Mark as "warming up" until N=30.

---

## Recommended sequencing (subagent's own ranking)

**This week (immediate value):**
1. Item 1 — `.HALT` PreToolUse hook (pure safety hardening)
2. Item 3 — Permission deny rules (pure safety hardening)
3. Item 7 — Contrarian agent (drop-in to EOD workflow)
4. Item 10 — Brier schema (start collecting calibration data NOW so it's meaningful by Stage 3)

**After clean Gate 2 PASS (Stage 3 prep):**
5. Item 2 — Stop hook journal enforcement
6. Item 4 — Financial Datasets MCP
7. Item 5 — Perplexity MCP
8. Item 8 — Regime classifier

**Defer or skip:**
- Item 6 (TradingView MCP) — defer until concrete need
- Item 9 (VectorBT) — defer; high overfitting risk for a beginner

---

## My (Claude's) ranking after reviewing

I agree with items 1, 3, 10 as the immediate wins. I'd downgrade item 7 (contrarian agent) — adding a 4th agent doubles token cost per EOD run for a marginal benefit at this scale. Better to start with item 10 (Brier scoring) which generates actual calibration data, and revisit contrarian once we have N=30 to know whether confidence is currently mis-calibrated.

I would also flag: **before adding any of these, run them past CLAUDE.md §7 (Hard Rules)**. Item 1 in particular intersects with the "kill switch must be testable by hand" requirement — make sure the bash hook doesn't break the existing fire-drill procedure.
