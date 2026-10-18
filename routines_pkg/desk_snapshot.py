"""
Desk fact pack + the one daily Telegram message — read-only. Never places or cancels orders.

Reads the IBKR paper account, checks the robot's log for integrity problems,
scores performance against SPY, and writes memory/desk-snapshot.json.
Flags with severity "halt" are the only grounds for auto_halt.py to write .HALT.

Usage: python -m routines_pkg.desk_snapshot [--report]
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from paper_trading.kill_switch import halt_reason  # noqa: E402
from paper_trading.yahoo_data import fetch_daily, last_completed_session  # noqa: E402
from strategies.portfolio import ALLOWED_POSITIONS, SLEEVES, log_symbol, split_log_lines  # noqa: E402

TICKER = "SPY"
ALLOWED = ALLOWED_POSITIONS
BACKTEST_MAX_DD_PCT = -12.4  # strategies/ma_crossover/STRATEGY.md: OOS max DD
FILL_LIMIT_PCT = {"SPY": 2.0, "IBIT": 5.0, "ETHA": 5.0}  # STRATEGY.md §10 (crypto_trend: 5%)
TRADE_DECISIONS = {"BUY", "SELL"}
CONFIDENCE_LOG = PROJECT_ROOT / "memory" / "confidence-log-ibkr.md"
EQUITY_LOG = PROJECT_ROOT / "memory" / "equity-ibkr.csv"
SNAPSHOT_FILE = PROJECT_ROOT / "memory" / "desk-snapshot.json"


def _flag(code: str, severity: str, detail: str) -> dict:
    return {"code": code, "severity": severity, "detail": detail}


def integrity_flags(
    log_lines: list[str], positions: list[dict], allowed: set[str], session: date, closing: set[str] = frozenset(),
) -> list[dict]:
    robot = [line for line in log_lines if log_symbol(line) is not None]
    today = [line for line in robot if line.startswith(session.isoformat())]
    decisions = [line.split("|")[1].strip() for line in today]
    flags: list[dict] = []

    halted_today = "HALT" in decisions
    for sleeve in SLEEVES:
        if not halted_today and not any(log_symbol(line) == sleeve.symbol for line in today):
            flags.append(_flag("robot_silent", "alert", f"no {sleeve.symbol} entry for session {session}"))
    if any("nan" in line.lower() for line in today):
        flags.append(_flag("nan_in_log", "halt", "NaN in today's decision — data integrity failure"))
    by_symbol: dict[str, list[str]] = {}
    for line, decision in zip(today, decisions):
        if decision not in {"PENDING", "HALT"}:
            by_symbol.setdefault(log_symbol(line), []).append(decision)
    for symbol, acted in by_symbol.items():
        if len(set(acted)) > 1 or sum(d in TRADE_DECISIONS for d in acted) > 1:
            flags.append(_flag("conflicting_decisions", "halt", f"{symbol} on {session} logged {acted}"))
    foreign = sorted(p["symbol"] for p in positions if p["symbol"] not in allowed)
    unmanaged = [s for s in foreign if s not in closing]
    if unmanaged:
        flags.append(_flag("foreign_position", "halt", f"positions outside the strategy: {unmanaged}"))
    if set(foreign) & closing:
        flags.append(_flag("foreign_position_closing", "alert", f"winding down with sell orders queued: {sorted(set(foreign) & closing)}"))
    return flags


def order_state_flags(log_lines: list[str], positions: list[dict], open_orders: list[dict]) -> list[dict]:
    """The latest BUY/SELL per sleeve must show up at the broker: as a position, or as an order still queued."""
    held = {p["symbol"] for p in positions}
    queued = {o["symbol"] for o in open_orders}
    flags = []
    for sleeve in SLEEVES:
        trades = [line for line in log_lines if log_symbol(line) == sleeve.symbol and line.split("|")[1].strip() in TRADE_DECISIONS]
        if not trades or sleeve.symbol in queued:
            continue
        last, action = trades[-1], trades[-1].split("|")[1].strip()
        if (action == "BUY") != (sleeve.symbol in held):
            flags.append(_flag("order_missing", "alert",
                               f"{sleeve.symbol}: robot logged {action} on {last[:10]} but the account "
                               f"{'holds no' if action == 'BUY' else 'still holds'} {sleeve.symbol} and nothing is queued"))
    return flags


def record_equity(rows: list[tuple[date, float]], session: date, equity: float) -> list[tuple[date, float]]:
    """One equity point per session; a rerun for the same session replaces it."""
    return sorted([r for r in rows if r[0] != session] + [(session, equity)])


def read_equity(path: Path = EQUITY_LOG) -> list[tuple[date, float]]:
    if not path.exists():
        return []
    rows = [line.split(",") for line in path.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
    return [(date.fromisoformat(d), float(v)) for d, v in rows]


def write_equity(rows: list[tuple[date, float]], path: Path = EQUITY_LOG) -> None:
    path.write_text("session,equity_usd\n" + "".join(f"{d.isoformat()},{v:.2f}\n" for d, v in rows), encoding="utf-8")


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


def _decision_line(line: str) -> str:
    """'2026-10-05 | BUY | 7/10 | IBIT: cross-up confirmed; fast-slow margin +1.2%; 104 sh at open' -> short form."""
    _, action, _, reason = [p.strip() for p in line.split("|", 3)]
    symbol, _, detail = reason.partition(":")
    extras = [part.strip() for part in detail.split(";")[1:]]
    return f"• {symbol} {action}" + (f" · {' · '.join(extras)}" if extras else "")


def daily_report(snapshot: dict) -> str:
    """The one end-of-day Telegram message."""
    perf = snapshot["performance"]
    icon = "📈" if perf["day_change"] >= 0 else "📉"
    lines = [
        f"{icon} {snapshot['session']} · IBKR paper · Equity ${snapshot['account']['equity']:,.2f} USD · "
        f"Today {_money(perf['day_change'])} ({_pct(perf['day_change_pct'])}%)",
        f"Since {perf['start']}: {_pct(perf['account_return_pct'])}% vs SPY {_pct(perf['spy_return_pct'])}% "
        f"({_pct(perf['vs_spy_pct'])} pts) · drawdown {perf['current_drawdown_pct']:.1f}%",
    ]
    if snapshot["positions"]:
        lines += [
            f"{p['symbol']} {p['qty']:g} sh · ${p['market_value']:,.0f} · unrealized {_money(p['unrealized_pl'], 0)}"
            for p in snapshot["positions"]
        ]
    else:
        lines.append("Positions: none (cash)")
    decisions = [_decision_line(line) for line in snapshot.get("robot_log_today", []) if line.count("|") >= 3]
    if decisions:
        lines += ["Robot decisions:"] + decisions
    for o in snapshot.get("open_orders", []):
        lines.append(f"⏳ Queued for next open: {o['side'].upper()} {o['qty']:g} {o['symbol']}")
    for f in snapshot.get("fills", []):
        lines.append(f"✅ Filled: {f['side'].upper()} {f['qty']:g} {f['symbol']} at ${f['filled_avg_price']:,.2f}")
    if snapshot["account"].get("cash", 1.0) <= 0:
        lines.append("💱 No USD cash: convert CAD→USD in the paper account or the robot cannot buy.")
    for flag in snapshot["flags"]:
        lines.append(f"{'🚨' if flag['severity'] == 'halt' else '⚠️'} {flag['code']}: {flag['detail']}")
    if snapshot.get("halted"):
        lines.append(f"🛑 HALTED — the robot will not trade until you delete .HALT. {snapshot['halted'].strip()}")
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
            out.append({"symbol": symbol, "filled_at": o["filled_at"], "fill": o["filled_avg_price"],
                        "signal_close": signal_price, "deviation_pct": deviation})
    return out


def risk_flags(perf: dict, deviations: list[dict]) -> list[dict]:
    flags = []
    if perf["current_drawdown_pct"] < 2 * BACKTEST_MAX_DD_PCT:
        flags.append(_flag("drawdown_kill", "halt", f"drawdown {perf['current_drawdown_pct']:.1f}% beyond 2x backtest max DD"))
    elif perf["current_drawdown_pct"] < -5:
        flags.append(_flag("drawdown_watch", "alert", f"drawdown {perf['current_drawdown_pct']:.1f}% from peak"))
    for d in deviations:
        flags.append(_flag("fill_deviation", "halt",
                           f"{d['symbol']} fill {d['fill']} vs signal close {d['signal_close']:.2f} ({d['deviation_pct']:+.2f}%)"))
    return flags


def build() -> dict:
    from brokers.ibkr import IbkrBroker  # needs a running Gateway; tests never import it here

    now = datetime.now(timezone.utc)
    session = last_completed_session(fetch_daily(TICKER, 10).index, now)
    client = IbkrBroker.connect()
    try:
        account = client.get_account()
        positions = client.get_positions()
        open_orders = client.get_open_orders()
        fills = client.get_fills()
        account_id = client.account_id
    finally:
        client.disconnect()

    equity = record_equity(read_equity(), session, account["equity"])
    write_equity(equity)
    start = equity[0][0]
    spy = fetch_daily(TICKER, (now.date() - start).days + 10)["close"]
    spy = spy[(spy.index >= pd.Timestamp(start)) & (spy.index <= pd.Timestamp(session))]
    perf = performance(equity, spy)

    deviations = []
    for sleeve in SLEEVES:
        if any(f["symbol"] == sleeve.symbol for f in fills):
            closes = fetch_daily(sleeve.symbol, 20)["close"]
            deviations += fill_deviations(fills, closes, sleeve.symbol, FILL_LIMIT_PCT[sleeve.symbol])
    log_lines = split_log_lines(CONFIDENCE_LOG.read_text(encoding="utf-8")) if CONFIDENCE_LOG.exists() else []
    closing = {o["symbol"] for o in open_orders if o["side"] == "sell"}
    flags = (integrity_flags(log_lines, positions, ALLOWED, session, closing)
             + order_state_flags(log_lines, positions, open_orders) + risk_flags(perf, deviations))
    return {
        "generated_at": now.isoformat(),
        "account_id": account_id,
        "session": session.isoformat(),
        "halted": halt_reason(),
        "account": account,
        "positions": positions,
        "open_orders": open_orders,
        "fills": fills,
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
