---
created: 2026-10-02
objective: Turn the paper system from "runs every day" into "trustworthy enough to risk real money on" — then find an edge that actually beats SPY.
mode: phased. Phase 1 is fully specified below (TDD, executable now). Phases 2-4 get their own detailed plan when the previous gate passes.
source: repo audit 2026-10-02 (see journal/2026-10-02.md once written)
---

# Make It Real — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every bug that is corrupting the paper record, close the alerting loop so the next bug reaches Rayyan within minutes instead of never, then use clean data to find (or rule out) a strategy that beats buy-and-hold SPY.

**Architecture:** Keep the deterministic robot (GHA + Python) as the only thing that touches orders. Swap its data source from yfinance to Alpaca (same vendor as the broker, market-calendar aware), add hard guards (NaN, stale data, foreign positions, rejected/duplicate orders) that fail loudly, and route every failure/trade to Telegram. Claude Code routines stay read-only narrators/auditors whose output lands on `master` and pings the phone.

**Tech Stack:** Python 3.11, alpaca-py 0.43.2 (trading + market data), pandas, pytest, GitHub Actions, cron-job.org (precise trigger), Telegram Bot API (urllib, no new dependency), Claude Code routines.

**Spec:** this file + audit findings below. Strategy spec of record: `strategies/ma_crossover/STRATEGY.md`.

## Why — audit findings this plan answers (2026-10-02)

| # | Finding | Evidence |
|---|---|---|
| F1 | yfinance returns a NaN last row on GHA → `NaN > NaN` = False → full SPY liquidation | SELLs 09-22 and 09-29 logged `margin +nan%`; flat in cash since 09-29 while SMA10 767.9 > SMA50 762.2 |
| F2 | ma-crossover and rsi2-multi share one Alpaca account, both trade SPY | 07-21 multi SPY buy **rejected**, ledger recorded it anyway, 07-23 multi "sold" 3.26 SPY belonging to ma-crossover |
| F3 | Failed orders are booked as fills; ledger never reconciled with broker | same as F2 |
| F4 | rsi2-multi executes one full session later than its backtest | signal close t → fill open t+2 (backtest: t+1) |
| F5 | GHA cron 3–5 h late; dates come from `datetime.now(UTC)` | EOD runs ~00:20–00:57 UTC next day → journal/confidence-log on the wrong date |
| F6 | "3-agent" LLM layer never ran (no `ANTHROPIC_API_KEY`) | 176 `[multi]` log lines, all deterministic |
| F7 | daily-reflection routine **caught F1 on 09-29** but nobody saw it | 76 `claude/peaceful-cannon-*` branches never merged; routine notifications off |
| F8 | rsi2-multi went live against CLAUDE.md §6 ("no more mean-reversion variants"); its "Sharpe 0.760" isn't on disk, the only results file says 0.215; spec contradicts itself (stop / time-stop) | `backtests/rsi2_multi/results/oos_2022_2024.json`, `strategies/rsi2_multi/STRATEGY.md` §5 vs §11 |
| F9 | Net result: account +3.4% vs SPY +7.8% (2026-04-23 → 10-02) | Alpaca portfolio history |

## Global Constraints

