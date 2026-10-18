# Prompt — Review a Backtest

Use this right after a backtest finishes. Output is a dated entry in `journal/` and an updated `STRATEGY.md`.

---

```
Backtest just finished. The run is at
`backtests/<run-id>/` — read the config, the trade log, and the metrics.

Tell me:

1. **Headline** — final equity, Sharpe, max drawdown, win rate, profit
   factor, number of trades. One line each, with units.
2. **Versus benchmark** — compare to buy-and-hold of the same universe
   over the same window. Did the strategy earn its complexity?
3. **Regime breakdown** — split the window into trending vs. chopping
   (use ADX or any simple rule), and show metrics for each. Does it work
   in both?
4. **Worst trade and best trade** — one of each, with the chart context
   and what the strategy "thought" it was doing.
5. **Smells** — anything suspicious. Examples: 90% of returns from one
   week, unrealistically tight stops never hitting, suspiciously high
   win rate (>70% = look harder).
6. **Verdict** — one of:
   - ship to paper
   - re-spec and re-run (say what to change in STRATEGY.md)
   - kill the idea

Write the review to `journal/YYYY-MM-DD-backtest-<slug>.md`. If verdict
is "ship to paper", update the strategy stage in `CLAUDE.md` section 6.
```

---

## Why this prompt

- Compares to benchmark (principle 6: AI is a research partner; without a benchmark, any positive return looks like a win).
- Splits by regime — survives principle 6's EMH reality check.
- Names the smells — overfitting detection is the #1 skill in this stage.
- Forces a verdict — avoids the "just tweak one parameter" loop (principle 5 corollary).
