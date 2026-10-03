# Weekly — 2026-W40 (desk, 2026-10-03T00:26:46Z)

**Return:** account +3.44% vs SPY +9.19% since start (-5.74pp). Max DD -4.54% (kill threshold 2x backtest DD = ~24.8%, far away).
**Trades:** SPY sell 09-29 (NaN-driven liquidation, 125.05 sh); GLD buy 09-30; IWM buy 10-01; GLD/IWM sells queued 10-02 for Mon open.
**Flags this week:** nan_in_log (acknowledged), foreign_position_closing (alert). No halts by the desk.
**Learned:** the account lags SPY mostly because a NaN bar forced two false full liquidations and ~97% cash since 09-29; the fixes (Alpaca bars, NaN guard, desk snapshot, Telegram alerts) landed this week.

**Proposals (max 3):**
1. Fix the log writer so the margin field never prints "nan" and lines are newline-separated (code change -> would be a desk/<slug> PR; not opened tonight).
2. Add a snapshot flag for a stale Gate 2 re-run (target was 2026-05-21, no re-run found).
3. Lessons.md addition: "A halt flag that stays red after its fix is deployed means the detector reads historical log lines — scope it to post-fix lines or acknowledge per session."

### Addendum — 2026-10-03T00:57:54Z (second desk firing)
- Since the first weekly: crypto-trend went to paper (BTC 5% + ETH 5%), ma-crossover now sizes at 85.5% of equity, and bef2db2 fixed the review findings. Tests: 140 passed.
- Market this week: S&P 500 down for the week despite +0.7% Friday. September payrolls were weak (+29K). Source: thestreet.com and CNN, read from search snippets.
- Proposed lessons.md addition: "A scheduled routine can fire twice for one session. The desk should check whether it already logged that session and append only the changes, not a second full brief."
