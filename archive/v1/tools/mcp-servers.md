# MCP Servers

Config lives at `~/.claude/.mcp.json` (global). Project-level overrides can go in `<workspace>/.mcp.json` (not checked in).

## Currently configured

| Name | Purpose | Status |
|------|---------|--------|
| tradingview | Chart inspection via TradingView Desktop | Active |
| alpaca | Paper broker API — account, positions, orders | Active (paper) |

## Planned (add as the roadmap progresses)

| Name | Purpose | When to add |
|------|---------|-------------|
| alpaca | Paper broker API + OHLCV | Stage 1/2 |
| financial-datasets | Fundamentals, earnings, filings | Stage 1 |
| public-com | Live broker API | Stage 3 only |
| web-fetch (built-in) | News / filings / research | Always on |

## API-backed services used by routines

These are part of the operating stack even when they are not exposed as standalone MCP servers.

| Name | Purpose | Stage | Key(s) |
|------|---------|-------|--------|
| perplexity | Fast catalyst and narrative research | 0+ | `PERPLEXITY_API_KEY` |
| telegram | Urgent alerts + mobile command channel + sentiment/news aggregation | 1+ | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| clickup | End-of-day and weekly summary delivery | 1+ | `CLICKUP_API_TOKEN` |

## Skills.md: The Automation Foundation

All local + remote routines depend on a `skills.md` file in their working folder. This file defines:
- Exchange API connections (keys encrypted, never sent to servers)
- The `/trade-*` command set (16+ skills for equities, crypto, research)
- Multi-agent workflows (5 parallel: technical + fundamentals + sentiment + risk + thesis)
- Webhook handlers (TradingView signals → trade execution)


## Supported Exchanges (encrypted local keys)

- **Crypto futures:** Binance, Bybit, Blofin, OKX, WEX, Tubbit (2bit)
- **Crypto spot:** same as above
- **Equities paper:** Alpaca (MCP)
- **Equities live:** Public.com (Stage 3+, MCP)
- **Options:** Through TradingView webhook

API keys are never shared with servers. Request signing happens on machine; keys stay local.

## Routine-specific note

For remote Claude routines, do **not** assume the run can read my local `.env`.

The routine prompt must reference the exact environment-variable names configured in the Claude environment. If the prompt asks for `ALPACA_API_SECRET` but the environment contains `ALPACA_SECRET`, the run will fail. Exact naming matters.

## How to add a new MCP

1. `pip install <package>` or `npm install -g <package>`.
2. Add to `~/.claude/.mcp.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "<name>": {
      "command": "<executable>",
      "args": [],
      "env": {
        "KEY": "${KEY_FROM_DOTENV}"
      }
    }
  }
}
```

3. Restart Claude Code.
4. Verify: `/mcp` inside Claude Code should list the new server.
5. Document here with the install command + verification step.

## Token bloat management

MCP tool descriptions are sent on every turn. Every enabled server costs tokens whether I use it or not.

- Keep only the servers I use in the current stage.
- If I'm doing pure research (no execution), don't need broker MCPs.
- If I'm backtesting historical, don't need live-data MCPs.
- Use `/mcp` to list active servers and disable ones I'm not using this session.
- Keep notification channels quiet by default. Alerts should be selective, not a running chat transcript.

## Debugging a dead MCP

1. Is the executable path resolvable? (on Windows, often the full path is needed)
2. Are env vars present in `.env` AND being interpolated correctly?
3. Does `/mcp` list it as connected or errored?
4. Last resort: `claude --debug` to see stderr from the MCP process.
