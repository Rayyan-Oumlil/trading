# The Seven Principles — 900 Hours, Compressed

Distilled from ~1,000 hours of other people's mistakes using Claude for trading, plus community consensus on what actually works vs. what doesn't. These are non-negotiable defaults for this workspace.

---

## 1. Plan Before You Build

The #1 failure mode: describe a strategy in one paragraph -> ask Claude to write the backtest -> get 200 lines of code -> debug errors for 3 hours -> realize the spec was wrong in the first place.

**The fix:** before any code, say *"Ask me every question you need to answer before we write a line of code."*

Typical questions Claude will surface:
- What is the universe? (SPX 500? Top 100 crypto by volume? A specific watchlist?)
- What is the bar? (1m / 5m / 1h / 1d?)
- Entry signal: exact formula, not intuition.
- Exit: stop-loss, take-profit, time stop, reversal?
- Position sizing: fixed $, fixed %, vol-scaled, Kelly?
- What do you do at halts / earnings / gaps / weekends / low volume?
- Slippage / commission assumptions?
- Walk-forward or fixed window backtest?

Making these decisions during planning costs nothing. Making them after 300 lines of code costs a full afternoon.

## 2. Treat Claude Like a Junior Quant with ADHD

Capable, fast, can build things you couldn't build alone in a week. But left with a vague brief, it guesses, and it guesses confidently.

**Bad:** "Build a backtest for mean reversion."

**Good:** "Write a Python function `calculate_signals(df)` where `df` has columns `[date, close, volume]`. Return a boolean column `signal` that is True when the 10-day return exceeds 5% and today's volume is above 1.5x its 20-day average. Nothing else."

My job is not to code. My job is to make the instructions tight enough that Claude's guesses are correct ones.

## 3. Voice Your Strategy, Type the Spec

Typed prompts are short because you edit yourself. Voice prompts are 2-3x longer and more specific because you add context naturally ("…but only when volume is above average, because that's when the signal is actually clean").

Workflow: record a voice note describing the strategy, paste the transcript into Claude, ask Claude to turn it into a structured spec, then write the spec to `strategies/<name>/STRATEGY.md`.

## 4. MCP Servers = Live Context

MCP is the USB port that plugs Claude into live data — broker APIs, market feeds, charting tools. Instead of downloading a CSV and pasting it, point Claude at the source.

Configured in this workspace (see [tools/mcp-servers.md](tools/mcp-servers.md)):
- **TradingView** — chart inspection
- **Alpaca** — paper trading execution + historical data (planned)
- **Public.com** — live execution (when we get there)
- **Financial datasets** — fundamentals (planned)

**Warning:** MCP is a fat protocol. Every tool description consumes tokens. Unplug servers you aren't using this session, and reset context when it bloats.

## 5. CLAUDE.md = Permanent Memory (Compound Engineering)

Every new session without `CLAUDE.md` = re-explain data format, broker setup, signals, risk rules from scratch. That's the first 15 minutes of every session wasted.

With `CLAUDE.md`, Claude reads it automatically. Month two, Claude knows my setup before I've typed a word.

This is **compound engineering** — same idea as compounding returns, applied to context. Every decision captured in `CLAUDE.md` or `journal/` makes every future session faster and smarter.

## 6. AI Is a Research Partner, Not an Oracle

Hard truth from [the community](https://www.reddit.com/r/learnmachinelearning/comments/16m3gx7/): most autonomous AI trading bots lose. The efficient market hypothesis is not a joke — if a simple pattern made money, it would be arbitraged away.

**Where AI wins:**
- Faster research loops (scan 500 tickers in minutes, not days).
- Better journaling and pattern recognition across trades.
- Spec-driven code that is testable and reproducible.
- Removing emotion from execution (once the rules are set).

**Where AI loses:**
- Pretending to predict price from chart patterns alone.
- Overfit ML models on limited history.
- "Autonomous" black-box bots with no journal.

**Therefore:** default posture is **human-in-the-loop, research-heavy, paper-first**. Full automation is the end state, not the starting state.

## 7. Routines Are Stateless; Files Are the Memory

A Claude routine does not wake up with durable memory. It wakes up with a prompt, the files it chooses to read, and whatever environment variables exist for that run.

That means the real system is not \"one smart agent\". It is a stateless agent plus durable files.

The operating loop is:

1. Read the smallest useful set of memory files.
2. Do the job.
3. Write back anything the next run must know.

For remote runs, there is one extra requirement: the updated files must be committed and pushed back to GitHub. If the run clones a repo, edits files, and the environment is destroyed without a push, the next run starts cold again.

Defaults for routine-based trading:

- Secrets come from environment variables, not committed files.
- Local routines are for testing; remote routines are for dependable schedules.
- Every new routine gets `Run now` tested before it is trusted.
- Notification channels are exception paths, not spam sinks.
- Token budget is part of the design. Read active memory, not the entire repo.

---

## Corollary Rules

- **Statistical logs are the deliverable.** Every backtest / paper trade ends with a `journal/YYYY-MM-DD.md` entry. No exceptions.
- **Don't tweak in a loop.** If a strategy needs >2 parameter passes, the thesis is wrong. Revisit `research/`.
- **Don't trust Claude with math without a second tool.** Always verify Sharpe, drawdown, win rate with a library function, not a one-off calculation.
- **Kill switches > stop losses.** Always have a way to halt the bot by hand.
- **Backtest != paper != live.** Each is a different animal. The transition between them is where most strategies die.
- **Remote routine without write-back = amnesia.** If memory files are not pushed back to GitHub, the next run forgets them.
