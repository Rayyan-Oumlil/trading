# TradingView — Desktop Charting via MCP

Claude inspects TradingView Desktop charts via the Chrome DevTools Protocol.

## Status

Configured globally at `~/.claude/.mcp.json`. MCP entry:

```json
{
  "tradingview": {
    "command": "C:/Users/rayya/AppData/Local/Programs/Python/Python311/Scripts/tradingview-mcp.exe",
    "args": [],
    "env": {}
  }
}
```

## How to use

1. Launch TradingView Desktop with the remote debugging flag:
   ```
   "C:\Path\To\TradingView.exe" --remote-debugging-port=9222
   ```
2. Open the chart/symbol you want Claude to inspect.
3. Claude reads via the MCP. It does NOT draw or click — read-only.

## When to use

- "Show me what this strategy is doing at today's signal on SPY 1h chart."
- "What does the current MACD histogram say for BTC 4h?"
- Sanity check a backtest entry against the human-visible chart.

## When NOT to use

- Bulk data pulls — use Alpaca/CCXT instead. TradingView via DevTools is slow.
- Indicators you could recompute locally. Don't burn the token budget.

## Alternatives

If TradingView Desktop is too flaky on Windows, swap for the pip-based `tradingview-mcp-server` which uses the public TV web interface. Less accurate on custom indicators, more portable.
