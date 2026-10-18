# ROADMAP — Learn to Live

A stage-gated progression. You do not skip stages. You do not revisit earlier stages with real money.

---

## Stage 0 — Foundations (1-2 weeks)

**Goal:** understand what I am doing before I do it.

- [ ] Read [PRINCIPLES.md](PRINCIPLES.md) and [CLAUDE.md](CLAUDE.md) end to end.
- [ ] Build [knowledge/glossary.md](knowledge/glossary.md) entries for: OHLCV, slippage, commission, Sharpe, drawdown, win rate, risk/reward, position sizing, mean reversion, trend following, walk-forward, overfitting.
- [ ] Complete one research note on a market I want to trade (equities or crypto). Template in [research/README.md](research/README.md).
- [ ] Install the Alpaca paper account and confirm API key works (keep in `.env`).

**Gate to Stage 1:** I can explain OHLCV, Sharpe, drawdown, and overfitting in my own words without looking them up.

## Stage 1 — First Strategy on Paper Data (1-2 weeks)

**Goal:** design one strategy, spec it tightly, run it against historical data.

- [ ] Pick a simple, well-documented strategy. Candidates: moving-average crossover, mean reversion on RSI, breakout on volume. Not a custom ML model.
- [ ] Create `strategies/<name>/STRATEGY.md` using the template.
- [ ] Have Claude ask me 10 clarifying questions (per [PRINCIPLES.md](PRINCIPLES.md) #1).
- [ ] Write the signal function with a type-checked, unit-tested spec.
- [ ] Run the backtest on 2+ years of data. Log results under [backtests/](backtests/).
- [ ] Write a dated journal entry analyzing the result (what worked, what broke, what surprised me).

**Gate to Stage 2:** I have one strategy with a green backtest across at least 2 market regimes (e.g. 2022 bear + 2023 bull, or trending + choppy).

## Stage 2 — Paper Trading (minimum 2 weeks, realistically 4-8)

**Goal:** verify the strategy survives live market microstructure without real money at risk.

- [ ] Configure Alpaca paper account. See [tools/alpaca-setup.md](tools/alpaca-setup.md).
- [ ] Wire the strategy to pull live Alpaca data and submit paper orders.
- [ ] Run daily. Each day ends with a `journal/YYYY-MM-DD.md` entry including: trades placed, P&L, any deviation from backtest.
- [ ] Implement a **kill switch** (env var or file flag) to halt orders without restarting.
- [ ] Track: fill rate, actual slippage vs. modeled slippage, time-to-fill.

**Gate to Stage 3:**
- 2+ weeks of paper trading with the same rules as the backtest.
- Actual P&L within ±20% of backtest expectation.
- No unexplained trades.
- I have a written kill-switch procedure.

## Stage 3 — Tiny Live (months, not weeks)

**Goal:** trade real money in sizes small enough that the loss doesn't hurt.

- [ ] Fund Public.com account with an amount I can 100% lose without pain.
- [ ] Configure Public.com MCP. See [tools/public-com-setup.md](tools/public-com-setup.md).
- [ ] Trade the same strategy, same rules, smallest viable size.
- [ ] Keep paper trading the same strategy in parallel — the spread between the two is information.
- [ ] Weekly review in `journal/`: actual vs. paper vs. backtest. Any drift gets diagnosed before scaling.

**Gate to Stage 4:** 3+ months of live trading with positive risk-adjusted return AND explained every drawdown AND the paper<->live spread stays small.

## Stage 4 — Scale (months, still careful)

**Goal:** increase size carefully, add strategies, introduce the multi-agent workflow.

- [ ] Scale position size by a fixed factor (e.g. 2x) only if stage 3 gates hold for another month at the new size.
- [ ] Add a second uncorrelated strategy — different market, different timeframe, different signal.

---

## Non-negotiables at every stage

1. **Journal.** Every session, every trade, every change.
2. **No emotional overrides.** If I want to change the rules mid-trade, the rule is: stop trading, write it up in the journal, revisit after 24h.
3. **Size is the risk knob.** The strategy is the vehicle. The position size is the risk. Size controls survival.
4. **"It worked in backtest" is not an argument.** Paper then live.
