# Paper Broker Setup

Detailed Alpaca + freqtrade dry-run configuration. Stage 2 of [../ROADMAP.md](../ROADMAP.md).

## Alpaca (US equities)

1. Create a free account at https://alpaca.markets/ (paper trading — no real money required).
2. In the dashboard, go to **Paper Account → API Keys → Generate**.
3. Add to `.env` in the repo root (never commit):

```env
ALPACA_API_KEY=<your-key>
ALPACA_API_SECRET=<your-secret>
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

4. Install the SDK:

```bash
pip install alpaca-py
```

5. Smoke test:

```python
from alpaca.trading.client import TradingClient
import os
client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_API_SECRET"), paper=True)
print(client.get_account())
```

Expected output: account status = `ACTIVE`, paper buying power ~ $100k (default).

## Alpaca MCP server (optional, for Claude Code)

Install the community Alpaca MCP so Claude can place paper orders from inside a session:

```bash
pip install alpaca-mcp-server
```

Add to `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "alpaca-mcp-server",
      "args": [],
      "env": {
        "ALPACA_API_KEY": "${ALPACA_API_KEY}",
        "ALPACA_API_SECRET": "${ALPACA_API_SECRET}",
        "ALPACA_PAPER": "true"
      }
    }
  }
}
```

Restart Claude Code. Verify the `alpaca` MCP appears in the MCP list.

## Freqtrade (crypto dry-run)

Already configured at [../ft_userdata/config/config.json](../ft_userdata/config/config.json). Key settings:

- `dry_run: true`
- `dry_run_wallet: 1000` USDT (simulated)
- 5 max trades, $100 stake
- Pairs: BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, XRP/USDT

Start:

```bash
cd "C:/Users/rayya/Desktop/Claude Trading"
docker-compose up -d
```

UI at http://localhost:8080 (credentials in `config.json`).

Stop: see [kill-switch.md](kill-switch.md).

## Validation checklist before running a real paper strategy

- [ ] Broker API keys in `.env`, not in code
- [ ] `.env` is in `.gitignore`
- [ ] Smoke test passes (account endpoint returns ACTIVE)
- [ ] Kill switch tested (halt + verify)
- [ ] Journal entry template ready for end-of-day
- [ ] Position size is smallest viable (even paper — build the habit)
