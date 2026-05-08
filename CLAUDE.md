# Claude Trading — Master Context

> Claude reads this file at the start of every session. It is the compound memory of this workspace. Update it whenever a decision gets made.

---

## 1. Who I Am

- Rayyan, CS student at UdeM, active builder of 15+ AI projects.
- **Trading level: beginner.** I have never done algorithmic trading before.
- I am using Claude Code as my senior quant partner, not as a magic money printer.
- Language: French or English, whichever I open with.

## 2. The Mission

Build a durable Claude-assisted trading practice: research -> design -> backtest -> paper -> live. Each stage is gated by proof. No live trading before **all three** gates pass:

1. Profitable backtest across at least 2 different market regimes (trend + chop, or bull + bear).
2. 2+ weeks of green paper trading with the same parameters as the backtest.
3. I can explain every line of the strategy in my own words.

## 3. How Claude Should Work With Me

Apply the seven lessons from [PRINCIPLES.md](PRINCIPLES.md) on every task:

1. **Plan before you build.** If I describe a strategy in one paragraph, ask me the questions I haven't answered before writing a line of code.
2. **Treat yourself as a junior quant with ADHD.** Demand tight, specific specs. If my brief is vague, ask more, guess less.
3. **Live context over pasted data.** Prefer MCP servers and APIs over CSV dumps.
4. **Memory compounds.** Update this file, [journal/](journal/), and the active strategy's spec after every session.
5. **Statistical logs are the deliverable.** Every backtest or paper trade ends with a dated entry in `journal/`.
6. **AI is a research partner, not an oracle.** Community consensus is clear: most autonomous bots lose. Our edge is tighter research loops, better journaling, faster iteration — not a secret ML model.
7. **Routines are stateless; files are the memory.** Any scheduled workflow has to read from durable files and write back to them, or it will not improve over time.

## 4. Workspace Layout

| Path | Purpose |
|------|---------|
| [CLAUDE.md](CLAUDE.md) | This file — master context |
| [PRINCIPLES.md](PRINCIPLES.md) | The seven core lessons (900 hours distilled) |
| [ROADMAP.md](ROADMAP.md) | Stage-gated progression: learn -> backtest -> paper -> live |
| [README.md](README.md) | Public-facing workspace overview |
| [prompts/](prompts/) | Reusable prompt templates for common tasks |
| [memory/](memory/) | Durable files that routines read and update |
| [routines/](routines/) | Routine run-specs, schedules, and conventions |
| [strategies/](strategies/) | Each strategy = folder with `STRATEGY.md` spec + code |
| [research/](research/) | Ticker / market / concept research notes |
| [backtests/](backtests/) | Backtest runs, configs, results |
| [paper-trading/](paper-trading/) | Paper broker setup + daily log |
| [live-trading/](live-trading/) | **Gated.** Empty until all 3 gates in section 2 pass |
| [journal/](journal/) | Daily statistical tests + session reflections |
| [knowledge/](knowledge/) | Glossary + concepts I've learned |
| [agents/](agents/) | Multi-agent workflow role definitions |
| [tools/](tools/) | MCP, broker, framework setup notes |
| [freqtrade/](freqtrade/) | Crypto bot framework (cloned) |
| [claude-trading-skills/](claude-trading-skills/) | Skills for screening/research/options |
| [TradingAgents/](TradingAgents/) | Multi-LLM firm framework — **dormant, do not use yet** |
| [ft_userdata/](ft_userdata/) | Freqtrade config, strategies, data |

## 5. My Stack (update as decisions get made)

- **Markets:** learning both crypto (freqtrade) and US equities (Alpaca paper).
- **Data format:** OHLCV bars, timezone UTC, no dividend adjustment unless noted.
- **Automation foundation:** `skills.md` in each routine folder defines exchange APIs, 16+ `/trade-*` commands, and 5-agent research workflows. See [tools/skills-template.md](tools/skills-template.md).
- **Research system:** 5 agents in parallel (technical + fundamentals + sentiment + risk + thesis synthesis) for every stock/ticker analysis.
- **Paper broker (equities):** Alpaca — free. See [tools/alpaca-setup.md](tools/alpaca-setup.md).
- **Live broker candidate (equities):** Public.com — official Claude Desktop MCP. See [tools/public-com-setup.md](tools/public-com-setup.md).
- **Crypto exchanges (futures + spot, with API encryption local):** Binance, Bybit, Blofin, OKX, WEX, Tubbit (2bit). Keys never leave machine.
- **Crypto bot:** freqtrade, dry-run mode, docker-compose on port 8080.
- **Charting:** TradingView Desktop via MCP + webhook integration for signal automation.
- **Research:** Perplexity API for fast narrative/catalyst research; built-in web tools only as fallback.
- **Notifications:** Telegram for urgent alerts + mobile command channel, ClickUp optional for summaries.
- **Scheduling:** Claude Code routines — local for testing, remote for weekday automation (GitHub-backed for state persistence).
- **Python libs preferred:** pandas, numpy, TA-Lib, vectorbt / backtrader. Battle-tested before hand-rolled.
- **Secrets:** `.env` only, never committed. Remote routines use environment variables.
- **Logs:** every session ends with a dated entry in `journal/`.

