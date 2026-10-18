# Prompt — Post-Trade / End-of-Day Review

Use this at the end of a paper or live trading session. Produces a `journal/YYYY-MM-DD.md` entry.

---

```
Session over. Let's log it.

1. Pull today's trades from <Alpaca MCP / Public.com MCP / freqtrade API>.
2. For each trade, tabulate:
   - symbol, side, entry time, exit time, entry price, exit price,
     size, P&L, strategy, reason (from journal / the bot log)
3. Aggregate:
   - number of trades, win rate, avg win, avg loss, profit factor,
     net P&L, gross exposure.
4. Compare to yesterday and to the 7-day rolling average.
5. Identify:
   - any trade that didn't match the strategy spec (discretionary override
     = red flag)
   - any fill that was materially worse than the modeled slippage
   - any strategy that underperformed its backtest expectation beyond
     normal noise
6. Ask me the reflection question: what did I learn today that I didn't
   know yesterday?

Write everything to `journal/YYYY-MM-DD.md` and append a summary line
to `paper-trading/log.md`.
```

---

## Why this prompt

- Trades logged, always (principle 5: compound memory).
- Compares to backtest (principle 6: drift between paper/live and backtest is the leading indicator of a dying strategy).
- Ends with reflection — the journal is where edge gets built, not the code.
