"""
Trading-desk fact pack — read-only. Never places or cancels orders.

Pulls broker state + SPY benchmark from Alpaca, checks the robot's log for
integrity problems, and writes memory/desk-snapshot.json for the trading-desk
routine to reason over. Flags with severity "halt" are the routine's only
grounds for writing .HALT (see routines/trading-desk.md).

Usage: python -m routines_pkg.desk_snapshot
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from paper_trading.alpaca_client import AlpacaClient  # noqa: E402
from paper_trading.kill_switch import halt_reason  # noqa: E402
from paper_trading.market_calendar import last_completed_session  # noqa: E402
from paper_trading.market_data import SIP_DELAY, get_daily_bars  # noqa: E402
from strategies.portfolio import split_log_lines  # noqa: E402,F401

TICKER = "SPY"
ALLOWED = {TICKER}
PAPER_START = date(2026, 4, 23)
BACKTEST_MAX_DD_PCT = -12.4  # strategies/ma_crossover/STRATEGY.md: OOS max DD
FILL_DEVIATION_LIMIT_PCT = 2.0  # STRATEGY.md §10 kill condition
TRADE_DECISIONS = {"BUY", "SELL"}
OPEN_STATUSES = {"new", "accepted", "pending_new", "partially_filled"}
CONFIDENCE_LOG = PROJECT_ROOT / "memory" / "confidence-log.md"
SNAPSHOT_FILE = PROJECT_ROOT / "memory" / "desk-snapshot.json"

def _flag(code: str, severity: str, detail: str) -> dict:
    return {"code": code, "severity": severity, "detail": detail}


def integrity_flags(
    log_lines: list[str], positions: list[dict], allowed: set[str], session: date, closing: set[str] = frozenset()
) -> list[dict]:
    robot = [line for line in log_lines if "[multi]" not in line]
    today = [line for line in robot if line.startswith(session.isoformat())]
    decisions = [line.split("|")[1].strip() for line in today]
    flags: list[dict] = []

    if not today:
        flags.append(_flag("robot_silent", "alert", f"no confidence-log entry for session {session}"))
    if any("nan" in line.lower() for line in today):
        flags.append(_flag("nan_in_log", "halt", "NaN in today's decision — data integrity failure"))
    acted = [d for d in decisions if d != "PENDING"]
    if len(set(acted)) > 1 or sum(d in TRADE_DECISIONS for d in acted) > 1:
        flags.append(_flag("conflicting_decisions", "halt", f"session {session} logged {decisions}"))
    foreign = sorted(p["symbol"] for p in positions if p["symbol"] not in allowed)
    unmanaged = [s for s in foreign if s not in closing]
    if unmanaged:
        flags.append(_flag("foreign_position", "halt", f"positions outside the strategy: {unmanaged}"))
    if set(foreign) & closing:
        flags.append(_flag("foreign_position_closing", "alert", f"winding down with sell orders queued: {sorted(set(foreign) & closing)}"))
    return flags


def performance(equity: list[tuple[date, float]], spy_closes: pd.Series) -> dict:
    values = pd.Series([v for _, v in equity], index=pd.to_datetime([d for d, _ in equity]))
    drawdown = values / values.cummax() - 1
    account_ret = (values.iloc[-1] / values.iloc[0] - 1) * 100
    spy_ret = (spy_closes.iloc[-1] / spy_closes.iloc[0] - 1) * 100
    return {
        "start": str(values.index[0].date()),
        "account_return_pct": float(account_ret),
        "spy_return_pct": float(spy_ret),
        "vs_spy_pct": float(account_ret - spy_ret),
        "current_drawdown_pct": float(drawdown.iloc[-1] * 100),
        "max_drawdown_pct": float(drawdown.min() * 100),
        "day_change": float(values.iloc[-1] - values.iloc[-2]) if len(values) > 1 else 0.0,
        "day_change_pct": float((values.iloc[-1] / values.iloc[-2] - 1) * 100) if len(values) > 1 else 0.0,
    }


def _money(x: float, decimals: int = 2) -> str:
    return f"{'−' if x < 0 else '+'}${abs(x):,.{decimals}f}"


def _pct(x: float) -> str:
    return f"{'−' if x < 0 else '+'}{abs(x):.2f}"


def daily_report(snapshot: dict) -> str:
    """Plain-language end-of-day P&L message for Telegram."""
    perf = snapshot["performance"]
    icon = "📈" if perf["day_change"] >= 0 else "📉"
    lines = [
        f"{icon} {snapshot['session']} · Equity ${snapshot['account']['equity']:,.2f} · "
        f"Today {_money(perf['day_change'])} ({_pct(perf['day_change_pct'])}%)",
        f"Since start {_pct(perf['account_return_pct'])}% vs SPY {_pct(perf['spy_return_pct'])}% "
        f"({_pct(perf['vs_spy_pct'])} pts) · drawdown {perf['current_drawdown_pct']:.1f}%",
    ]
    if snapshot["positions"]:
        lines += [
            f"{p['symbol']} {p['qty']:g} sh · ${p['market_value']:,.0f} · unrealized {_money(p['unrealized_pl'], 0)}"
            for p in snapshot["positions"]
        ]
    else:
        lines.append("Positions: none (cash)")
    if snapshot["flags"]:
        n = len(snapshot["flags"])
        lines.append(f"⚠️ {n} flag{'s' if n > 1 else ''} — the desk will review tonight")
    return "\n".join(lines)


def fill_deviations(orders: list[dict], closes: pd.Series, symbol: str, limit_pct: float) -> list[dict]:
    """Fills that deviate from the prior session's close (the signal price) by more than limit_pct."""
    out = []
    for o in orders:
        if o["symbol"] != symbol or o["status"] != "filled" or not o["filled_avg_price"]:
            continue
        fill_day = pd.Timestamp(datetime.fromisoformat(o["filled_at"]).date())
        prior = closes[closes.index < fill_day]
        if prior.empty:
            continue
        signal_price = float(prior.iloc[-1])
        deviation = (float(o["filled_avg_price"]) / signal_price - 1) * 100
        if abs(deviation) > limit_pct:
            out.append({"filled_at": o["filled_at"], "fill": o["filled_avg_price"],
                        "signal_close": signal_price, "deviation_pct": deviation})
    return out


