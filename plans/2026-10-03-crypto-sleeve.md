---
created: 2026-10-03
objective: Paper-trade the crypto-trend strategy (backtest PASSED 2026-10-03) as a 10% sleeve of the single Alpaca account, with one robot owning every order.
approved: Rayyan, 2026-10-03 ("yes … continue non stop"; sleeve size defaulted to the recommended 10%)
---

# Crypto Sleeve — Plan

## Decisions

| Topic | Decision | Why |
|---|---|---|
| Ownership | **One robot** (`run_signal.py`) places every order in the account | Two order-placers in one account caused the July collision |
| Sleeves | SPY **85.5%** of equity (90% sleeve × 95% invested, keeps the old 5% buffer) · BTC/USD **5%** · ETH/USD **5%** | 10% crypto; a repeat of the −60.5% backtest drawdown costs ~6% of the account |
| Trade semantics | Per symbol, trade **only on a state flip** (flat→long buys `weight × equity` notional; long→flat sells all). No drift rebalancing | Matches both backtests (ma-crossover and the crypto run traded only on flips) |
| ma-crossover sizing | Changes from "95% of cash" to "85.5% of equity" | Equity-based sleeves can't starve each other; cash-based sizing let one strategy eat the other's cash |
| Signals | SPY: SMA10 > SMA50 on completed US sessions (unchanged). Crypto: SMA10 > SMA50 on completed **UTC days** from Alpaca crypto bars (drop the in-progress day) | Identical to the pre-registered backtests |
| Schedule | One EOD run **daily, 7 days**, after 00:00 UTC (Windows task 20:10 ET, GHA cron `20 0 * * *` fallback). SPY orders still queue for the next open, as today | Crypto's day closes at 00:00 UTC; SPY's session is long closed by then |
| Idempotency | Robot skips a symbol already logged for its session/day; per-symbol open-order check | GHA fallback + weekend runs must never double-trade or log contradictions |
| Log format | `DATE \| DECISION \| score \| SYMBOL: reason` (legacy lines without a prefix = SPY) | Desk checks conflicts per symbol |
| Crypto orders | Market, `GTC` (Alpaca rejects `DAY` for crypto); buys by notional, sells full position qty | Alpaca crypto rules |
| Desk | Allowed symbols {SPY, BTCUSD, ETHUSD}; conflicts per symbol; desk cron moves to `30 1 * * *`-style after robot | Desk must run after the robot in both EDT and EST |

## Tasks (TDD each)

1. `paper_trading/crypto_data.py` — completed-UTC-day bars, NaN/stale guards.
2. `AlpacaClient` — time-in-force per order, notional buys; symbol mapping `BTC/USD ↔ BTCUSD`.
3. `strategies/portfolio.py` — sleeves, flip decision, `already_decided`.
4. `run_signal.py` — loop sleeves with the existing guards; per-symbol logs.
5. `routines_pkg/desk_snapshot.py` — allowed set, per-symbol conflict check.
6. Workflow cron, Windows task, docs: `strategies/crypto_trend/STRATEGY.md`, ma-crossover §6, journal, CLAUDE.md, desk prompt.
7. Live read-only dry run + Alpaca-vs-yfinance SMA parity for BTC/ETH; final review; push before Monday 2026-10-05 16:00 ET.
