"""
Trading Strategy Framework for DeeJae LeEtta Network
Implements investment strategies with risk management
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from config.logging_config import setup_logger
from config.error_handlers import TradingError, retry_on_failure
from config.settings import (
    RISK_TOLERANCE,
    MAX_POSITION_SIZE,
    STOP_LOSS_PERCENTAGE,
    TAKE_PROFIT_PERCENTAGE,
    TRADING_MODE
)

logger = setup_logger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


@dataclass
class TradingSignal:
    """Trading signal data structure"""
    symbol: str
    signal_type: SignalType
    price: float
    confidence: float
    timestamp: datetime
    strategy_name: str
    metadata: Dict = None


@dataclass
class Position:
    """Trading position data structure"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    pnl: float
    pnl_percentage: float
    opened_at: datetime


class RiskManager:
    """Risk management for trading strategies"""

    def __init__(self, risk_tolerance: float = RISK_TOLERANCE,
                 max_position_size: float = MAX_POSITION_SIZE):
        self.risk_tolerance = risk_tolerance
        self.max_position_size = max_position_size
        logger.info(f"RiskManager initialized: risk_tolerance={risk_tolerance}, max_position_size={max_position_size}")

    def calculate_position_size(self, portfolio_value: float, entry_price: float,
                                stop_loss_price: float) -> float:
        """
        Calculate position size based on risk tolerance

        Args:
            portfolio_value: Total portfolio value
            entry_price: Entry price for the position
            stop_loss_price: Stop loss price

        Returns:
            Position size (number of units)
        """
        risk_amount = portfolio_value * self.risk_tolerance
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk == 0:
            logger.warning("Price risk is zero, using minimum position size")
            return 0

        position_size = risk_amount / price_risk

        # Cap at max position size
        max_size = (portfolio_value * self.max_position_size) / entry_price
        position_size = min(position_size, max_size)

        logger.debug(f"Calculated position size: {position_size} units")
        return position_size

    def calculate_stop_loss(self, entry_price: float, is_long: bool = True) -> float:
        """Calculate stop loss price"""
        if is_long:
            return entry_price * (1 - STOP_LOSS_PERCENTAGE)
        return entry_price * (1 + STOP_LOSS_PERCENTAGE)

    def calculate_take_profit(self, entry_price: float, is_long: bool = True) -> float:
        """Calculate take profit price"""
        if is_long:
            return entry_price * (1 + TAKE_PROFIT_PERCENTAGE)
        return entry_price * (1 - TAKE_PROFIT_PERCENTAGE)

    def should_close_position(self, position: Position) -> Tuple[bool, str]:
        """
        Determine if a position should be closed

        Args:
            position: Current position

        Returns:
            Tuple of (should_close, reason)
        """
        if position.current_price <= position.stop_loss:
            return True, "Stop loss triggered"

        if position.current_price >= position.take_profit:
            return True, "Take profit triggered"

        return False, ""


class TradingStrategy(ABC):
    """Abstract base class for trading strategies"""

    def __init__(self, name: str):
        self.name = name
        self.risk_manager = RiskManager()
        logger.info(f"Strategy '{name}' initialized")

    @abstractmethod
    def generate_signal(self, market_data: Dict) -> Optional[TradingSignal]:
        """
        Generate trading signal based on market data

        Args:
            market_data: Current market data

        Returns:
            Trading signal or None
        """
        pass

    @abstractmethod
    def analyze_market(self, market_data: Dict) -> Dict:
        """
        Analyze market conditions

        Args:
            market_data: Market data to analyze

        Returns:
            Analysis results
        """
        pass


class MomentumStrategy(TradingStrategy):
    """Momentum-based trading strategy"""

    def __init__(self):
        super().__init__("Momentum Strategy")
        self.lookback_period = 20
        self.momentum_threshold = 0.02

    def generate_signal(self, market_data: Dict) -> Optional[TradingSignal]:
        """Generate signal based on momentum"""
        try:
            analysis = self.analyze_market(market_data)

            if analysis['momentum'] > self.momentum_threshold:
                return TradingSignal(
                    symbol=market_data['symbol'],
                    signal_type=SignalType.BUY,
                    price=market_data['price'],
                    confidence=min(analysis['momentum'] / (self.momentum_threshold * 2), 1.0),
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata=analysis
                )
            elif analysis['momentum'] < -self.momentum_threshold:
                return TradingSignal(
                    symbol=market_data['symbol'],
                    signal_type=SignalType.SELL,
                    price=market_data['price'],
                    confidence=min(abs(analysis['momentum']) / (self.momentum_threshold * 2), 1.0),
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata=analysis
                )

            return None

        except Exception as e:
            logger.error(f"Error generating momentum signal: {e}")
            return None

    def analyze_market(self, market_data: Dict) -> Dict:
        """Analyze market momentum"""
        # Simplified momentum calculation
        prices = market_data.get('historical_prices', [])

        if len(prices) < self.lookback_period:
            return {'momentum': 0, 'strength': 'weak'}

        current_price = market_data['price']
        past_price = prices[-self.lookback_period]

        momentum = (current_price - past_price) / past_price

        strength = 'strong' if abs(momentum) > self.momentum_threshold * 2 else 'moderate'

        return {
            'momentum': momentum,
            'strength': strength,
            'lookback_period': self.lookback_period
        }


