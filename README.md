# Claude Trading

My personal Claude-assisted trading workspace. Learning algorithmic trading from zero, using Claude Code as a senior-quant partner.

> **Start here:** [CLAUDE.md](CLAUDE.md) for session context, [PRINCIPLES.md](PRINCIPLES.md) for the rules of engagement, [ROADMAP.md](ROADMAP.md) for the stage-gated progression.

## Layout

```
CLAUDE.md           master context — Claude reads on every session
PRINCIPLES.md       seven rules distilled from community experience
ROADMAP.md          learn -> backtest -> paper -> live, stage-gated

prompts/            reusable prompt templates (research, strategy, review)
memory/             routine-readable state files and operating memory
routines/           schedule-facing routine specs and run conventions
strategies/         one folder per strategy with STRATEGY.md + code
research/           ticker / market / concept research notes
backtests/          backtest configs + results (never delete)
paper-trading/      paper broker setup + daily execution log
live-trading/       GATED. empty until roadmap stage 3 passes.
journal/            daily session notes + statistical tests
knowledge/          glossary + concepts I've learned
agents/             multi-agent workflow role definitions
tools/              MCP + broker + framework setup docs
tasks/              cross-session lessons and process corrections

freqtrade/          crypto bot framework (cloned)
claude-trading-skills/  Claude skills for screening/research/options
TradingAgents/      multi-LLM firm framework — DORMANT
ft_userdata/        freqtrade config + strategies + data
```

## First session

From any new Claude Code session in this folder, the bot will read `CLAUDE.md` automatically. Open a session with:

> "What are we working on today?"

Claude will route to research, strategy design, backtest, paper review, or journal based on my answer and the workspace state.

## Active strategies

| Strategy | Stage | OOS Sharpe | Max DD | Trades/yr | Notes |
|----------|-------|-----------|--------|-----------|-------|
| [ma-crossover](strategies/ma_crossover/STRATEGY.md) | Paper (Gate 2 soft-pass) | 0.65 | -12.4% | 3.0 | 0 fills in 14 days; kill-switch drill pending |
| [rsi2-multi](strategies/rsi2_multi/STRATEGY.md) | Backtest passed | 0.76 | -5.59% | 72 | 6 ETFs, no hard stop; all 3 gates green |
| [rsi2-connors](strategies/rsi2_connors/STRATEGY.md) | Rejected | 0.31 | — | 6.8 | Sharpe < 0.5, too few trades |

No live trading. Gate 2 paper requirement: 2+ weeks green with backtest params unchanged. See [ROADMAP.md](ROADMAP.md).
