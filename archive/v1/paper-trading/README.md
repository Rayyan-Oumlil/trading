# Paper Trading

Where strategies live after they pass a backtest but before any real money. This is the proving ground for [ROADMAP.md](../ROADMAP.md) stage 2.

## Files

- [log.md](log.md) — daily one-line summary of every paper session
- [broker-setup.md](broker-setup.md) — Alpaca + freqtrade paper account procedures
- [kill-switch.md](kill-switch.md) — how to halt all paper orders without restarting

## Daily workflow

1. Morning: [../prompts/daily-plan.md](../prompts/daily-plan.md)
2. The strategy runs (Alpaca or freqtrade dry-run) against live data, submits paper orders.
3. End of day: [../prompts/post-trade-review.md](../prompts/post-trade-review.md) creates [../journal/YYYY-MM-DD.md](../journal/) and appends one line to [log.md](log.md).

## Exit criteria to graduate to live

See [ROADMAP.md](../ROADMAP.md) stage 2 gates. In short:
- 2+ weeks of consistent rules-following
- Paper P&L within ±20% of backtest expectation
- Kill switch tested
- No discretionary overrides

## Common failures at this stage

- **Slippage reality check:** backtest assumed 5 bps, paper shows 30+ bps on illiquid names -> strategy P&L craters.
- **Fill rate surprise:** limit orders that looked good in backtest don't fill at all in live queues.
- **Latency:** end-of-bar fills in backtest are start-of-next-bar fills in live -> different entry price.
- **Earnings / halts:** backtest had no halt logic and earnings skipped. Live, the stock opens 10% up.

When any of these show up, document in the daily journal, not in the strategy code. The strategy code changes ONLY after a pattern is clear over multiple days.
