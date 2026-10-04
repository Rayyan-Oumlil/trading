# IBKR paper becomes the only account (2026-10-04)

**Decision (Rayyan, 2026-10-04):** the robot trades the IBKR paper account `DUR239224` by itself, every evening, from GitHub. One Telegram message per evening. Alpaca retired.

## What the research settled

| Question | Answer | Source |
|---|---|---|
| Can the robot send orders for Canadian-listed ETFs (VFV, BTCC…)? | **No.** CIRO (ex-IIROC) DMR 3200 forbids client-owned automated order systems on Canadian marketplaces; IBKR returns *"API/CTCI orders for canadian stocks are not allowed"*. | [QuantConnect forum](https://www.quantconnect.com/forum/discussion/7303/canadians-not-allowed-to-use-interactive-brokers-api-anymore/), [twsapi group](https://groups.io/g/twsapi/topic/api_ctci_orders_for_canadian/74083342), [Portfolio123](https://community.portfolio123.com/t/canada-trading-with-interactive-brokers-is-now-enabled/70876) |
| US-listed ETFs via API from a Canadian account? | **Yes.** | same |
| Can GitHub log in unattended? | **Paper: yes.** IBKR dropped 2FA for paper accounts (March 2026). Live logins still need IB Key. | [gnzsnz/ib-gateway-docker #126](https://github.com/gnzsnz/ib-gateway-docker/discussions/126) |
| How? | `ghcr.io/gnzsnz/ib-gateway:stable` (IB Gateway + IBC), `TRADING_MODE=paper`, paper API on container port 4004. | [gnzsnz/ib-gateway-docker](https://github.com/gnzsnz/ib-gateway-docker) |

So: **automatic = US-listed ETFs only.** Canadian ETFs remain possible only by hand.

## What changed

| Sleeve | Before (Alpaca) | Now (IBKR paper) | Signal (unchanged) |
|---|---|---|---|
| S&P 500, 85.5% | SPY | SPY | SMA10/50 on SPY, completed US sessions |
| Bitcoin, 5% | BTC/USD coin, 24/7 | **IBIT** (iShares Bitcoin Trust) | SMA10/50 on BTC-USD, completed UTC days |
| Ether, 5% | ETH/USD coin, 24/7 | **ETHA** (iShares Ethereum Trust) | SMA10/50 on ETH-USD, completed UTC days |

- Orders: market-on-open, whole shares, capped at **USD cash** (never borrows).
- Data: Yahoo Finance (yfinance), adjusted daily bars. Holidays need no calendar (no bar = no session).
- One run per evening after the close; crypto flips on a weekend are acted on Monday evening (the ETF can't trade before).
- Telegram: one report per evening (equity, day P&L, vs SPY, positions, robot decisions, queued orders, fills, flags, halt). Failures still alert separately.

**Execution deviation from the crypto backtest:** the backtest bought the coin at the next UTC day's open; the ETF fills at the next US open, up to ~3 days later after a weekend flip, and carries a 0.25% fee. That is exactly what roadmap idea 0 ("crypto via ETF") needs measured — this paper run is that measurement.

## One-time setup (Rayyan)

1. Wait for the paper account to activate (next business day).
2. Log in once at the Client Portal with the **paper** username; in the paper account, convert about 1,000,000 CAD of fake money to USD (Trade → Currency Conversion) — otherwise the robot has no USD cash and will say so every evening.
3. GitHub → repo `trading` → Settings → Secrets and variables → Actions → add `IBKR_USERNAME` (paper username) and `IBKR_PASSWORD` (paper password).
4. Actions → daily-trade → Run workflow. Expect one Telegram message.

## Risks to watch in the first week

- IBKR may throttle logins from GitHub's datacenter IPs → run would fail with "IB Gateway not reachable". Fallback: run the same workflow on a self-hosted runner (your PC).
- Paper fills without a market-data subscription: unverified. The fill-deviation check (2% SPY, 5% ETFs) will flag nonsense fills.
- OPG (market-on-open) acceptance on SMART-routed ETFs in paper: unverified; a rejection fails the run loudly.