def risk_flags(perf: dict, deviations: list[dict]) -> list[dict]:
    flags = []
    if perf["current_drawdown_pct"] < 2 * BACKTEST_MAX_DD_PCT:
        flags.append(_flag("drawdown_kill", "halt", f"drawdown {perf['current_drawdown_pct']:.1f}% beyond 2x backtest max DD"))
    elif perf["current_drawdown_pct"] < -5:
        flags.append(_flag("drawdown_watch", "alert", f"drawdown {perf['current_drawdown_pct']:.1f}% from peak"))
    for d in deviations:
        flags.append(_flag("fill_deviation", "halt", f"fill {d['fill']} vs signal close {d['signal_close']:.2f} ({d['deviation_pct']:+.2f}%)"))
    return flags


def build() -> dict:
    client = AlpacaClient()
    now = datetime.now(timezone.utc)
    session = last_completed_session(now - SIP_DELAY, client.get_calendar(now.date() - timedelta(days=10), now.date()))
    account = client.get_account()
    positions = client.get_positions()
    orders = client.get_recent_orders(after=now - timedelta(days=10))
    equity = [(d, v) for d, v in client.get_equity_history() if d >= PAPER_START]
    spy = get_daily_bars(TICKER, lookback_days=(now.date() - PAPER_START).days + 5, last_session=session)["close"]
    spy = spy[spy.index >= pd.Timestamp(PAPER_START)]
    log_lines = split_log_lines(CONFIDENCE_LOG.read_text(encoding="utf-8"))

    perf = performance(equity, spy)
    deviations = fill_deviations(orders, spy, TICKER, FILL_DEVIATION_LIMIT_PCT)
    open_orders = [o for o in orders if o["status"] in OPEN_STATUSES]
    closing = {o["symbol"] for o in open_orders if o["side"] == "sell"}
    flags = integrity_flags(log_lines, positions, ALLOWED, session, closing) + risk_flags(perf, deviations)
    return {
        "generated_at": now.isoformat(),
        "session": session.isoformat(),
        "halted": halt_reason(),
        "account": account,
        "positions": positions,
        "open_orders": open_orders,
        "recent_orders": orders,
        "performance": perf,
        "robot_log_today": [line for line in log_lines if line.startswith(session.isoformat())],
        "flags": flags,
        "halt_recommended": any(f["severity"] == "halt" for f in flags),
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # emoji in the report; Windows consoles default to cp1252
    snapshot = build()
    SNAPSHOT_FILE.write_text(json.dumps(snapshot, indent=2, default=str) + "\n", encoding="utf-8")
    print(daily_report(snapshot) if "--report" in sys.argv else json.dumps(snapshot, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
