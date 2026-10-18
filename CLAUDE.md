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

Apply the seven lessons from [docs/PRINCIPLES.md](docs/PRINCIPLES.md) on every task:

1. **Plan before you build.** If I describe a strategy in one paragraph, ask me the questions I haven't answered before writing a line of code.
2. **Treat yourself as a junior quant with ADHD.** Demand tight, specific specs. If my brief is vague, ask more, guess less.
3. **Live context over pasted data.** Prefer MCP servers and APIs over CSV dumps.
4. **Memory compounds.** Update this file, [journal/](journal/), and the active strategy's spec after every session.
5. **Statistical logs are the deliverable.** Every backtest or paper trade ends with a dated entry in `journal/`.
6. **AI is a research partner, not an oracle.** Community consensus is clear: most autonomous bots lose. Our edge is tighter research loops, better journaling, faster iteration — not a secret ML model.
7. **Routines are stateless; files are the memory.** Any scheduled workflow has to read from durable files and write back to them, or it will not improve over time.

## 4. Workspace Layout (simplified 2026-10-18)

| Path | Purpose |
|------|---------|
| [CLAUDE.md](CLAUDE.md) | This file — master context |
| [journal/](journal/) | Dated session logs and statistical tests |
| [docs/](docs/) | Principles, roadmap, lessons, glossary, research queue |
| [archive/v1/](archive/v1/) | All v1 code, backtests, strategies, memory, prompts, plans. Read-only history |

New v2 code goes in a top-level `trading/` folder once Gate 1 work starts. Keep the top level this small.

## 5. My Stack (update as decisions get made)

- **Markets:** US-listed ETFs only. Canadian residents may not send API orders on Canadian-listed products (CIRO).
- **Paper broker:** IBKR paper `DUR239224`. The v1 robot (`archive/v1/run_signal.py`) is **archived and not scheduled**. Its IBKR adapter, Gateway workflow and FX conversion are in `archive/v1/brokers/` and `archive/v1/.github/workflows/` for reuse.
- **Live broker candidate:** IBKR Canada (account approved 2026-10-04). TFSA + API automation still unverified — ask IBKR in writing.
- **v2 objective (2026-10-18):** safety first, ~5–7%/yr, worst drop ≤ 20%. Pattern: "live = last row of the backtest" — one `target_weights(prices)` function shared by backtest and robot.
- **Python libs:** pandas, numpy. Battle-tested before hand-rolled.
- **Secrets:** `.env` only, never committed.
- **Logs:** every session ends with a dated entry in `journal/`.
- **History:** everything removed on 2026-10-18 is in git tag `archive/v1-2026-10-18`. Research pipeline: [docs/research-queue.md](docs/research-queue.md).

## 6. Strategies

No active strategy. v2 starts at Gate 1 with the multi-asset 200-day trend candidate in [docs/research-queue.md](docs/research-queue.md).

v1 strategies (all archived; their backtest numbers are **not reliable** — look-ahead exit and wrong-sign slippage found 2026-10-18): ma-crossover, crypto-trend, rsi2-connors, rsi2-multi. Specs in `archive/v1/strategies/`.

### Rejected experiments (do not retry without a new thesis)

- **Intraday (noise-area SPY momentum, last-half-hour momentum, 5-min ORB on QQQ)** — all failed pre-registered tests 2026-10-04 on 2016–2026 minute data with realistic costs. Best one (noise area) had OOS Sharpe 0.58 vs SPY 1.35 and ~0% since its 2024 publication. See `docs/research-queue.md` items 4–6.

- **Sector momentum (C, 1-month, top-2 of 5)** — failed pre-registered test 2026-10-03: MaxDD −65.3% vs SPY −55.2%, Sharpe 0.62 vs 0.64.
- **Dual momentum (GEM)** — failed 2026-10-03: Sharpe 0.61 vs 0.64 (full), 0.47 vs 0.74 (recent). Halves drawdowns — reuse only under a new pre-registered thesis.

- **rsi2-multi (6-ETF RSI(2))** — rejected 2026-10-02 after 4 months live-paper. Deployed 2026-06-01 in violation of the rsi2-connors rejection below. Execution lagged its backtest by a full session, it shared ma-crossover's Alpaca account (sold SPY it never owned), and its headline Sharpe 0.760 was never saved — the only results file says 0.215. Workflow `multi-agent-trade` disabled; positions flattened. See `archive/v1/strategies/rsi2_multi/STRATEGY.md §12`.

- **VIX25 regime gate** — rejected 2026-05-05. Filtered exactly one OOS trade and that trade was a +$1,763 winner (Nov-Dec 2022 reversal). High-VIX cross-ups on broad indices are reversal entries, not noise. See `journal/2026-05-05.md`. No re-tuning at thresholds 20/30 — the frame is wrong, not the number.
- **RSI(2) Connors mean-reversion** — rejected 2026-05-07. IS Sharpe 0.42, OOS Sharpe 0.31 (both below 0.5 bar). 200-DMA filter blocks too much of 2022 (bear) and RSI<10 readings too rare in 2023-24 (steady bull). Hard-stop variant strictly worse — confirms Connors original. Correlation 0.187 with ma-crossover OOS is genuinely low, BUT absolute return too weak (5% in 3 years) to be a useful diversifier on its own. See `archive/v1/strategies/rsi2_connors/STRATEGY.md §12`. Do not retry — the next strategy candidate is C (sector momentum) or D (crypto MA), not another mean-reversion variant.

## 7. Hard Rules (never break without a written waiver in this file)

- No live orders until all 3 gates in section 2 pass.
- No strategy change without a new dated entry in `journal/` and an updated `STRATEGY.md`.
- No deleting backtest logs. Losses are the training data.
- No "just tweak the parameters" loops — that is overfitting. If a strategy needs more than 2 parameter passes, re-examine the thesis in `docs/research-queue.md` first.
- Secrets live in `.env` only. Never commit keys, tokens, webhook URLs.
- Remote routines use environment variables and must push file changes back to GitHub if they are expected to persist state.
- MCP tokens are fat — reset sessions when context bloats (see [docs/PRINCIPLES.md](docs/PRINCIPLES.md) comment on token management).

## 8. When Claude Starts a New Session

1. Read this file.
2. Read the latest entry in [journal/](journal/) if one exists.
3. Read [docs/lessons.md](docs/lessons.md) — rules from past mistakes.
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
