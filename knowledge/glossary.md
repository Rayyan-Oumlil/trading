# Glossary

Every term, in my own words. Add as I learn. Update when my understanding improves.

---

## Data

**OHLCV.** One bar of market data: Open, High, Low, Close, Volume. Any timeframe (1m, 1h, 1d).

**Bar / candle.** One period of OHLCV. A "1h bar" aggregates trades over one hour.

**Tick.** A single trade. Tick data is raw, massive, usually unnecessary for beginner strategies.

**Spread.** Difference between best bid and best ask at a moment. Wider = less liquid = costlier to trade.

**Slippage.** Difference between the price you intended vs. the price you got. Biggest hidden cost for beginners.

**Adjusted close.** Close price adjusted for splits (and optionally dividends). Use for backtests across corporate actions.

**Routine / cron.** A scheduled job that wakes up at a fixed time and runs the same workflow without me manually opening a session.

**Local routine.** A routine that runs on my own machine. Easy to test, but it stops if my computer or Claude Desktop is off.

**Remote routine.** A routine that runs in Claude's cloud environment. Better for dependable weekday schedules, but it only remembers what gets written to files and pushed back to GitHub.

---

## Metrics (what backtest reports try to tell me)

**Return %.** P&L as a % of starting equity. Raw, doesn't say anything about risk.

**Annualized return.** Return scaled to a 1-year basis so 6-month vs 3-month results are comparable.

**Sharpe ratio.** `(return - risk_free) / std_of_returns`, annualized. Measures return per unit of volatility. >1 is ok, >2 is great, >3 is suspicious (probably overfit).

**Max drawdown.** Largest peak-to-trough equity decline. Measures the worst pain the strategy has caused.

**Win rate.** Fraction of trades that were profitable. Alone, useless — a 30% win rate with 3:1 R/R beats a 70% win rate with 0.5:1 R/R.

**Profit factor.** `gross_profit / gross_loss`. >1 means strategy made money overall. 1.5+ is decent.

**Expectancy.** `(win_rate × avg_win) - (loss_rate × avg_loss)`. Per-trade expected value.

**R multiple.** P&L of a trade expressed in units of the risk per trade (R). A +3R trade made 3x the planned risk.

---

## Risk

**Position size.** How much capital in one trade. The #1 lever. Strategy = vehicle, size = risk.

**Risk per trade.** Usually % of equity (e.g. 1%). Fixed-percent sizing means losses shrink position auto.

**Stop-loss.** Pre-defined exit price for a losing trade. Without one, a loser becomes a bag-holder.

**Take-profit.** Pre-defined exit for a winner. Optional — trailing stops are an alternative.

**Trailing stop.** A stop that ratchets in my favor as price moves in my favor, but does not widen when price moves against me.

**Kelly fraction.** Sizing formula: `f = (p*b - q) / b` where p = win prob, b = win/loss ratio, q = 1-p. Theoretically optimal for geometric growth. Practically, use a fraction of Kelly (quarter Kelly) because Kelly assumes perfect knowledge of p and b.

**Correlation.** How much two positions move together. Portfolio of correlated assets = one big bet, not diversification.

---

## Strategy families

**Trend following.** Buy higher highs, sell lower lows. Loses in chop, wins in trends. Low win rate, high avg win.

**Mean reversion.** Fade extremes — buy low, sell high around a running mean. Wins in range, loses in trends. High win rate, low avg win.

**Breakout.** Enter when price crosses a level (support/resistance, range high/low). Works when volatility expands.

**Carry.** Hold something that pays you to hold it (dividends, funding rates). Rare as a standalone edge.

**Arbitrage.** Two prices should be equal; trade the difference. True arbs are rare; "statistical arb" is "we bet they converge".

---

## Markets / instruments

**Equity / stock.** Share of a company. Long = bet it goes up.

**Option.** Right (not obligation) to buy (call) or sell (put) an asset at a strike price before expiry. Non-linear payoff.

**Future.** Obligation to exchange an asset at a fixed price in the future. Leveraged.

**ETF.** Basket of assets tradeable like a stock. SPY = S&P 500.

**Perp (perpetual swap).** Crypto future with no expiry. Funded continuously by funding rate.

**Funding rate.** The periodic payment between longs and shorts on perpetual futures that keeps the perp anchored to spot. Positive funding means longs pay shorts; negative funding means shorts pay longs.

**Sub-account.** A separate exchange account under the same master login, used to isolate capital, permissions, or strategy risk.

**Paper mode.** A setting where the system behaves like it is trading, but routes to a paper broker or simulated account instead of real money.

---

## Pitfalls

**Overfitting.** Model fits historical noise, not signal. Signs: high Sharpe on in-sample + poor on OOS, many parameters, short history.

