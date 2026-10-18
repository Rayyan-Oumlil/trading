# Prompt — Research a Stock / Market

Use this when starting research on a new ticker, sector, or market. Output lands in `research/<ticker-or-topic>.md`.

---

```
I want to research <TICKER or TOPIC>.

Before you answer, pull the latest data via MCP (TradingView for chart / Alpaca
for OHLCV / financial-datasets for fundamentals). Do not invent numbers.

Give me:

1. **What this asset is** — one paragraph, assume I'm a beginner.
2. **Key metrics** — price, market cap, 30d / 1y return, volatility (30d stdev
   of daily returns), average daily volume, 52-week high/low.
3. **Liquidity check** — is this tradeable at my size (start: <$500 positions)?
4. **Correlation** — vs. SPY for equities, vs. BTC for alts.
5. **Recent narrative** — last 3 material events (earnings, product launches,
   regulatory). Cite sources.
6. **Three strategy ideas** that might have an edge on this name, ranked by
   how testable they are.
7. **Risks I haven't asked about** — what would wipe out each idea above.

Save the output as `research/<slug>.md` with today's date in the frontmatter.
```

---

## Why this prompt

- Pulls live data (principle 4: MCP over pasted CSV).
- Demands specific numbers (principle 2: tight spec).
- Ends with a written artifact (principle 5: compound memory).
- Surfaces risks proactively (principle 6: AI is a research partner, not a cheerleader).
