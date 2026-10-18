# Live Trading — LOCKED

**This folder is gated.** Do not add strategies, orders, or credentials here until **all three gates** in [../CLAUDE.md](../CLAUDE.md) section 2 pass:

1. Profitable backtest across 2+ market regimes.
2. 2+ weeks of green paper trading matching the backtest.
3. I can explain every line of the strategy in my own words.

If I try to add content here before those gates pass, Claude should refuse and point me back to [../ROADMAP.md](../ROADMAP.md).

## When the gates pass

See [../tools/public-com-setup.md](../tools/public-com-setup.md) for the Public.com MCP that will handle real orders.

Expected structure once unlocked:

```
live-trading/
├── README.md
├── account.md           balance, funded date, size policy
├── log.md               every live trade, every day
├── position-sizing.md   current sizing policy (revise only in writing)
└── strategies-live/     symlinks to strategies/ with "live" stage
```

## First-live checklist (use when gates pass)

- [ ] Funded amount = no-pain amount (losing 100% doesn't affect life)
- [ ] Position sizing = smallest the broker allows (e.g. 1 share, 0.001 BTC)
- [ ] Kill switch tested on live, not just paper
- [ ] Spouse / accountant / whoever-needs-to-know is told
- [ ] Journal template ready
- [ ] Paper trading continues in parallel (the spread is information)
