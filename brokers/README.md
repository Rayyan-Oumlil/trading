# Brokers

`run_signal.py` executes on the broker named by `BROKER` (default `alpaca`).

| BROKER | Where it runs | Account | Notes |
|---|---|---|---|
| `alpaca` | GitHub Actions (nightly) | Alpaca paper — the **reference** | unchanged |
| `ibkr` | a machine running IB Gateway (your PC for now) | IBKR paper (`DU…`) — the **mirror** | logs to `memory/confidence-log-ibkr.md` |

## IBKR adapter (`brokers/ibkr.py`) — what it does

- US-listed stocks/ETFs only (API orders on Canadian-listed products are blocked for Canadian residents — CIRO rule).
- Orders: market-on-open (MKT, TIF=OPG), **whole shares** only.
- Account values in **USD** (base currency is CAD): equity = net liquidation ÷ USD rate; only **USD cash** can buy. Convert CAD→USD once in IBKR.
- Crypto sleeves are skipped until the crypto-via-ETF test (roadmap idea 0) passes.
- **Live gate:** a non-paper account is refused unless `LIVE_TRADING=1` **and** `live-trading/ARMED` exist.

## Set up the IBKR paper account (once)

1. Open an IBKR Canada account (IBKR Pro, **cash** account) and get it approved and funded.
2. Client Portal → Settings → Paper Trading Account → request it (ready within ~24 h, 1,000,000 USD fictitious).
3. Install **IB Gateway (stable)** from IBKR. Log in with the **paper** username.
4. Gateway → Configure → Settings → API → Settings:
   - Enable ActiveX and Socket Clients
   - Socket port **4002** (paper default)
   - Uncheck **Read-Only API** (the robot must place orders)
   - Trusted IPs: `127.0.0.1`
5. In IBKR, convert some CAD to USD (paper: already USD).
6. Check the connection (read-only): `python -m brokers.ibkr_smoke`

## Run the mirror (after the smoke test passes)

```
set BROKER=ibkr
python run_signal.py
```

Optional env: `IBKR_HOST` (127.0.0.1), `IBKR_PORT` (4002), `IBKR_CLIENT_ID` (17).