- Paper only. `paper=True` stays hardcoded; `ALPACA_PAPER_TRADE == "true"` gate in workflows stays.
- No strategy parameter changes in Phase 1. Fixes are data/execution integrity only (CLAUDE.md §7: no "tweak the parameters" loops).
- Every failure path raises; no silent fallbacks (no `except: pass`, no `or 50.0` defaults for indicators).
- Secrets only via `.env` locally and GitHub/routine secrets remotely: `ALPACA_API_KEY`, `ALPACA_API_SECRET`, `ALPACA_PAPER_TRADE`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GH_DISPATCH_PAT` (cron-job.org only).
- Every behavior change gets a dated `journal/` entry (CLAUDE.md §7).
- Conventional commits (`fix:`, `feat:`, `chore:`, `docs:`).
- Test command for the project (excludes vendored freqtrade/skills): `python -m pytest -q` (after Task 1 adds `pytest.ini`).

## Review Focus

1. **Duplicate trigger** (cron-job.org dispatch + GHA fallback cron both fire): the second run must see the pending after-hours order and do nothing — pinned in Task 5 (`has_open_order`) and Task 6 (`PENDING` branch).
2. **Run before the close** (manual dispatch at 14:00 ET, or holiday half-day at 13:00 ET): must use the *previous completed* session and drop today's partial bar — pinned in Task 3 (half-day test) and Task 4 (partial-bar filter test).
3. **Stale data** (Alpaca returns nothing for the latest session): must refuse to trade, not trade on yesterday's bar as if it were today's — pinned in Task 4 (`stale` test).
4. **Rejected order**: must raise and leave a red GHA run, never log a BUY — pinned in Task 5 (`order_failed`) and Task 6.
5. **Alert channel broken** (Telegram secrets missing): must raise with a clear message, not pretend the alert went out — pinned in Task 7.

---

# PHASE 1 — Stop the bleeding (target: this week)

**Gate to leave Phase 1:** 5 consecutive trading days with (a) zero red runs or every red run explained, (b) confidence-log date == session date, (c) one deliberate failure (Task 7 Step 6) reached the phone, (d) broker positions == expected positions every day.

### Task 1: Ship the NaN fix with a test gate in CI

Already done locally (uncommitted): `run_signal.py` `clean_bars()` + NaN guard in `current_regime()`, tests in `tests_run_signal/test_run_signal.py` (4 tests, all 40 project tests green).

**Files:**
- Create: `pytest.ini`
- Modify: `.github/workflows/daily-trade.yml` (add test step)
- Commit: `run_signal.py`, `tests_run_signal/test_run_signal.py`

- [ ] **Step 1: Restrict pytest to project code** (bare `pytest` currently errors on 60 vendored freqtrade/skills tests)

```ini
[pytest]
testpaths = paper_trading routines_pkg strategies backtests tests_run_signal
```

- [ ] **Step 2: Run** `python -m pytest -q` → Expected: `40 passed`
- [ ] **Step 3: Add the test gate to `daily-trade.yml`**, immediately after "Install dependencies":

```yaml
      - name: Run tests (no trading on a red suite)
        run: python -m pytest -q
```

- [ ] **Step 4: Commit and push**

```bash
git add pytest.ini run_signal.py tests_run_signal/ .github/workflows/daily-trade.yml
git commit -m "fix: refuse to trade on NaN bars; run test suite before every routine"
git push
```

- [ ] **Step 5: Verify** `gh workflow run daily-trade.yml -f mode=premarket` → `gh run watch` → green, "Run tests" step shows `40 passed`. **Do not dispatch `eod` manually during market hours** — it would buy ~$93k SPY on a partial bar (that hole is closed in Task 6).

### Task 2: Pause rsi2-multi and flatten its positions

Decision (Rayyan confirms before Step 2): rsi2-multi is **rejected**, not paused-for-later — F4 lag, F8 rule violation, 0.215 Sharpe on disk.

**Files:**
- Modify: `strategies/rsi2_multi/STRATEGY.md` (stage → rejected, §12 add row)
- Modify: `CLAUDE.md` §6 (add rsi2-multi to rejected list)
- Create: `journal/2026-10-02.md` section "Audit + rsi2-multi shutdown"

- [ ] **Step 1: Disable the workflow** — `gh workflow disable multi-agent-trade` → `gh workflow list` shows `disabled_manually`.
- [ ] **Step 2: Flatten its broker positions** (current: GLD 6.62, IWM 8.97 — re-check first):

```bash
python - <<'EOF'
from dotenv import load_dotenv; load_dotenv(".env")
from paper_trading.alpaca_client import AlpacaClient
c = AlpacaClient()
for p in c.get_positions():
    if p["symbol"] != "SPY":
        r = c.place_market_order(p["symbol"], p["qty"], "sell")
        print(p["symbol"], p["qty"], r.status)
EOF
```

Expected: two sells, status `accepted`/`new` (fill at next open). Next day: `get_positions()` contains only SPY (or nothing).
- [ ] **Step 3: Update docs.** STRATEGY.md frontmatter `stage: rejected`; §12 add row `2026-10-02 | live-paper review | Rejected: execution lag t+2 vs backtest t+1, shared-account collision, claimed Sharpe 0.760 not reproducible (file on disk: 0.215)`. CLAUDE.md §6 add a "Rejected experiments" bullet with the same facts. Journal entry lists F1–F9.
- [ ] **Step 4: Lesson** — append to `tasks/lessons.md`: *"A strategy goes live only from a results file on disk produced by a committed script. No file, no deploy. And no two strategies share one broker account."*
- [ ] **Step 5: Commit** `git commit -m "chore: reject rsi2-multi, disable its workflow, record 2026-10-02 audit"` and push.

### Task 3: Market-calendar session date

Every date the robot writes must be the **trading session it acted on**, not the UTC wall clock (F5).

**Files:**
- Create: `paper_trading/market_calendar.py`
- Modify: `paper_trading/alpaca_client.py` (add `get_calendar`)
- Test: `paper_trading/tests/test_market_calendar.py`, `paper_trading/tests/test_alpaca_client.py`

**Interfaces:**
- Produces: `last_completed_session(now_utc: datetime, sessions: list[tuple[date, time]]) -> date`; `AlpacaClient.get_calendar(start: date, end: date) -> list[tuple[date, time]]` (close time in America/New_York).

- [ ] **Step 1: Write the failing tests**

```python
from datetime import date, datetime, time, timezone

