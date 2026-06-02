"""
Multi-instrument RSI(2) signal engine with 3-agent research layer.

Runs in two modes:
  python run_signal_multi.py premarket   -- scan universe, run agents, queue signals
  python run_signal_multi.py eod         -- evaluate exits, execute queued entries, journal

Strategy: strategies/rsi2_multi/STRATEGY.md
Universe:  SPY, QQQ, IWM, GLD, XLK, XLE
Agents:    Technical (A) + Macro/Sentiment (B) + Portfolio/Risk (C) — parallel via threads
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf
from anthropic import Anthropic
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from paper_trading.kill_switch import is_halted  # noqa: E402
from strategies.rsi2_connors.signals import wilder_rsi  # noqa: E402

# ── constants ──────────────────────────────────────────────────────────────────
UNIVERSE     = ["SPY", "QQQ", "IWM", "GLD", "XLK", "XLE"]
RSI_PERIOD   = 2
RSI_ENTRY    = 10.0
RSI_EXIT     = 70.0
SMA_EXIT     = 5
TIME_STOP    = 10          # bars
POS_PCT      = 0.12        # 12% equity per position
MAX_POS      = 5
SLIPPAGE     = 0.0005
WARMUP_BARS  = 10          # min bars needed before first signal

PORTFOLIO_FILE  = PROJECT_ROOT / "memory" / "multi-portfolio-state.md"
CONFIDENCE_FILE = PROJECT_ROOT / "memory" / "confidence-log.md"
SIGNALS_QUEUE   = PROJECT_ROOT / "memory" / "multi-signals-queue.json"

_ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = Anthropic(api_key=_ANTHROPIC_KEY) if _ANTHROPIC_KEY else None
AGENTS_ENABLED = bool(_ANTHROPIC_KEY)


# ── data helpers ───────────────────────────────────────────────────────────────

def fetch_bars(tickers: list[str], days: int = 60) -> dict[str, pd.DataFrame]:
    """Return per-ticker OHLCV DataFrames (last `days` trading days)."""
    raw = yf.download(tickers, period=f"{days}d", auto_adjust=True, progress=False)
    result: dict[str, pd.DataFrame] = {}
    for t in tickers:
        try:
            df = pd.DataFrame({
                "open":   raw["Open"][t],
                "high":   raw["High"][t],
                "low":    raw["Low"][t],
                "close":  raw["Close"][t],
                "volume": raw["Volume"][t],
            }).dropna()
            if len(df) >= WARMUP_BARS:
                result[t] = df
        except Exception:
            pass
    return result


def compute_signals(bars: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Compute current RSI(2) and signal state for each ticker."""
    signals: dict[str, dict] = {}
    for t, df in bars.items():
        rsi_series = wilder_rsi(df["close"], RSI_PERIOD)
        sma5       = df["close"].rolling(SMA_EXIT).mean()
        rsi_now    = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
        rsi_prev   = float(rsi_series.iloc[-2]) if not pd.isna(rsi_series.iloc[-2]) else 50.0
        sma5_prev  = float(sma5.iloc[-2])        if not pd.isna(sma5.iloc[-2]) else df["close"].iloc[-2]
        close_prev = float(df["close"].iloc[-2])
        close_now  = float(df["close"].iloc[-1])
        signals[t] = {
            "rsi_now":    round(rsi_now, 2),
            "rsi_prev":   round(rsi_prev, 2),
            "close_now":  round(close_now, 2),
            "close_prev": round(close_prev, 2),
            "sma5_prev":  round(sma5_prev, 2),
            "entry_signal": rsi_prev < RSI_ENTRY,
            "exit_signal":  rsi_prev > RSI_EXIT or close_prev > sma5_prev,
        }
    return signals


# ── portfolio state ────────────────────────────────────────────────────────────

def load_portfolio() -> dict:
    if not PORTFOLIO_FILE.exists():
        return {"positions": {}, "cash": 100_000.0, "equity": 100_000.0,
                "last_updated": "", "peak_equity": 100_000.0}
    text = PORTFOLIO_FILE.read_text(encoding="utf-8")
    # Parse the JSON block between ```json and ```
    if "```json" in text:
        start = text.index("```json") + 7
        end   = text.index("```", start)
        return json.loads(text[start:end].strip())
    return {"positions": {}, "cash": 100_000.0, "equity": 100_000.0,
            "last_updated": "", "peak_equity": 100_000.0}


