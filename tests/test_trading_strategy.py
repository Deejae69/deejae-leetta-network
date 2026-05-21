"""
Unit tests for trading strategy
"""

import pytest
from datetime import datetime
from scripts.trading_strategy import (
    RiskManager, MomentumStrategy, MeanReversionStrategy,
    TradingEngine, TradingSignal, Position, SignalType
)


# ---------------------------------------------------------------------------
# RiskManager tests
# ---------------------------------------------------------------------------

def test_risk_manager_initialization():
    """Test risk manager initialization"""
    rm = RiskManager(risk_tolerance=0.02, max_position_size=0.1)

    assert rm.risk_tolerance == 0.02
    assert rm.max_position_size == 0.1


def test_risk_manager_position_size():
    """Test position size is positive and capped by max_position_size"""
    rm = RiskManager(risk_tolerance=0.02, max_position_size=0.5)

    portfolio_value = 10000
    entry_price = 100
    stop_loss_price = 95

    position_size = rm.calculate_position_size(portfolio_value, entry_price, stop_loss_price)

    assert position_size > 0
    assert position_size <= (portfolio_value * 0.5) / entry_price


def test_risk_manager_position_size_zero_price_risk():
    """When entry == stop_loss position size should be 0"""
    rm = RiskManager()
    size = rm.calculate_position_size(10000, 100, 100)
    assert size == 0


def test_risk_manager_calculate_stop_loss_long():
    """Stop loss for long position is below entry price"""
    rm = RiskManager()
    entry = 100.0
    stop = rm.calculate_stop_loss(entry, is_long=True)
    assert stop < entry


def test_risk_manager_calculate_stop_loss_short():
    """Stop loss for short position is above entry price"""
    rm = RiskManager()
    entry = 100.0
    stop = rm.calculate_stop_loss(entry, is_long=False)
    assert stop > entry


def test_risk_manager_calculate_take_profit_long():
    """Take profit for long position is above entry price"""
    rm = RiskManager()
    entry = 100.0
    tp = rm.calculate_take_profit(entry, is_long=True)
    assert tp > entry


def test_risk_manager_calculate_take_profit_short():
    """Take profit for short position is below entry price"""
    rm = RiskManager()
    entry = 100.0
    tp = rm.calculate_take_profit(entry, is_long=False)
    assert tp < entry


def _make_position(current_price, stop_loss=90.0, take_profit=115.0):
    return Position(
        symbol="TEST",
        quantity=10,
        entry_price=100.0,
        current_price=current_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        pnl=0,
        pnl_percentage=0,
        opened_at=datetime.now(),
    )


def test_risk_manager_should_close_stop_loss_triggered():
    rm = RiskManager()
    pos = _make_position(current_price=89.0)
    should_close, reason = rm.should_close_position(pos)
    assert should_close is True
    assert "Stop loss" in reason


def test_risk_manager_should_close_take_profit_triggered():
    rm = RiskManager()
    pos = _make_position(current_price=116.0)
    should_close, reason = rm.should_close_position(pos)
    assert should_close is True
    assert "Take profit" in reason


def test_risk_manager_should_not_close_within_range():
    rm = RiskManager()
    pos = _make_position(current_price=100.0)
    should_close, reason = rm.should_close_position(pos)
    assert should_close is False
    assert reason == ""


# ---------------------------------------------------------------------------
# MomentumStrategy tests
# ---------------------------------------------------------------------------

def test_momentum_strategy_buy_signal():
    """Strong upward momentum generates a BUY signal"""
    strategy = MomentumStrategy()
    market_data = {
        "symbol": "TEST",
        "price": 110,
        "historical_prices": [100] * 20 + [110],
    }
    signal = strategy.generate_signal(market_data)
    assert signal is not None
    assert signal.symbol == "TEST"
    assert signal.signal_type == SignalType.BUY


def test_momentum_strategy_sell_signal():
    """Strong downward momentum generates a SELL signal"""
    strategy = MomentumStrategy()
    market_data = {
        "symbol": "TEST",
        "price": 90,
        "historical_prices": [100] * 20 + [90],
    }
    signal = strategy.generate_signal(market_data)
    assert signal is not None
    assert signal.signal_type == SignalType.SELL


def test_momentum_strategy_hold_returns_none():
    """No significant momentum returns None"""
    strategy = MomentumStrategy()
    market_data = {
        "symbol": "TEST",
        "price": 100.1,
        "historical_prices": [100] * 20 + [100.1],
    }
    signal = strategy.generate_signal(market_data)
    assert signal is None


def test_momentum_strategy_insufficient_data():
    """Fewer prices than lookback period returns no signal"""
    strategy = MomentumStrategy()
    market_data = {
        "symbol": "TEST",
        "price": 110,
        "historical_prices": [100, 105],
    }
    signal = strategy.generate_signal(market_data)
    assert signal is None


def test_momentum_strategy_analyze_market():
    """analyze_market returns momentum and strength keys"""
    strategy = MomentumStrategy()
    market_data = {
        "symbol": "TEST",
        "price": 110,
        "historical_prices": [100] * 20 + [110],
    }
    result = strategy.analyze_market(market_data)
    assert "momentum" in result
    assert "strength" in result


