# Confidence Log

One line per day. The agent appends to this file at the end of each daily routine.

Format: `YYYY-MM-DD | DECISION | N/10 | <one-phrase reason>`

The point of this log: after 4+ weeks, sort by confidence and check whether high-conviction days outperformed low-conviction days. If they don't, the confidence scoring is uncalibrated and needs a rule revision.

---

## Entries

```
2026-04-24 | HOLD | 7/10 | position open, no regime change (seed entry, pre-multi-agent)
```
2026-05-07 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.48% (pre-market)
2026-05-07 | HOLD | 7/10 | weekly close: all agents bullish, Iran deal risk-on, no MA cross
2026-05-07 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.45%
2026-05-07 | HALT | 0/10 | kill switch active
2026-05-07 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.44%
2026-05-07 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.44%
2026-05-07 | HOLD | 7/10 | post-EOD reflection: regime stable, sanity-checks clean, NFP+CPI flags noted (no action) [reconstructed — routine push 403]
2026-05-08 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.63%
2026-05-11 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.82%
2026-05-12 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.04%
2026-05-13 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.29%
2026-05-14 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.52%
2026-05-15 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.60%
2026-05-18 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.69%
2026-05-19 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.66%
2026-05-20 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.56%
2026-05-21 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.51%
2026-05-22 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.38%
2026-05-25 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.38%
2026-05-26 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.26%
2026-05-27 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.19%
2026-05-28 | HOLD | 7/10 | position aligned with regime; fast-slow margin +6.10%
2026-05-29 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.93%
2026-06-01 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.90%

2026-06-02 | SCAN | 6/10 | entries=['XLE'] exits=[] [multi] [multi]
2026-06-02 | 1BUY+0SELL | 6/10 | entered=['XLE'] closed=[] [multi] [multi]2026-06-02 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.87%

2026-06-02 | 1BUY+1SELL | 6/10 | entered=['XLE'] closed=['XLE'] [multi] [multi]
2026-06-03 | SCAN | 6/10 | entries=[] exits=['XLE'] [multi] [multi]
2026-06-03 | 0BUY+1SELL | 6/10 | entered=[] closed=['XLE'] [multi] [multi]2026-06-03 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.86%

2026-06-04 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-04 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-04 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.77%

2026-06-05 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-05 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-05 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.46%

2026-06-08 | SCAN | 6/10 | entries=['SPY', 'QQQ', 'XLK'] exits=[] [multi] [multi]
2026-06-08 | 3BUY+0SELL | 6/10 | entered=['SPY', 'QQQ', 'XLK'] closed=[] [multi] [multi]2026-06-08 | HOLD | 7/10 | position aligned with regime; fast-slow margin +5.09%

2026-06-09 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-09 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-09 | HOLD | 7/10 | position aligned with regime; fast-slow margin +4.60%

2026-06-10 | SCAN | 6/10 | entries=['GLD'] exits=[] [multi] [multi]
2026-06-10 | 1BUY+0SELL | 6/10 | entered=['GLD'] closed=[] [multi] [multi]2026-06-10 | HOLD | 7/10 | position aligned with regime; fast-slow margin +3.98%

2026-06-11 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-11 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-11 | HOLD | 7/10 | position aligned with regime; fast-slow margin +3.50%

2026-06-12 | SCAN | 6/10 | entries=[] exits=['SPY', 'QQQ', 'XLK'] [multi] [multi]
2026-06-12 | 0BUY+3SELL | 6/10 | entered=[] closed=['SPY', 'QQQ', 'XLK'] [multi] [multi]2026-06-12 | HOLD | 7/10 | position aligned with regime; fast-slow margin +3.05%

2026-06-15 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-15 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-15 | HOLD | 7/10 | position aligned with regime; fast-slow margin +2.71%

2026-06-16 | SCAN | 6/10 | entries=[] exits=['GLD'] [multi] [multi]
2026-06-16 | 0BUY+1SELL | 6/10 | entered=[] closed=['GLD'] [multi] [multi]2026-06-16 | HOLD | 7/10 | position aligned with regime; fast-slow margin +2.33%

2026-06-17 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-17 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-17 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.92%

2026-06-18 | SCAN | 6/10 | entries=['XLE'] exits=[] [multi] [multi]
2026-06-18 | 1BUY+0SELL | 6/10 | entered=['XLE'] closed=[] [multi] [multi]2026-06-18 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.58%

2026-06-19 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-19 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-19 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.60%

2026-06-22 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-22 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-22 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.53%

2026-06-23 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-23 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-23 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.33%

2026-06-24 | SCAN | 6/10 | entries=['GLD'] exits=['XLE'] [multi] [multi]
2026-06-24 | 1BUY+1SELL | 6/10 | entered=['GLD'] closed=['XLE'] [multi] [multi]2026-06-24 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.16%

2026-06-25 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-25 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-25 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.20%

2026-06-26 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-26 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-26 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.02%

2026-06-29 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-29 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-29 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.92%

2026-06-30 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-06-30 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-06-30 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.73%

2026-07-01 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-07-01 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-07-01 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.59%

2026-07-02 | SCAN | 6/10 | entries=['XLE'] exits=['GLD'] [multi] [multi]
2026-07-02 | 1BUY+1SELL | 6/10 | entered=['XLE'] closed=['GLD'] [multi] [multi]2026-07-02 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.55%

2026-07-03 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-07-03 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-07-03 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.55%

2026-07-06 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-07-06 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-07-06 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.50%

2026-07-07 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-07-07 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-07-07 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.43%

2026-07-08 | SCAN | 6/10 | entries=[] exits=['XLE'] [multi] [multi]
2026-07-08 | 0BUY+1SELL | 6/10 | entered=[] closed=['XLE'] [multi] [multi]2026-07-08 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.50%

2026-07-09 | SCAN | 6/10 | entries=['IWM'] exits=[] [multi] [multi]
2026-07-09 | 1BUY+0SELL | 6/10 | entered=['IWM'] closed=[] [multi] [multi]2026-07-09 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.64%

2026-07-10 | SCAN | 6/10 | entries=[] exits=['IWM'] [multi] [multi]
2026-07-10 | 0BUY+1SELL | 6/10 | entered=[] closed=['IWM'] [multi] [multi]2026-07-10 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.80%

2026-07-13 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]
2026-07-13 | HOLD | 6/10 | entered=[] closed=[] [multi] [multi]2026-07-13 | HOLD | 7/10 | position aligned with regime; fast-slow margin +0.97%

2026-07-14 | SCAN | 6/10 | entries=['GLD'] exits=[] [multi] [multi]
2026-07-14 | 1BUY+0SELL | 6/10 | entered=['GLD'] closed=[] [multi] [multi]2026-07-14 | HOLD | 7/10 | position aligned with regime; fast-slow margin +1.02%

2026-07-15 | SCAN | 6/10 | entries=[] exits=[] [multi] [multi]