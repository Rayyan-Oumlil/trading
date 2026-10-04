from datetime import date

import pytest

from strategies.portfolio import ALLOWED_POSITIONS, SLEEVES, already_decided, decide, log_symbol


def test_sleeves_sum_to_at_most_95_percent_and_crypto_is_10():
    assert sum(s.weight for s in SLEEVES) <= 0.955 + 1e-9
    assert sum(s.weight for s in SLEEVES if s.clock == "utc_day") == pytest.approx(0.10)
    assert ALLOWED_POSITIONS == {"SPY", "IBIT", "ETHA"}


def test_crypto_etfs_follow_the_backtested_coin_signal():
    assert {s.symbol: s.signal for s in SLEEVES} == {"SPY": "SPY", "IBIT": "BTC-USD", "ETHA": "ETH-USD"}


@pytest.mark.parametrize("want_long,held,expected", [
    (True, 0.0, "BUY"), (True, 1.5, "HOLD"), (False, 1.5, "SELL"), (False, 0.0, "FLAT"),
])
def test_decide_trades_only_on_flips(want_long, held, expected):
    assert decide(want_long, held) == expected


def test_log_symbol_parses_prefix_and_legacy_lines():
    assert log_symbol("2026-10-05 | BUY | 7/10 | IBIT: cross-up") == "IBIT"
    assert log_symbol("2026-10-05 | HOLD | 7/10 | position aligned; fast-slow margin +0.5%") == "SPY"
    assert log_symbol("2026-10-02 | SCAN | 6/10 | entries=[] [multi] [multi]") is None


def test_already_decided_is_per_symbol_and_day_and_ignores_halts():
    lines = [
        "2026-10-05 | BUY | 7/10 | SPY: cross-up",
        "2026-10-05 | HALT | 0/10 | kill switch active",
        "2026-10-04 | HOLD | 7/10 | ETHA: aligned",
    ]
    assert already_decided(lines, date(2026, 10, 5), "SPY")
    assert not already_decided(lines, date(2026, 10, 5), "ETHA")
    assert already_decided(lines, date(2026, 10, 4), "ETHA")
    assert not already_decided(["2026-10-05 | HALT | 0/10 | kill switch active"], date(2026, 10, 5), "SPY")