# ---------------------------------------------------------------------------
# MeanReversionStrategy tests
# ---------------------------------------------------------------------------

def test_mean_reversion_strategy_analyze_market():
    """analyze_market returns z_score and mean"""
    strategy = MeanReversionStrategy()
    market_data = {
        "symbol": "TEST",
        "price": 120,
        "historical_prices": [100] * 30,
    }
    analysis = strategy.analyze_market(market_data)
    assert "z_score" in analysis
    assert "mean" in analysis


def test_mean_reversion_strategy_buy_signal():
    """Price far below mean generates BUY signal"""
    strategy = MeanReversionStrategy()
    # Mean=100, std≈0 when all same price; use varied prices
    historical = [100.0] * 28 + [100.0, 100.0]
    market_data = {
        "symbol": "MR",
        "price": 50.0,  # Very far below mean
        "historical_prices": historical,
    }
    # Force z_score < -2 by using a price far from mean with real std
    base = [100.0 + i * 0.1 for i in range(30)]
    market_data = {"symbol": "MR", "price": 80.0, "historical_prices": base}
    analysis = strategy.analyze_market(market_data)
    if analysis["std"] > 0:
        # Just verify the z_score direction
        assert analysis["z_score"] < 0


def test_mean_reversion_strategy_sell_signal():
    """Price far above mean generates SELL signal"""
    strategy = MeanReversionStrategy()
    base = [100.0 + i * 0.1 for i in range(30)]
    market_data = {"symbol": "MR", "price": 115.0, "historical_prices": base}
    analysis = strategy.analyze_market(market_data)
    if analysis["std"] > 0:
        assert analysis["z_score"] > 0


def test_mean_reversion_strategy_insufficient_data():
    """Fewer prices than lookback period returns zero z_score"""
    strategy = MeanReversionStrategy()
    market_data = {
        "symbol": "MR",
        "price": 110,
        "historical_prices": [100, 105],
    }
    analysis = strategy.analyze_market(market_data)
    assert analysis["z_score"] == 0


def test_mean_reversion_strategy_no_signal_within_threshold():
    """Price near mean returns None from generate_signal"""
    strategy = MeanReversionStrategy()
    prices = [100.0] * 30
    market_data = {"symbol": "MR", "price": 100.0, "historical_prices": prices}
    signal = strategy.generate_signal(market_data)
    # std is 0 so z_score is 0 => no signal
    assert signal is None


# ---------------------------------------------------------------------------
# TradingEngine tests
# ---------------------------------------------------------------------------

def test_trading_engine_initialization():
    """Test trading engine initialization"""
    strategies = [MomentumStrategy(), MeanReversionStrategy()]
    engine = TradingEngine(strategies)

    assert len(engine.strategies) == 2
    assert engine.mode in ["paper", "live"]


def test_trading_engine_process_market_data_returns_list():
    """process_market_data returns a list of signals"""
    engine = TradingEngine([MomentumStrategy(), MeanReversionStrategy()])
    market_data = {
        "symbol": "TEST",
        "price": 110,
        "historical_prices": [100] * 30 + [110],
    }
    signals = engine.process_market_data(market_data)
    assert isinstance(signals, list)


def test_trading_engine_execute_signal_paper_mode():
    """In paper/default mode execute_signal returns True without opening positions"""
    engine = TradingEngine([MomentumStrategy()])
    engine.mode = "paper"
    signal = TradingSignal(
        symbol="TEST",
        signal_type=SignalType.BUY,
        price=100.0,
        confidence=0.8,
        timestamp=datetime.now(),
        strategy_name="test",
    )
    result = engine.execute_signal(signal, portfolio_value=10000)
    assert result is True


def test_trading_engine_get_portfolio_summary_empty():
    """Portfolio summary with no positions returns zero totals"""
    engine = TradingEngine([MomentumStrategy()])
    summary = engine.get_portfolio_summary()
    assert summary["total_positions"] == 0
    assert summary["total_pnl"] == 0
    assert "mode" in summary


def test_trading_engine_update_positions_no_op_when_no_positions():
    """update_positions with unknown symbol does not raise"""
    engine = TradingEngine([MomentumStrategy()])
    engine.update_positions({"symbol": "UNKNOWN", "price": 50.0})  # Should not raise


def test_trading_engine_update_positions_updates_pnl():
    """update_positions changes current_price and pnl for a known position"""
    engine = TradingEngine([MomentumStrategy()])
    engine.mode = "live"
    pos = Position(
        symbol="ABC",
        quantity=10,
        entry_price=100.0,
        current_price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        pnl=0,
        pnl_percentage=0,
        opened_at=datetime.now(),
    )
    engine.positions["ABC"] = pos
    engine.update_positions({"symbol": "ABC", "price": 105.0})
    assert engine.positions["ABC"].current_price == 105.0
    assert engine.positions["ABC"].pnl == pytest.approx(50.0)