def save_portfolio(state: dict) -> None:
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    content = f"""# Multi-Instrument Portfolio State

Last updated: {state['last_updated']}

**Equity:**       ${state['equity']:,.2f}
**Cash:**         ${state['cash']:,.2f}
**Peak equity:**  ${state['peak_equity']:,.2f}
**Positions:**    {len(state['positions'])} / {MAX_POS}

```json
{json.dumps(state, indent=2)}
```
"""
    PORTFOLIO_FILE.write_text(content, encoding="utf-8")


def append_confidence(decision: str, score: int, reason: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line  = f"\n{today} | {decision} | {score}/10 | {reason} [multi]"
    if CONFIDENCE_FILE.exists():
        with open(CONFIDENCE_FILE, "a", encoding="utf-8") as f:
            f.write(line)


# ── Alpaca order placement ──────────────────────────────────────────────────────

def place_paper_order(ticker: str, side: str, qty: float) -> str | None:
    """Place a paper order via Alpaca. Returns order ID or None."""
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        tc = TradingClient(
            os.environ["ALPACA_API_KEY"],
            os.environ["ALPACA_API_SECRET"],
            paper=True,
        )
        req = MarketOrderRequest(
            symbol=ticker,
            qty=round(qty, 2),
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        order = tc.submit_order(req)
        return str(order.id)
    except Exception as e:
        print(f"  [order error] {ticker} {side}: {e}")
        return None


# ── agent calls ────────────────────────────────────────────────────────────────

def agent_technical(signals: dict, portfolio: dict) -> dict:
    """Agent A: technical confirmation + earnings check."""
    ticker_summary = "\n".join(
        f"  {t}: RSI={v['rsi_prev']:.1f}, close={v['close_prev']}, "
        f"entry_signal={v['entry_signal']}, exit_signal={v['exit_signal']}"
        for t, v in signals.items()
    )
    prompt = f"""You are Agent A (Technical) in a multi-agent paper-trading system.

Universe signals right now:
{ticker_summary}

Open positions: {list(portfolio['positions'].keys())}
Cash available: ${portfolio['cash']:,.0f}

Your job:
1. List which tickers have entry_signal=True (RSI(2) < 10 — oversold).
2. List which open positions have exit_signal=True (RSI > 70 or above 5-DMA).
3. Flag any ticker you suspect has earnings in the next 2 trading days (use your knowledge; if unsure, say unsure).
4. Give an overall TECHNICAL_VERDICT: PROCEED / CAUTION / VETO (veto only if data is obviously broken).

Respond in this exact format:
ENTRY_CANDIDATES: [list of tickers]
EXIT_CANDIDATES: [list of tickers]
EARNINGS_FLAGS: [list or "none"]
TECHNICAL_VERDICT: PROCEED|CAUTION|VETO
NOTES: (1-2 sentences)"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    return {"agent": "A_technical", "output": text}


def agent_macro(signals: dict) -> dict:
    """Agent B: macro/sentiment check."""
    tickers_str = ", ".join(signals.keys())
    prompt = f"""You are Agent B (Macro/Sentiment) in a paper-trading system trading: {tickers_str}.

Today is {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.

Your job:
1. Is there a scheduled FOMC decision, CPI, NFP, or PPI print in the next 24 hours?
2. Is there any major geopolitical shock or market-moving news right now?
3. Is the broad market sentiment risk_on, risk_off, or neutral?

Respond in this exact format:
MACRO_EVENT_TODAY: [event name or "none"]
MACRO_EVENT_TOMORROW: [event name or "none"]
SENTIMENT: risk_on|risk_off|neutral
MACRO_VERDICT: PROCEED|CAUTION|VETO
NOTES: (1-2 sentences citing what you know)

VETO only if there is a same-day major macro print (FOMC decision day, NFP release) that could gap the whole market unpredictably. CAUTION for minor data. PROCEED otherwise."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    return {"agent": "B_macro", "output": text}


def agent_risk(portfolio: dict, proposed_entries: list[str]) -> dict:
    """Agent C: portfolio risk and kill-switch check."""
    equity   = portfolio["equity"]
    peak     = portfolio["peak_equity"]
    dd       = (equity - peak) / peak * 100 if peak > 0 else 0.0
    n_pos    = len(portfolio["positions"])
    backtest_max_dd = -5.59  # from OOS backtest

    prompt = f"""You are Agent C (Risk) in a paper-trading system.

Current portfolio state:
  Equity: ${equity:,.2f}
  Peak equity: ${peak:,.2f}
  Current drawdown from peak: {dd:.2f}%
  Open positions: {n_pos} / {MAX_POS}
  Cash: ${portfolio['cash']:,.2f}
  Backtest max drawdown: {backtest_max_dd}%
  Kill threshold (2x backtest DD): {backtest_max_dd * 2:.1f}%

Proposed new entries: {proposed_entries}
Each new position = 12% of equity = ${equity * 0.12:,.0f}

Your job:
1. Is the kill threshold breached? ({dd:.2f}% vs {backtest_max_dd*2:.1f}% threshold)
2. Is there enough cash for the proposed entries?
3. Would any proposed entry push total allocation over 60% (5 positions)?
4. Any position sizing concerns?

Respond in this exact format:
KILL_TRIGGERED: yes|no
CASH_SUFFICIENT: yes|no
ALLOCATION_OK: yes|no
RISK_VERDICT: PROCEED|CAUTION|VETO
APPROVED_ENTRIES: [list of approved tickers or "none"]
NOTES: (1-2 sentences)"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    return {"agent": "C_risk", "output": text}


def synthesize_decision(agent_a: dict, agent_b: dict, agent_c: dict,
                        signals: dict, portfolio: dict) -> dict:
    """Parse agent outputs and produce final decision."""
    import re

    def extract(text: str, key: str) -> str:
        m = re.search(rf"{key}:\s*(.+)", text)
        return m.group(1).strip() if m else ""

    verdict_a = extract(agent_a["output"], "TECHNICAL_VERDICT")
    verdict_b = extract(agent_b["output"], "MACRO_VERDICT")
    verdict_c = extract(agent_c["output"], "RISK_VERDICT")
    kill      = extract(agent_c["output"], "KILL_TRIGGERED").lower() == "yes"

    # Parse entry candidates from agent A
    ec_raw = extract(agent_a["output"], "ENTRY_CANDIDATES")
    entry_candidates = [t.strip().strip("[],'\" ") for t in ec_raw.split(",") if t.strip().strip("[],'\" ") in UNIVERSE]

    # Parse exit candidates
    ex_raw = extract(agent_a["output"], "EXIT_CANDIDATES")
    exit_candidates = [t.strip().strip("[],'\" ") for t in ex_raw.split(",") if t.strip().strip("[],'\" ") in portfolio["positions"]]

    # Parse approved entries from agent C
    ap_raw    = extract(agent_c["output"], "APPROVED_ENTRIES")
    approved  = [t.strip().strip("[],'\" ") for t in ap_raw.split(",") if t.strip().strip("[],'\" ") in UNIVERSE]

    # Veto logic: any VETO from any agent kills all entries
    veto = any(v == "VETO" for v in [verdict_a, verdict_b, verdict_c]) or kill

    final_entries = [] if veto else [t for t in entry_candidates if t in approved]
    final_exits   = exit_candidates  # exits always proceed regardless of veto

    # Confidence score
    score = 7
    cautions = sum(v == "CAUTION" for v in [verdict_a, verdict_b, verdict_c])
    if cautions == 0 and not veto: score = min(10, score + 1)
    if cautions == 1: score = max(1, score - 1)
    if cautions >= 2: score = max(1, score - 2)
    if veto: score = 0

    sentiment  = extract(agent_b["output"], "SENTIMENT")
    macro_event = extract(agent_b["output"], "MACRO_EVENT_TODAY")

    return {
        "final_entries": final_entries,
        "final_exits":   final_exits,
        "veto":          veto,
        "kill":          kill,
        "confidence":    score,
        "verdicts":      {"A": verdict_a, "B": verdict_b, "C": verdict_c},
        "sentiment":     sentiment,
        "macro_event":   macro_event,
        "agent_outputs": {
            "A": agent_a["output"],
            "B": agent_b["output"],
            "C": agent_c["output"],
        },
    }


# ── premarket mode ─────────────────────────────────────────────────────────────

def run_premarket() -> None:
    print("=== PREMARKET — rsi2-multi ===")

    if is_halted():
        print("HALTED — kill switch active. Skipping.")
        append_confidence("HALT", 0, "kill switch active [multi]")
        return

    bars      = fetch_bars(UNIVERSE, days=60)
    signals   = compute_signals(bars)
    portfolio = load_portfolio()

    entry_cands = [t for t, s in signals.items() if s["entry_signal"] and t not in portfolio["positions"]]
    print(f"RSI(2) entry candidates: {entry_cands or 'none'}")
    print(f"Open positions: {list(portfolio['positions'].keys())}")

    if not entry_cands and not any(s["exit_signal"] for s in signals.values()):
        print("No signals today. Skipping agent calls.")
        append_confidence("HOLD", 7, "no rsi2 signals across universe [multi]")
        return

    if AGENTS_ENABLED:
        print("Running 3 agents in parallel...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            fut_a = ex.submit(agent_technical, signals, portfolio)
            fut_b = ex.submit(agent_macro, signals)
            fut_c = ex.submit(agent_risk, portfolio, entry_cands)
            agent_a = fut_a.result(timeout=60)
            agent_b = fut_b.result(timeout=60)
            agent_c = fut_c.result(timeout=60)
        decision = synthesize_decision(agent_a, agent_b, agent_c, signals, portfolio)
    else:
        print("ANTHROPIC_API_KEY not set — using deterministic-only mode (no LLM veto).")
        exit_cands = [t for t, s in signals.items() if s["exit_signal"] and t in portfolio["positions"]]
        decision = {
            "final_entries": entry_cands[:MAX_POS - len(portfolio["positions"])],
            "final_exits": exit_cands,
            "veto": False, "kill": False, "confidence": 6,
            "verdicts": {"A": "PROCEED", "B": "PROCEED", "C": "PROCEED"},
            "sentiment": "neutral", "macro_event": "none",
            "agent_outputs": {"A": "deterministic", "B": "deterministic", "C": "deterministic"},
        }

    print(f"\nVerdicts: A={decision['verdicts']['A']} B={decision['verdicts']['B']} C={decision['verdicts']['C']}")
    print(f"Entries approved: {decision['final_entries']}")
    print(f"Exits queued:     {decision['final_exits']}")
    print(f"Confidence: {decision['confidence']}/10")

    # Save signals queue for EOD to execute
    queue = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entries": decision["final_entries"],
        "exits":   decision["final_exits"],
        "decision": decision,
        "signals": {t: {k: v for k, v in s.items() if k != "entry_signal"} for t, s in signals.items()},
    }
    SIGNALS_QUEUE.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    append_confidence("SCAN", decision["confidence"],
                      f"entries={decision['final_entries']} exits={decision['final_exits']} [multi]")
    print(f"\nQueue written to {SIGNALS_QUEUE.name}")


# ── EOD mode ───────────────────────────────────────────────────────────────────

def run_eod() -> None:
    print("=== EOD — rsi2-multi ===")

    if is_halted():
        print("HALTED — kill switch active. Skipping.")
        append_confidence("HALT", 0, "kill switch active [multi]")
        return

    portfolio = load_portfolio()
    bars      = fetch_bars(UNIVERSE, days=60)
    signals   = compute_signals(bars)
    today     = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load queue from premarket
    queue: dict = {}
    if SIGNALS_QUEUE.exists():
        queue = json.loads(SIGNALS_QUEUE.read_text(encoding="utf-8"))

    # --- EXIT existing positions ---
    positions = dict(portfolio["positions"])
    closed: list[dict] = []
    for t, pos in positions.items():
        sig = signals.get(t, {})
        bars_held = pos.get("bars_held", 0) + 1
        pos["bars_held"] = bars_held
        should_exit = sig.get("exit_signal", False) or bars_held >= TIME_STOP
        if t in queue.get("exits", []):
            should_exit = True
        if should_exit:
            current_price = sig.get("close_now", pos["entry_price"])
            exit_price    = current_price * (1 - SLIPPAGE)
            pnl           = (exit_price - pos["entry_price"]) * pos["qty"]
            portfolio["cash"] += pos["qty"] * exit_price
            reason = "time_stop" if bars_held >= TIME_STOP else "signal"
            closed.append({"ticker": t, "pnl": round(pnl, 2), "reason": reason,
                           "bars_held": bars_held, "exit_price": round(exit_price, 4)})
            order_id = place_paper_order(t, "sell", pos["qty"])
            print(f"  SELL {t}: qty={pos['qty']:.2f} @ ~${exit_price:.2f} P&L=${pnl:+.2f} ({reason}) order={order_id}")
            del portfolio["positions"][t]

    # --- ENTER new positions ---
    entered: list[dict] = []
    for t in queue.get("entries", []):
        if t in portfolio["positions"]: continue
        if len(portfolio["positions"]) >= MAX_POS: break
        current_price = signals.get(t, {}).get("close_now", 0)
        if current_price <= 0: continue
        fill   = current_price * (1 + SLIPPAGE)
        equity = portfolio["cash"] + sum(
            p.get("market_value", p["entry_price"] * p["qty"])
            for p in portfolio["positions"].values()
        )
        alloc = equity * POS_PCT
        qty   = alloc / fill
        if qty * fill > portfolio["cash"]:
            print(f"  SKIP {t}: insufficient cash")
            continue
        portfolio["cash"] -= qty * fill
        portfolio["positions"][t] = {
            "qty": round(qty, 4), "entry_price": round(fill, 4),
            "entry_date": today, "bars_held": 0,
        }
        order_id = place_paper_order(t, "buy", qty)
        entered.append({"ticker": t, "qty": round(qty, 4), "fill": round(fill, 4), "order_id": order_id})
        print(f"  BUY  {t}: qty={qty:.2f} @ ~${fill:.2f} order={order_id}")

    # --- Update portfolio equity ---
    for t, pos in portfolio["positions"].items():
        price = signals.get(t, {}).get("close_now", pos["entry_price"])
        pos["market_value"] = round(pos["qty"] * price, 2)
        pos["unrealized_pl"] = round((price - pos["entry_price"]) * pos["qty"], 2)

    portfolio["equity"] = portfolio["cash"] + sum(
        p.get("market_value", 0) for p in portfolio["positions"].values()
    )
    portfolio["peak_equity"] = max(portfolio["peak_equity"], portfolio["equity"])
    save_portfolio(portfolio)

    decision_tag = "HOLD" if not entered and not closed else f"{len(entered)}BUY+{len(closed)}SELL"
    append_confidence(decision_tag, queue.get("decision", {}).get("confidence", 7),
                      f"entered={[e['ticker'] for e in entered]} closed={[c['ticker'] for c in closed]} [multi]")

    print(f"\nEOD summary: equity=${portfolio['equity']:,.2f} cash=${portfolio['cash']:,.2f}")
    print(f"Positions: {list(portfolio['positions'].keys())}")
    print(f"Closed today: {[(c['ticker'], c['pnl']) for c in closed]}")
    print(f"Entered today: {[e['ticker'] for e in entered]}")

    # Write journal snippet
    journal_path = PROJECT_ROOT / "journal" / f"{today}.md"
    if journal_path.exists():
        snippet = f"""
---

## Multi-Strategy EOD — {datetime.now(timezone.utc).isoformat()}

**Equity:** ${portfolio['equity']:,.2f} | **Cash:** ${portfolio['cash']:,.2f}
**Positions ({len(portfolio['positions'])}/{MAX_POS}):** {list(portfolio['positions'].keys()) or 'none'}

### Trades today
Closed: {closed or 'none'}
Entered: {entered or 'none'}

### Agent verdicts
{queue.get('decision', {}).get('verdicts', {})}
Sentiment: {queue.get('decision', {}).get('sentiment', 'n/a')}
Confidence: {queue.get('decision', {}).get('confidence', 'n/a')}/10
"""
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(snippet)
        print(f"Journal updated: {journal_path.name}")


# ── entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "eod"
    if mode == "premarket":
        run_premarket()
    else:
        run_eod()
