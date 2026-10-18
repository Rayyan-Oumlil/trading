# Strategies

One folder per strategy. Each strategy is specified **before** it is coded. The `STRATEGY.md` file is the source of truth — code follows the spec, not the other way around.

## Layout

```
strategies/
├── README.md              (this file)
├── _template/
│   └── STRATEGY.md        (copy this to start a new strategy)
└── <strategy-name>/
    ├── STRATEGY.md        spec — entry, exit, sizing, assumptions
    ├── signal.py          signal function (pure, testable)
    ├── test_signal.py     unit tests — required
    ├── notes.md           design decisions, rejected alternatives
    └── runs/              symlinks to backtests/ and paper logs
```

## Naming

`<asset-class>-<idea>-<version>` — e.g. `crypto-mean-reversion-v1`, `equity-breakout-v2`.

## Creating a new strategy

1. Use [../prompts/design-strategy.md](../prompts/design-strategy.md) to extract the spec.
2. Copy `_template/STRATEGY.md` into `<name>/STRATEGY.md` and fill it in.
3. Add the strategy to `CLAUDE.md` section 6 with its stage.
4. Only then write code.

## Stages

- `research` — idea only, no code
- `backtest` — code exists, running on historical data
- `paper` — running on Alpaca paper
- `live` — running with real money (gated by [../ROADMAP.md](../ROADMAP.md))
- `archived` — killed, kept for reference (never deleted)
