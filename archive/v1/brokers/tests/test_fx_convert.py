import pytest

from brokers.fx_convert import plan_usd_purchase


def test_converts_98_percent_rounded_down_to_a_thousand():
    # 1,000,000 CAD * 0.98 / 1.40 CAD per USD = 700,000 USD
    assert plan_usd_purchase({"CAD": 1_000_000.0}, cad_per_usd=1.40) == 700_000
    assert plan_usd_purchase({"CAD": 1_000_000.0}, cad_per_usd=1.3777) == 711_000


def test_does_nothing_when_usd_is_already_held():
    assert plan_usd_purchase({"CAD": 20_000.0, "USD": 700_000.0}, cad_per_usd=1.40) == 0


def test_does_nothing_without_cad():
    assert plan_usd_purchase({}, cad_per_usd=1.40) == 0


@pytest.mark.parametrize("rate", [0.0, -1.0, 0.5, 3.0])
def test_rejects_an_implausible_exchange_rate(rate):
    with pytest.raises(RuntimeError, match="CAD per USD"):
        plan_usd_purchase({"CAD": 1_000_000.0}, cad_per_usd=rate)
