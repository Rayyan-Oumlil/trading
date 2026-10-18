# Tools — Setup & Integration Notes

Every external tool I use in this workspace. Each has a setup doc and a note on when I would (and would not) use it.

| Doc | Purpose | Stage |
|-----|---------|-------|
| [mcp-servers.md](mcp-servers.md) | Claude Code MCP servers configured | all |
| [telegram-setup.md](telegram-setup.md) | Telegram bot alerts and optional command channel | 1+ |
| [tradingview-setup.md](tradingview-setup.md) | Desktop charting via MCP | all |

## Philosophy

- **Battle-tested > hand-rolled.** Default: use the community tool if it exists.
- **Every tool has a kill switch.** If I can't halt it, I don't run it.
- **Credentials in `.env`, never in code.** `.env` is gitignored.
- **Remote routines use environment variables, not `.env`.** Cloud runs do not inherit my local shell by magic.
- **MCP is fat.** Each enabled server consumes context on every turn. Unplug what I'm not using.