import pytest

from paper_trading.market_calendar import last_completed_session

REGULAR = [(date(2026, 10, 1), time(16, 0)), (date(2026, 10, 2), time(16, 0))]


def test_after_close_returns_today():
    now = datetime(2026, 10, 2, 20, 30, tzinfo=timezone.utc)  # 16:30 EDT
    assert last_completed_session(now, REGULAR) == date(2026, 10, 2)


def test_during_session_returns_previous_session():
    now = datetime(2026, 10, 2, 19, 0, tzinfo=timezone.utc)  # 15:00 EDT
    assert last_completed_session(now, REGULAR) == date(2026, 10, 1)


def test_late_gha_run_after_midnight_utc_keeps_session_date():
    now = datetime(2026, 10, 3, 0, 45, tzinfo=timezone.utc)  # 20:45 EDT 10-02
    assert last_completed_session(now, REGULAR) == date(2026, 10, 2)


def test_half_day_close_counts_after_1pm():
    sessions = [(date(2026, 11, 25), time(16, 0)), (date(2026, 11, 27), time(13, 0))]
    now = datetime(2026, 11, 27, 18, 30, tzinfo=timezone.utc)  # 13:30 EST
    assert last_completed_session(now, sessions) == date(2026, 11, 27)


def test_raises_when_no_session_completed():
    now = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(RuntimeError):
        last_completed_session(now, REGULAR)
```

- [ ] **Step 2: Run** `python -m pytest paper_trading/tests/test_market_calendar.py -v` → FAIL (`ModuleNotFoundError`)
- [ ] **Step 3: Implement**

```python
"""Trading-session dates from the exchange calendar, not the UTC wall clock."""
from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")


def last_completed_session(now_utc: datetime, sessions: list[tuple[date, time]]) -> date:
    completed = [d for d, close in sessions if datetime.combine(d, close, tzinfo=NEW_YORK) <= now_utc]
    if not completed:
        raise RuntimeError(f"No completed session at {now_utc.isoformat()} in calendar window")
    return max(completed)
```

- [ ] **Step 4: Add `get_calendar` to `AlpacaClient`** — failing test first (append to `test_alpaca_client.py`):

```python
class TestGetCalendar:
    def test_returns_date_and_close_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from datetime import date, datetime, time
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        day = MagicMock()
        day.date = date(2026, 11, 27)
        day.close = datetime(2026, 11, 27, 13, 0)
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_calendar.return_value = [day]
            result = AlpacaClient().get_calendar(date(2026, 11, 20), date(2026, 11, 27))
        assert result == [(date(2026, 11, 27), time(13, 0))]
```

Implementation (add import `from datetime import date, datetime, time` and `GetCalendarRequest` to the requests import):

```python
    def get_calendar(self, start: date, end: date) -> list[tuple[date, time]]:
        days = self._client.get_calendar(GetCalendarRequest(start=start, end=end))
        return [(d.date, d.close.time() if isinstance(d.close, datetime) else d.close) for d in days]
```

- [ ] **Step 5: Run** `python -m pytest -q` → all pass.
- [ ] **Step 6: Commit** `git commit -m "feat: derive trading-session date from Alpaca calendar"`

### Task 4: Alpaca daily bars (replace yfinance in the live path)

**Files:**
- Create: `paper_trading/market_data.py`
- Test: `paper_trading/tests/test_market_data.py`

**Interfaces:**
- Consumes: session `date` from Task 3.
- Produces: `bars_to_frame(raw: pd.DataFrame, symbol: str, last_session: date) -> pd.DataFrame` (pure; lowercase OHLCV, DatetimeIndex of session dates, completed sessions only, no NaN close, last row == `last_session` else `RuntimeError`); `get_daily_bars(symbol: str, lookback_days: int, last_session: date) -> pd.DataFrame`.

- [ ] **Step 1: Write the failing tests**

```python
from datetime import date

import numpy as np
import pandas as pd
import pytest

from paper_trading.market_data import bars_to_frame