class MeanReversionStrategy(TradingStrategy):
    """Mean reversion trading strategy"""

    def __init__(self):
        super().__init__("Mean Reversion Strategy")
        self.lookback_period = 30
        self.std_threshold = 2.0

    def generate_signal(self, market_data: Dict) -> Optional[TradingSignal]:
        """Generate signal based on mean reversion"""
        try:
            analysis = self.analyze_market(market_data)

            if analysis['z_score'] < -self.std_threshold:
                return TradingSignal(
                    symbol=market_data['symbol'],
                    signal_type=SignalType.BUY,
                    price=market_data['price'],
                    confidence=min(abs(analysis['z_score']) / (self.std_threshold * 2), 1.0),
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata=analysis
                )
            elif analysis['z_score'] > self.std_threshold:
                return TradingSignal(
                    symbol=market_data['symbol'],
                    signal_type=SignalType.SELL,
                    price=market_data['price'],
                    confidence=min(analysis['z_score'] / (self.std_threshold * 2), 1.0),
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata=analysis
                )

            return None

        except Exception as e:
            logger.error(f"Error generating mean reversion signal: {e}")
            return None

    def analyze_market(self, market_data: Dict) -> Dict:
        """Analyze mean reversion opportunity"""
        prices = market_data.get('historical_prices', [])

        if len(prices) < self.lookback_period:
            return {'z_score': 0, 'mean': 0, 'std': 0}

        import statistics

        mean = statistics.mean(prices[-self.lookback_period:])
        std = statistics.stdev(prices[-self.lookback_period:])

        if std == 0:
            return {'z_score': 0, 'mean': mean, 'std': std}

        current_price = market_data['price']
        z_score = (current_price - mean) / std

        return {
            'z_score': z_score,
            'mean': mean,
            'std': std,
            'current_price': current_price
        }


class TradingEngine:
    """Main trading engine that orchestrates strategies"""

    def __init__(self, strategies: List[TradingStrategy]):
        self.strategies = strategies
        self.risk_manager = RiskManager()
        self.positions: Dict[str, Position] = {}
        self.mode = TRADING_MODE
        logger.info(f"TradingEngine initialized with {len(strategies)} strategies in {self.mode} mode")

    def process_market_data(self, market_data: Dict) -> List[TradingSignal]:
        """
        Process market data through all strategies

        Args:
            market_data: Current market data

        Returns:
            List of trading signals
        """
        signals = []

        for strategy in self.strategies:
            signal = strategy.generate_signal(market_data)
            if signal:
                logger.info(f"Signal generated by {strategy.name}: {signal.signal_type.value} {signal.symbol} at {signal.price}")
                signals.append(signal)

        return signals

    @retry_on_failure(max_retries=3)
    def execute_signal(self, signal: TradingSignal, portfolio_value: float) -> bool:
        """
        Execute a trading signal

        Args:
            signal: Trading signal to execute
            portfolio_value: Current portfolio value

        Returns:
            True if execution successful
        """
        if self.mode != "live":
            logger.info(f"[{self.mode.upper()} MODE] Would execute: {signal.signal_type.value} {signal.symbol} at {signal.price}")
            return True

        try:
            if signal.signal_type == SignalType.BUY:
                stop_loss = self.risk_manager.calculate_stop_loss(signal.price, is_long=True)
                take_profit = self.risk_manager.calculate_take_profit(signal.price, is_long=True)
                position_size = self.risk_manager.calculate_position_size(
                    portfolio_value, signal.price, stop_loss
                )

                position = Position(
                    symbol=signal.symbol,
                    quantity=position_size,
                    entry_price=signal.price,
                    current_price=signal.price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    pnl=0,
                    pnl_percentage=0,
                    opened_at=datetime.now()
                )

                self.positions[signal.symbol] = position
                logger.info(f"Opened position: {signal.symbol} x{position_size} @ {signal.price}")

            elif signal.signal_type == SignalType.SELL:
                if signal.symbol in self.positions:
                    position = self.positions.pop(signal.symbol)
                    pnl = (signal.price - position.entry_price) * position.quantity
                    logger.info(f"Closed position: {signal.symbol} with PnL: {pnl}")

            return True

        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            raise TradingError(f"Failed to execute signal: {e}")

    def update_positions(self, market_data: Dict):
        """Update all open positions with current market data"""
        symbol = market_data['symbol']

        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = market_data['price']
            position.pnl = (position.current_price - position.entry_price) * position.quantity
            position.pnl_percentage = (position.current_price - position.entry_price) / position.entry_price

            should_close, reason = self.risk_manager.should_close_position(position)
            if should_close:
                logger.info(f"Closing position {symbol}: {reason}")
                # Execute close order
                self.positions.pop(symbol)

    def get_portfolio_summary(self) -> Dict:
        """Get summary of all positions"""
        total_pnl = sum(pos.pnl for pos in self.positions.values())

        return {
            'total_positions': len(self.positions),
            'positions': [
                {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'pnl': pos.pnl,
                    'pnl_percentage': pos.pnl_percentage * 100
                }
                for pos in self.positions.values()
            ],
            'total_pnl': total_pnl,
            'mode': self.mode
        }