## 6. Active Strategies

- [ma-crossover](strategies/ma_crossover/STRATEGY.md) — stage: **paper** (entered 2026-04-23). Backtest: IS Sharpe 0.82, OOS Sharpe 0.65, OOS DD -12.4%, OOS trades/year 3.02. **Gate 2: SOFT-PASS** as of 2026-05-07 (21% relative spread vs SPY×95% expectation; 0 fills in 14 days; kill-switch drill not yet run). Re-run target 2026-05-21. Tool: `backtests/ma_crossover/gate2_check.py --carry-in`.
- [rsi2-connors](strategies/rsi2_connors/STRATEGY.md) — stage: **rejected** (specced + backtested 2026-05-07). Fails 2/3 standalone OOS gates (Sharpe 0.31 < 0.5; trades/year 6.8 < 15). Correlation with ma-crossover OOS is 0.187 (genuinely diversifying), but absolute performance too weak to paper-trade. Hard-stop variant strictly worse → confirms Connors original framing. No re-tuning per §7.

### Rejected experiments (do not retry without a new thesis)

- **VIX25 regime gate** — rejected 2026-05-05. Filtered exactly one OOS trade and that trade was a +$1,763 winner (Nov-Dec 2022 reversal). High-VIX cross-ups on broad indices are reversal entries, not noise. See `journal/2026-05-05.md`. No re-tuning at thresholds 20/30 — the frame is wrong, not the number.
- **RSI(2) Connors mean-reversion** — rejected 2026-05-07. IS Sharpe 0.42, OOS Sharpe 0.31 (both below 0.5 bar). 200-DMA filter blocks too much of 2022 (bear) and RSI<10 readings too rare in 2023-24 (steady bull). Hard-stop variant strictly worse — confirms Connors original. Correlation 0.187 with ma-crossover OOS is genuinely low, BUT absolute return too weak (5% in 3 years) to be a useful diversifier on its own. See `strategies/rsi2_connors/STRATEGY.md §12`. Do not retry — the next strategy candidate is C (sector momentum) or D (crypto MA), not another mean-reversion variant.

## 7. Hard Rules (never break without a written waiver in this file)

- No live orders until all 3 gates in section 2 pass.
- No strategy change without a new dated entry in `journal/` and an updated `STRATEGY.md`.
- No deleting backtest logs. Losses are the training data.
- No "just tweak the parameters" loops — that is overfitting. If a strategy needs more than 2 parameter passes, re-examine the thesis in `research/` first.
- Secrets live in `.env` only. Never commit keys, tokens, webhook URLs.
- Remote routines use environment variables and must push file changes back to GitHub if they are expected to persist state.
- MCP tokens are fat — reset sessions when context bloats (see [PRINCIPLES.md](PRINCIPLES.md) comment on token management).

## 8. When Claude Starts a New Session

1. Read this file.
2. Read the latest entry in [journal/](journal/) if one exists.
3. If the task is a scheduled routine or automation task, read the files in [memory/](memory/) before acting.
4. If the task involves an active strategy, read its `STRATEGY.md`.
5. Ask me: "What are we working on today — research, strategy design, backtest, paper review, or journaling?"
6. If the task is non-trivial (3+ steps or architectural), enter plan mode before coding.

## 9. When Claude Should Push Back

- If I skip the plan step.
- If I want to go live before the 3 gates pass.
- If I describe a strategy in one paragraph and ask for 200 lines of code.
- If I am tweaking parameters in a loop (overfitting smell).
- If I ask you to do something that contradicts this file — prefer the file, then flag the conflict to me.
- If I get emotional about a loss and want to double down or change the system mid-trade.
