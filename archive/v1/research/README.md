# Research

Notes on tickers, markets, asset classes, strategy families, workflow design, and concepts. One file per topic.

## Naming

- Ticker: `<ticker>.md` — e.g. `spy.md`, `btc-usdt.md`
- Theme: `<slug>.md` — e.g. `mean-reversion-on-large-caps.md`
- Concept: `<slug>.md` — e.g. `vix-term-structure.md`
- Workflow / tooling: `<slug>.md` — e.g. `claude-routines-trading-system.md`

## Template for a ticker research note

```markdown
---
ticker: <TICKER>
class: equity | crypto | etf | future | option
researched: YYYY-MM-DD
next-review: YYYY-MM-DD
---

# <Ticker> — Research Note

## What it is
(one paragraph, beginner-friendly)

## Current state (as of YYYY-MM-DD via <MCP source>)
- Price:
- Market cap:
- 30d return / 1y return:
- 30d realized vol (daily stdev × √252):
- ADV (avg daily $ volume):
- 52w high / low:

## Liquidity
Can I trade this at $500 / $1000 / $5000 notional without moving the tape?

## Correlations
- vs SPY: ρ(30d) = ?
- vs BTC: ρ(30d) = ?
- vs sector ETF: ρ(30d) = ?

## Recent narrative
Last 3 material events with dates and sources.

## Strategy ideas for this name
1. ... (and why testable)
2. ...
3. ...

## Risks
For each idea above, what kills it.

## Links
Filings, earnings call summary, on-chain data, etc.
```

## Workflow

Use [../prompts/research-stock.md](../prompts/research-stock.md) to generate the first draft. Keep iterating — research notes are living documents.
