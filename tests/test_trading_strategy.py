"""
Unit tests for trading strategy
"""

import pytest
from scripts.trading_strategy import (
    RiskManager, MomentumStrategy, MeanReversionStrategy,
    TradingEngine, SignalType
)
from config.settings import MAX_POSITION_SIZE


def test_risk_manager_initialization():
    """Test risk manager initialization"""
    rm = RiskManager(risk_tolerance=0.02, max_position_size=0.1)

    assert rm.risk_tolerance == 0.02
    assert rm.max_position_size == 0.1


def test_risk_manager_position_size():
    """Test position size calculation"""
    rm = RiskManager()

    portfolio_value = 10000
    entry_price = 100
    stop_loss_price = 95

    position_size = rm.calculate_position_size(portfolio_value, entry_price, stop_loss_price)

    assert position_size > 0
    assert position_size <= (portfolio_value * MAX_POSITION_SIZE) / entry_price


def test_momentum_strategy():
    """Test momentum strategy signal generation"""
    strategy = MomentumStrategy()

    market_data = {
        "symbol": "TEST",
        "price": 110,
        "historical_prices": [100] * 20 + [110]
    }

    signal = strategy.generate_signal(market_data)

    assert signal is not None
    assert signal.symbol == "TEST"
    assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]


def test_mean_reversion_strategy():
    """Test mean reversion strategy"""
    strategy = MeanReversionStrategy()

    market_data = {
        "symbol": "TEST",
        "price": 120,
        "historical_prices": [100] * 30
    }

    analysis = strategy.analyze_market(market_data)

    assert "z_score" in analysis
    assert "mean" in analysis


def test_trading_engine_initialization():
    """Test trading engine initialization"""
    strategies = [MomentumStrategy(), MeanReversionStrategy()]
    engine = TradingEngine(strategies)

    assert len(engine.strategies) == 2
    assert engine.mode in ["paper", "live"]
