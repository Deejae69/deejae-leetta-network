import pytest

from scripts.token_worth import (
    btc_price_from_market_cap,
    target_token_price,
    market_cap_from_price_and_supply,
    supply_from_market_cap_and_price,
    calculate_worth,
)


def test_btc_price_from_market_cap():
    assert btc_price_from_market_cap(210.0, 21.0) == 10.0


def test_target_token_price():
    assert target_token_price(10.0, 3.0) == 30.0


def test_market_cap_and_supply_inverses():
    price = 30.0
    supply = 100.0
    market_cap = market_cap_from_price_and_supply(price, supply)
    assert market_cap == 3000.0
    assert supply_from_market_cap_and_price(market_cap, price) == supply


def test_calculate_worth_from_supply():
    result = calculate_worth(btc_price=10.0, ratio=3.0, d33j_supply=100.0)
    assert result.target_d33j_price == 30.0
    assert result.d33j_market_cap == 3000.0


def test_calculate_worth_from_market_cap():
    result = calculate_worth(btc_price=10.0, ratio=3.0, d33j_market_cap=3000.0)
    assert result.target_d33j_price == 30.0
    assert result.d33j_supply == 100.0


def test_validation():
    with pytest.raises(ValueError):
        target_token_price(0.0, 30000.0)
    with pytest.raises(ValueError):
        calculate_worth(btc_price=10.0, ratio=3.0)
    with pytest.raises(ValueError):
        calculate_worth(btc_price=10.0, ratio=3.0, d33j_supply=1.0, d33j_market_cap=2.0)