**Look-ahead bias.** Using data in a backtest that wouldn't have been available at the trade time. #1 beginner bug. Example: using today's close to decide today's entry.

**Survivorship bias.** Backtesting a strategy on today's index constituents across history — ignores delisted losers. Real universe had more losers.

**Data snooping.** Trying many strategies on the same data until one "works" by chance. Multiple-hypothesis problem.

**Webhook.** An HTTP endpoint that receives an event from another system, like a TradingView alert that tells a routine or broker bridge to act.

**Pine Script.** TradingView's scripting language for indicators, alerts, and strategy backtests.

**Efficient Market Hypothesis (EMH).** The market quickly incorporates information. If a simple pattern printed money, it would already be arbitraged away. Corollary: if a strategy looks too easy, look harder.

**Regime shift.** A strategy that worked in 2015-2019 low-vol may fail in 2022 high-vol. No edge is permanent.

---

## Technical Indicators

**ATR (Average True Range).** Volatility measure: average of `max(high-low, |high-prev_close|, |low-prev_close|)` over N bars. Used to size stops in proportion to recent volatility.

**ADX (Average Directional Index).** Trend strength (0-100). >25 = trending, <20 = ranging. Does NOT indicate direction — use +DI/-DI for that.

**RSI (Relative Strength Index).** `100 - 100/(1 + avg_gain/avg_loss)` over N periods. 0-100. >70 = overbought, <30 = oversold in range markets. In trends, these levels lose meaning.

**MACD.** `EMA(12) - EMA(26)`. Signal line = `EMA(MACD, 9)`. Histogram = MACD - signal. Used to spot momentum shifts.

**Bollinger Bands.** `SMA(N) ± k * std(N)`. Default N=20, k=2. Price touching upper band ≠ sell signal; in strong trends it "walks the band".

**VWAP (Volume-Weighted Average Price).** Cumulative `(price × volume) / cumulative_volume` since open. Intraday benchmark. Institutional traders care about it; daily bar traders less so.

---

## Order Types

**Market order.** Execute immediately at best available price. Guaranteed fill, not guaranteed price. Use only in liquid markets.

**Limit order.** Execute only at your specified price or better. No guaranteed fill.

**Stop order.** Triggers a market order when price touches the stop level. Gap risk: can fill far past stop in fast markets.

**Stop-limit order.** Triggers a limit (not market) order at the stop. Avoids gap-fill risk but may not fill at all.

**Trailing stop (order type).** Stop that advances with price in your favor but does not retreat. Locks in profit progressively.

**Bracket order.** Entry + take-profit + stop-loss in one atomic submission. All three active until one fires.

**Iceberg order.** Large order split into small visible slices to hide size. Not relevant at retail scale.

---

## Backtesting Methodology

**In-sample (IS).** The data period used to design and tune the strategy. Never used for final evaluation.

**Out-of-sample (OOS).** Data the strategy has never "seen" during design. The only valid performance estimate.

**Walk-forward test.** Roll a fixed IS window forward in time, test each resulting OOS window. Produces multiple OOS periods, reduces fluke risk.

**Train/test split.** Simplest OOS check: e.g., use 2018-2022 to design, test on 2023-2024. At least 20% of data should be OOS.

---

## Regulatory & Account

**PDT (Pattern Day Trader) rule.** US regulation: if you make 4+ day trades in 5 business days in a margin account under $25k, your account is flagged PDT and day trading is restricted. Paper accounts are not subject to this, but build the habit of knowing it.

**Margin.** Borrowed capital from the broker. Amplifies gains and losses. Requires maintaining a minimum equity level.

**Maintenance margin.** Minimum account equity percentage to hold a leveraged position. Fall below it → margin call.

**Margin call.** Broker demands you deposit more cash or they will liquidate positions to bring you back above maintenance.

**Short selling.** Borrowing shares to sell them, expecting to buy back cheaper. Requires "locate" (borrow availability). HTB = hard to borrow; costs extra.

**Implied volatility (IV).** The market's forward-looking vol estimate, implied by option prices via Black-Scholes. Higher IV = more expensive options.

**Realized volatility.** Historical volatility actually observed in price moves. Compare to IV: if IV > realized, options are expensive (good to sell premium, risky to buy).

**Greeks.** Option sensitivity measures:
- Delta: $ change in option per $1 change in underlying.
- Gamma: rate of delta change per $1 change in underlying.
- Theta: time decay — value lost per day as expiry approaches.
- Vega: $ change per 1% change in implied volatility.

**Paper vs simulated vs live.**
- Paper: real market prices, fake money (Alpaca paper account). Best pre-live environment.
- Simulated: backtest replay, idealized fills. Useful but not a paper substitute.
- Live: real money, real fills, real slippage. Only after Stage 2 gates pass.