def _raw(days: list[str], closes: list[float]) -> pd.DataFrame:
    # Alpaca stamps daily bars at midnight New York (04:00 UTC during EDT).
    idx = pd.MultiIndex.from_tuples(
        [("SPY", pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=4)) for d in days],
        names=["symbol", "timestamp"],
    )
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes,
         "volume": [1_000.0] * len(days), "trade_count": [1.0] * len(days), "vwap": closes},
        index=idx,
    )


def test_drops_partial_session_after_last_completed():
    raw = _raw(["2026-09-30", "2026-10-01", "2026-10-02"], [760.0, 764.0, 769.0])
    df = bars_to_frame(raw, "SPY", date(2026, 10, 1))
    assert list(df.index.date) == [date(2026, 9, 30), date(2026, 10, 1)]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_drops_nan_close_rows():
    raw = _raw(["2026-09-30", "2026-10-01"], [760.0, 764.0])
    raw.iloc[0, raw.columns.get_loc("close")] = np.nan
    df = bars_to_frame(raw, "SPY", date(2026, 10, 1))
    assert len(df) == 1


def test_raises_when_latest_session_missing():
    raw = _raw(["2026-09-30"], [760.0])
    with pytest.raises(RuntimeError, match="stale"):
        bars_to_frame(raw, "SPY", date(2026, 10, 1))
