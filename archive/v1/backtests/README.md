# Backtests

Every backtest run lives here, in a folder named by run-id. **Never delete a run.** Losses and failed tests are training data.

## Layout

```
backtests/
├── README.md                  (this file)
└── <strategy>-<YYYY-MM-DD>-<nn>/
    ├── config.yml             exact parameters of the run
    ├── equity.csv             equity curve
    ├── trades.csv             per-trade log
    ├── metrics.json           Sharpe, drawdown, win rate, etc.
    ├── chart.png              equity vs benchmark
    └── review.md              output of prompts/backtest-review.md
```

## Run-id convention

`<strategy-slug>-<date>-<sequence>`
e.g. `crypto-mean-reversion-v1-2026-04-19-01`

First run of the day = `-01`. Re-runs with different params = `-02`, `-03`, ...

## Metrics to log (minimum)

- Total return %
- Annualized return %
- Annualized Sharpe (risk-free = 0 unless noted)
- Max drawdown % + date range
- Win rate
- Profit factor (gross profit / gross loss)
- Number of trades
- Avg holding period
- Benchmark total return over same window
- Active return (strategy - benchmark)

## Red flags in a run

- < 30 trades total -> variance estimate is noise
- Sharpe > 3 -> almost certainly overfit or a bug
- Win rate > 70% with < 2 R/R -> look for a survivorship or look-ahead bug
- All of the return in one week -> one-trick pony, probably won't repeat
- Slippage modeled at 0 bps -> redo with realistic fills

## Reproducibility

Every `config.yml` must include the exact library versions used. `pip freeze > config.yml` is not enough — the strategy commit hash goes in too.
