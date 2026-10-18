# Prompt — Design a Strategy (plan-first)

Use this when I have a trading idea but no spec. Output lands in `strategies/<name>/STRATEGY.md`.

---

```
I have a strategy idea: <one-paragraph-idea>.

DO NOT write code yet.

Instead, ask me every question you need answered before we could write a
clean backtest. Group questions by:

1. Universe (what assets, when, what filters).
2. Bar / timeframe.
3. Entry signal (exact formula, including edge cases: missing data, halts,
   after-hours, gaps).
4. Exit rules (stop-loss, take-profit, time-stop, reversal).
5. Position sizing (fixed $, fixed %, vol-scaled, Kelly).
6. Execution assumptions (slippage, commission, fill model).
7. Backtest design (walk-forward or fixed? in-sample/out-of-sample split?).
8. What "success" looks like (target Sharpe, max drawdown, min trades/year).

After I answer, write the strategy spec to
`strategies/<slug>/STRATEGY.md` using the template from
`strategies/_template/STRATEGY.md`. Then stop. We run the backtest in a
separate session.
```

---

## Why this prompt

- Forces the plan step before any code (principle 1).
- Treats Claude as a junior quant (principle 2): extracts the 10 decisions
  that would otherwise be hallucinated.
- Persists the spec to disk (principle 5).
- Separates design from execution — one session per phase, so context stays tight.