```

- [ ] **Step 2: Run** → FAIL (`ModuleNotFoundError`)
- [ ] **Step 3: Implement**

```python
"""Daily OHLCV from Alpaca (same vendor as the broker). Completed sessions only."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

SIP_DELAY = timedelta(minutes=16)  # free plan serves SIP data older than 15 min
OHLCV = ["open", "high", "low", "close", "volume"]


def bars_to_frame(raw: pd.DataFrame, symbol: str, last_session: date) -> pd.DataFrame:
    df = raw.xs(symbol, level="symbol") if isinstance(raw.index, pd.MultiIndex) else raw
    df = df[OHLCV].copy()
    df.index = pd.DatetimeIndex(df.index.tz_convert("America/New_York").date)
    df = df[df.index.date <= last_session].dropna(subset=["close"])
    if df.empty or df.index[-1].date() != last_session:
        latest = df.index[-1].date() if not df.empty else None
        raise RuntimeError(f"{symbol} data stale: latest bar {latest}, expected {last_session}")
    return df


def get_daily_bars(symbol: str, lookback_days: int, last_session: date) -> pd.DataFrame:
    client = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_API_SECRET"])
    end = datetime.now(timezone.utc) - SIP_DELAY
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=end - timedelta(days=lookback_days),
        end=end,
        feed=DataFeed.SIP,
        adjustment=Adjustment.ALL,
    )
    raw = client.get_stock_bars(request).df
    if raw.empty:
        raise RuntimeError(f"Alpaca returned no bars for {symbol}")
    return bars_to_frame(raw, symbol, last_session)
```

- [ ] **Step 4: Run** `python -m pytest -q` → all pass.
- [ ] **Step 5: Parity check against the backtest's data source** (the backtest used yfinance adjusted closes; the SMAs must agree or the live signal ≠ the backtested one):

```bash
python - <<'EOF'
from datetime import date
from dotenv import load_dotenv; load_dotenv(".env")
import yfinance as yf
from paper_trading.market_data import get_daily_bars
session = date(2026, 10, 1)  # set to the last completed session
a = get_daily_bars("SPY", 120, session)["close"]
y = yf.download("SPY", period="120d", auto_adjust=True, progress=False)["Close"].squeeze()
y.index = y.index.normalize()
for n in (10, 50):
    sa, sy = a.rolling(n).mean().iloc[-1], y.loc[:str(session)].rolling(n).mean().iloc[-1]
    print(n, round(sa, 2), round(sy, 2), f"{abs(sa - sy) / sy:.4%}")
EOF
```

Expected: both diffs < 0.10%. If not → stop, journal it, decide data source before Task 6.
- [ ] **Step 6: Commit** `git commit -m "feat: Alpaca daily bars with stale/partial/NaN guards"`

### Task 5: Order guards — duplicates, rejections, foreign positions

**Files:**
- Modify: `paper_trading/alpaca_client.py` (add `has_open_order`)
- Create: `paper_trading/guards.py`
- Test: `paper_trading/tests/test_guards.py`, `paper_trading/tests/test_alpaca_client.py`

**Interfaces:**
- Produces: `order_failed(status: str) -> bool`; `assert_only_expected_positions(positions: list[dict], allowed: set[str]) -> None`; `AlpacaClient.has_open_order(symbol: str) -> bool`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from paper_trading.guards import assert_only_expected_positions, order_failed


@pytest.mark.parametrize("status", ["OrderStatus.REJECTED", "rejected", "OrderStatus.CANCELED", "expired"])
def test_failed_statuses(status):
    assert order_failed(status)


@pytest.mark.parametrize("status", ["OrderStatus.ACCEPTED", "new", "filled", "OrderStatus.PENDING_NEW"])
def test_live_statuses(status):
    assert not order_failed(status)


def test_foreign_position_raises():
    with pytest.raises(RuntimeError, match="GLD"):
        assert_only_expected_positions([{"symbol": "SPY"}, {"symbol": "GLD"}], allowed={"SPY"})


def test_expected_positions_pass():
    assert_only_expected_positions([{"symbol": "SPY"}], allowed={"SPY"})
    assert_only_expected_positions([], allowed={"SPY"})
```

`has_open_order` test (append to `test_alpaca_client.py`):

```python
class TestHasOpenOrder:
    def test_true_when_open_order_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_orders.return_value = [MagicMock()]
            assert AlpacaClient().has_open_order("SPY") is True

    def test_false_when_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPACA_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("paper_trading.alpaca_client.TradingClient") as mock_tc:
            mock_tc.return_value.get_orders.return_value = []
            assert AlpacaClient().has_open_order("SPY") is False
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement** `paper_trading/guards.py`:

```python
"""Hard pre/post-trade checks. Each one raises or returns a bool — never logs and continues."""
from __future__ import annotations

_FAILED = {"rejected", "canceled", "expired", "suspended"}


def order_failed(status: str) -> bool:
    return status.lower().rsplit(".", 1)[-1] in _FAILED


def assert_only_expected_positions(positions: list[dict], allowed: set[str]) -> None:
    foreign = sorted(p["symbol"] for p in positions if p["symbol"] not in allowed)
    if foreign:
        raise RuntimeError(f"Unexpected positions {foreign}: another strategy or a manual trade is in this account")
```

and in `AlpacaClient` (imports: `GetOrdersRequest`, `QueryOrderStatus`):

```python
    def has_open_order(self, symbol: str) -> bool:
        orders = self._client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol]))
        return len(orders) > 0
```

- [ ] **Step 4: Run** `python -m pytest -q` → all pass.
- [ ] **Step 5: Commit** `git commit -m "feat: order/position guards (duplicate, rejected, foreign)"`

### Task 6: Wire guards + Alpaca data + session date into the robot

**Files:**
- Modify: `run_signal.py` (`main`, `append_confidence`; delete `fetch_bars` + `yfinance` import)
- Modify: `routines_pkg/eod_close.py:152` (session date)
- Test: `tests_run_signal/test_run_signal.py` (existing 4 tests must stay green)

**Interfaces:**
- Consumes: `last_completed_session`, `AlpacaClient.get_calendar`, `get_daily_bars`, `clean_bars`, `order_failed`, `assert_only_expected_positions`, `AlpacaClient.has_open_order`.

- [ ] **Step 0: Imports** — `run_signal.py`: replace `import yfinance as yf` and the datetime import with

```python
from datetime import date, datetime, timedelta, timezone
```

and add after the existing project imports:

```python
from paper_trading.guards import assert_only_expected_positions, order_failed  # noqa: E402
from paper_trading.market_calendar import last_completed_session  # noqa: E402
from paper_trading.market_data import get_daily_bars  # noqa: E402
```

`routines_pkg/eod_close.py`: add `timedelta` to its datetime import and `from paper_trading.market_calendar import last_completed_session`.

- [ ] **Step 1: Session-dated confidence log**

```python
def append_confidence(session: date, decision: str, score: int, reason: str) -> None:
    """Append one line to memory/confidence-log.md, dated by trading session."""
    line = f"{session.isoformat()} | {decision} | {score}/10 | {reason}\n"
    CONFIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONFIDENCE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)
```

The HALT branch runs before the calendar is known: give it `datetime.now(timezone.utc).date()`.

- [ ] **Step 2: Replace the top of `main()` (after the halt check) through the position lookup**

```python
    client = AlpacaClient()
    now = datetime.now(timezone.utc)
    session = last_completed_session(now, client.get_calendar(now.date() - timedelta(days=10), now.date()))

    print(f"Fetching {TICKER} bars through session {session}...")
    df = clean_bars(get_daily_bars(TICKER, lookback_days=120, last_session=session))
    sma_fast, sma_slow, should_be_long = current_regime(df)
    last_close = float(df["close"].iloc[-1])
    last_date = str(df.index[-1].date())
    # ... existing prints unchanged ...

    account = client.get_account()
    positions = client.get_positions()
    assert_only_expected_positions(positions, allowed={TICKER})
    spy_pos = next((p for p in positions if p["symbol"] == TICKER), None)

    if client.has_open_order(TICKER):
        print("\nPENDING — an order for this session is already queued. Nothing to do.")
        append_confidence(session, "PENDING", 6, "open order exists; duplicate run skipped")
        return 0
```

`fetch_bars` previously called `clean_bars`; now `get_daily_bars` output goes through `clean_bars` explicitly (keeps the ≥50-bar check). Delete `fetch_bars` and `import yfinance`.

- [ ] **Step 3: After each `place_market_order` call (BUY and SELL branches)**

```python
        if order_failed(result.status):
            raise RuntimeError(f"{TICKER} order {result.order_id} failed with status {result.status}")
```

and pass `session` as first arg to every `append_confidence` call.

- [ ] **Step 4: `eod_close.py`** — replace line 152:

```python
    now = datetime.now(timezone.utc)
    session = last_completed_session(now, client.get_calendar(now.date() - timedelta(days=10), now.date()))
    date_str = session.isoformat()
```

- [ ] **Step 5: Run** `python -m pytest -q` → all pass. Then dry-run read-only pieces live:

```bash
python -c "from dotenv import load_dotenv; load_dotenv('.env'); from datetime import datetime, timezone, timedelta; from paper_trading.alpaca_client import AlpacaClient; from paper_trading.market_calendar import last_completed_session; from paper_trading.market_data import get_daily_bars; import run_signal as r; c=AlpacaClient(); n=datetime.now(timezone.utc); s=last_completed_session(n, c.get_calendar(n.date()-timedelta(days=10), n.date())); df=r.clean_bars(get_daily_bars('SPY',120,s)); print(s, r.current_regime(df))"
```

Expected: last session date and `(fast, slow, True/False)` with finite numbers.
- [ ] **Step 6: Commit, push, then journal** the first live EOD: what it did and why. Expected after F1: **BUY** ~95% cash SPY at next open (regime bullish since ~09-24). That re-entry is the system correcting the bug, not a new trade idea — say so in the journal.

```bash
git commit -m "fix: session-dated, Alpaca-sourced, guarded ma-crossover executor"
```

### Task 7: Telegram alerts — failures, trades, halts

**Files:**
- Create: `paper_trading/notify.py`
- Test: `paper_trading/tests/test_notify.py`
- Modify: `.github/workflows/daily-trade.yml`

- [ ] **Step 1: Failing test**

```python
import pytest

from paper_trading.notify import send_telegram


def test_missing_credentials_raise(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(RuntimeError, match="TELEGRAM"):
        send_telegram("hello")
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**

```python
"""Telegram alerts. Missing credentials are an error, never a silent skip."""
from __future__ import annotations

import json
import os
import sys
import urllib.request


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set")
    body = json.dumps({"chat_id": chat_id, "text": text[:4000]}).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"Telegram HTTP {response.status}")


if __name__ == "__main__":
    send_telegram(" ".join(sys.argv[1:]))
```

- [ ] **Step 4: Setup (Rayyan, 5 min):** Telegram → @BotFather → `/newbot` → token; message the bot once; `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id`. Add both to `.env` and `gh secret set TELEGRAM_BOT_TOKEN` / `gh secret set TELEGRAM_CHAT_ID`.
- [ ] **Step 5: Workflow** — add to job `env:` the two secrets, then append these steps after the commit step:

```yaml
      - name: Alert on trade or halt
        if: success()
        shell: bash
        run: |
          last="$(tail -n 1 memory/confidence-log.md)"
          if echo "$last" | grep -qE '\| (BUY|SELL|HALT|PENDING) \|'; then
            python -m paper_trading.notify "daily-trade ${{ steps.mode.outputs.mode }}: $last"
          fi

      - name: Alert on failure
        if: failure()
        run: python -m paper_trading.notify "daily-trade ${{ steps.mode.outputs.mode }} FAILED - ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
```

Also add `if: always()` to "Commit memory + journal updates" so a failed run still persists what it wrote.
- [ ] **Step 6: Fire drill** — push a branch where `run_signal.py` raises on line 1, `gh workflow run daily-trade.yml --ref <branch> -f mode=premarket` (premarket doesn't run `run_signal`; use `-f mode=eod` **only after 16:15 ET**). Expected: red run + phone buzz within 2 min. Delete the branch. Journal "alert fire drill PASSED".
- [ ] **Step 7: Commit** `git commit -m "feat: Telegram alerts for failures, trades and halts"`

### Task 8: Precise trigger (stop relying on GHA cron)

GHA scheduled runs were 3–5 h late (F5). cron-job.org is free, timezone-aware (handles DST) and calls GitHub's `workflow_dispatch` on time. GHA cron stays as a late fallback — safe because Task 6 made a second run a no-op (`PENDING`).

- [ ] **Step 1:** Create a fine-grained PAT: repo `Rayyan-Oumlil/claude-trading` only, permission **Actions: Read and write**, 1-year expiry. Store it only in cron-job.org.
- [ ] **Step 2:** cron-job.org → two jobs, timezone **America/New_York**, Mon–Fri:
  - `07:00` premarket, `16:20` eod
  - URL `https://api.github.com/repos/Rayyan-Oumlil/claude-trading/actions/workflows/daily-trade.yml/dispatches`, method POST
  - Headers: `Authorization: Bearer <PAT>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`
  - Body: `{"ref":"master","inputs":{"mode":"eod"}}` (resp. `premarket`)
  - Enable failure notifications (email) in cron-job.org.
- [ ] **Step 3:** Use "Test run" on the premarket job → `gh run list -L 1` shows `workflow_dispatch` within 1 min.
- [ ] **Step 4:** Next trading day verify: `gh run list -L 6 --json event,createdAt` → dispatch runs at ~20:20 UTC (EDT) / 21:20 UTC (EST), cron fallback later shows `PENDING` or `HOLD`, never a second BUY/SELL.
- [ ] **Step 5:** Document in `routines/README.md` (trigger source, PAT expiry date, how to rotate). Commit `docs: precise dispatch trigger via cron-job.org`.

### Task 9: Fix the daily-reflection routine (it already caught F1 — make it heard)

- [ ] **Step 1: Notifications ON** in the routine's Details panel (currently "Notifications off").
- [ ] **Step 2: Let it push to `master`.** In the routine's repository settings, allow pushes to the default branch (by default cloud runs push to `claude/*` branches — that is why 76 reflections never reached `master`). If the setting isn't available: tell the routine to open a PR and add a GHA workflow that auto-merges PRs from `claude/*` touching only `journal/**`.
- [ ] **Step 3: Update the prompt** (`routines/daily-reflection.md`, then paste into the routine):
  - Step 4 add flags: *"Any `nan` in today's confidence-log lines"*, *"two different decisions for the same session date"*, *"broker positions in portfolio-state.md contain a symbol other than SPY"*, *"latest confidence-log date != latest completed session"*.
  - New first line of the reflection when any flag fires: `🚨 ACTION NEEDED: <flag>`; then run `python -m paper_trading.notify "reflection: <flag>"` (add `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` to the routine's environment variables).
  - Replace "MA-crossover thesis" Gate 2 text with: *"Gate 2 clock restarts on the first clean session after Task 6 shipped (see journal)."*
- [ ] **Step 4: Backfill the 76 orphaned reflections** into master journals (only the `## Reflection` sections, skip "skip" commits):

```bash
python - <<'EOF'
import re, subprocess
from pathlib import Path
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
branches = [b.strip() for b in run("git", "branch", "-r", "--list", "origin/claude/peaceful-cannon-*").splitlines()]
added = 0
for br in branches:
    for path in run("git", "diff", "--name-only", f"master...{br}", "--", "journal/").split():
        text = run("git", "show", f"{br}:{path}")
        for section in re.findall(r"(## Reflection.*?)(?=\n---\n|\n## (?!#)|\Z)", text, re.S):
            target = Path(path)
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if section.strip() not in current:
                target.write_text(current.rstrip() + "\n\n---\n\n" + section.strip() + "\n", encoding="utf-8")
                added += 1
print("sections added:", added)
EOF
git diff --stat journal/
```

Expected: ~20–40 sections added (the rest were "skip" runs). Read 2–3 diffs before committing. Commit `docs: backfill orphaned daily reflections into journal`.
- [ ] **Step 5 (Rayyan confirms):** delete the merged branches — `git branch -r --list 'origin/claude/peaceful-cannon-*' | sed 's#origin/##' | xargs -n 20 git push origin --delete`.
- [ ] **Step 6:** "Run now" the routine → verify a commit lands on **master** and the phone buzzes if a flag fires.

---

# PHASE 2 — Honest measurement (weeks 1–4 after Phase 1) — *own plan when Phase 1 gate passes*

Deliverables:
1. **Benchmark in every snapshot.** `eod_close` writes equity, SPY buy-and-hold equity from the same start, and the ratio into `memory/portfolio-state.md` + a CSV `memory/equity-curve.csv` (one row per session). Nothing gets called "profitable" without the SPY column next to it.
2. **Gate 2 restart.** Clock restarts on the first clean session after Task 6. Re-run `backtests/ma_crossover/gate2_check.py` at 2 and 4 weeks; journal both.
3. **Reproducible research.** Every backtest script writes `results/<run>.json` containing git SHA, params, data source, date range, metrics. `backtests/registry.md` lists every run, pass or fail. Rule: a strategy's STRATEGY.md may only cite numbers that exist in the registry.
4. **CLAUDE.md refresh** (§5 stack: Alpaca data, cron-job.org, Telegram; §6 statuses; §8 add "`git pull` before auditing" — the stale-clone lesson bit again on 2026-10-02).
5. **Walk-forward re-check of ma-crossover** across 2008, 2015-16 chop, 2020, 2022 with costs. Question: *does SMA10/50 beat SPY buy-and-hold after costs on a risk-adjusted basis?* If no → it is a market-timing overlay at best, and Phase 3 matters more.

**Gate:** 20 clean sessions, Gate 2 re-run done, registry populated, equity-vs-SPY visible daily.

# PHASE 3 — Find an edge or prove there isn't one (weeks 2–8, overlaps Phase 2) — *own plan*

Candidate C from the existing roadmap: **sector / dual momentum** (monthly rotation among sector ETFs or SPY/EFA/AGG by 12-1 month return, absolute-momentum cash filter). Why this one: long public evidence base, ~12 decisions/year (low cost, low tax friction, survives cron lag), structurally different from the trend overlay already running.

Process (CLAUDE.md §3 #1 — questions before code):
1. Spec in `strategies/<name>/STRATEGY.md` from `_template`, every parameter sourced to literature, decided **before** any backtest. Pre-registered pass bar: OOS Sharpe ≥ SPY's over the same window **and** max DD ≤ SPY's, ≥ 2 regimes.
2. One backtest pass, one optional revision pass (CLAUDE.md §7: >2 passes = re-examine thesis). Results only via the registry.
3. Pass → own Alpaca paper account (Alpaca allows multiple paper accounts — one account per strategy, never shared, F2). Fail → rejected list, next candidate D (crypto MA via freqtrade dry-run).

# PHASE 4 — Real money (only after all 3 CLAUDE.md gates) — *own plan*

- **Broker for a Canadian resident:** verify before anything else — Alpaca live-account eligibility for Canada, versus IBKR Canada (API) / Questrade (API). Pick the one with an API, CAD/USD conversion cost you understand, and paper/live parity.
- **Account type:** a TFSA used for frequent trading risks CRA treating gains as business income (taxable). A monthly-rotation strategy is the lower-risk profile. Confirm with a tax source before funding.
- **Size:** start with an amount you would be fine losing entirely ($500–$1,000). Scale ×2 only after 3 months live within 1.5× of paper drawdown and tracking error vs paper < 2%/month.
- **Live kill switch:** same `.HALT` + Telegram, plus a max-daily-loss check against the broker before every order.
- **Expectation, written down:** on $5k, beating SPY by 5%/yr = $250/yr. The compounding value right now is the system and the track record, not the P&L.

---

# Routine roster (Claude Code routines — read-only on orders, always write to `master`, always notify)

| Routine | When | Does | Writes | Alerts |
|---|---|---|---|---|
| **daily-reflection** (fix, Task 9) | Weekdays 19:00 ET | Narrative + integrity flags on today's session | `journal/<session>.md` | 🚨 flags → Telegram |
| **weekly-review** (new, Phase 2) | Fri 18:00 ET | Equity vs SPY week/since-start, Gate 2 progress, open threads, lessons; proposes CLAUDE.md §6 edits as a PR (never edits rules directly) | `journal/YYYY-Www-weekly.md` | Summary → Telegram |
| **strategy-lab** (new, Phase 3) | Sun 10:00 ET | Pops the top item of `research/queue.md`, runs that **pre-registered** backtest exactly as specced, records it in the registry. Forbidden: changing parameters, re-running a failed spec | `backtests/registry.md`, results JSON | Pass/fail → Telegram |
| **monthly-audit** (new, Phase 2) | 1st Sat of month | Re-runs this audit: `git pull`, tests, red runs, broker vs ledger, docs vs code drift, rule violations (live strategy without registry entry, shared accounts) | PR with findings | PR link → Telegram |

Deliberately **not** added: any routine that places, sizes or vetoes orders. The LLM layer narrates, audits and researches; deterministic code trades (PRINCIPLES #6, F6).

# Execution order

`T1 → T2` (today) → `T3, T4, T5` (independent, any order) → `T6` → `T7` → `T8, T9` → Phase 1 gate (5 clean sessions) → Phase 2 plan.
