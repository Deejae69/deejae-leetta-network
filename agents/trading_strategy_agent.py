"""
Trading Strategy Agent
Executes trading strategies and investment decisions
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentTask
from config.logging_config import setup_logger
from scripts.trading_strategy import (
    TradingEngine, MomentumStrategy, MeanReversionStrategy, TradingSignal
)

logger = setup_logger(__name__)


class TradingStrategyAgent(BaseAgent):
    """Agent specialized in trading and investment strategies"""

    def __init__(self):
        super().__init__(
            name="Trading Strategy Agent",
            description="Executes trading strategies with risk management"
        )
        # Initialize trading engine with strategies
        self.trading_engine = TradingEngine([
            MomentumStrategy(),
            MeanReversionStrategy()
        ])
        self.portfolio_value = 10000.0  # Starting portfolio
        self.trade_history = []

    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute trading strategy task"""
        task_type = task.task_type

        if task_type == "analyze_market":
            return self._analyze_market(task.data)
        elif task_type == "execute_trade":
            return self._execute_trade(task.data)
        elif task_type == "monitor_positions":
            return self._monitor_positions(task.data)
        elif task_type == "rebalance_portfolio":
            return self._rebalance_portfolio(task.data)
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return {"status": "unknown_task_type"}

    def learn_from_result(self, task: AgentTask, result: Dict[str, Any]):
        """Learn from trading results"""
        if task.task_type == "execute_trade":
            success = result.get("success", False)
            pnl = result.get("pnl", 0)

            if success:
                self.portfolio_value += pnl
                self.metrics.total_revenue_generated += max(0, pnl)

            self.trade_history.append(result)

            logger.info(f"Learned from trade: PnL=${pnl:.2f}, Portfolio=${self.portfolio_value:.2f}")

    def _analyze_market(self, data: Dict) -> Dict[str, Any]:
        """Analyze market and generate signals"""
        market_data = data.get("market_data", {})

        logger.info(f"Analyzing market for {market_data.get('symbol', 'unknown')}")

        # Generate signals from all strategies
        signals = self.trading_engine.process_market_data(market_data)

        analysis = {
            "symbol": market_data.get("symbol"),
            "current_price": market_data.get("price"),
            "signals_generated": len(signals),
            "signals": [
                {
                    "strategy": sig.strategy_name,
                    "signal_type": sig.signal_type.value,
                    "confidence": sig.confidence,
                    "price": sig.price
                }
                for sig in signals
            ],
            "recommendation": self._determine_recommendation(signals)
        }

        return analysis

    def _execute_trade(self, data: Dict) -> Dict[str, Any]:
        """Execute a trade"""
        signal_data = data.get("signal")

        if not signal_data:
            return {"success": False, "error": "No signal provided"}

        logger.info(f"Executing trade: {signal_data}")

        # Create signal object (simplified - in production would use actual signal)
        from scripts.trading_strategy import SignalType
        from datetime import datetime

        signal = TradingSignal(
            symbol=signal_data.get("symbol"),
            signal_type=SignalType(signal_data.get("signal_type", "buy")),
            price=signal_data.get("price"),
            confidence=signal_data.get("confidence", 0.7),
            timestamp=datetime.now(),
            strategy_name=signal_data.get("strategy", "manual")
        )

        # Execute through trading engine
        success = self.trading_engine.execute_signal(signal, self.portfolio_value)

        trade_result = {
            "success": success,
            "symbol": signal.symbol,
            "signal_type": signal.signal_type.value,
            "price": signal.price,
            "pnl": 0,  # Would calculate actual PnL
            "timestamp": signal.timestamp.isoformat()
        }

        return trade_result

    def _monitor_positions(self, data: Dict) -> Dict[str, Any]:
        """Monitor open positions"""
        market_data = data.get("market_data", {})

        logger.info("Monitoring open positions")

        # Update positions with current market data
        self.trading_engine.update_positions(market_data)

        # Get portfolio summary
        summary = self.trading_engine.get_portfolio_summary()

        monitoring_result = {
            "portfolio_value": self.portfolio_value,
            "open_positions": summary["total_positions"],
            "positions": summary["positions"],
            "total_pnl": summary["total_pnl"],
            "mode": summary["mode"]
        }

        return monitoring_result

    def _rebalance_portfolio(self, data: Dict) -> Dict[str, Any]:
        """Rebalance portfolio based on strategy"""
        target_allocation = data.get("target_allocation", {})

        logger.info("Rebalancing portfolio")

        rebalance_result = {
            "status": "completed",
            "previous_allocation": self._get_current_allocation(),
            "target_allocation": target_allocation,
            "trades_executed": [],
            "new_portfolio_value": self.portfolio_value
        }

        return rebalance_result

    def _determine_recommendation(self, signals: List[TradingSignal]) -> str:
        """Determine overall recommendation from multiple signals"""
        if not signals:
            return "hold"

        from scripts.trading_strategy import SignalType

        buy_signals = sum(1 for s in signals if s.signal_type == SignalType.BUY)
        sell_signals = sum(1 for s in signals if s.signal_type == SignalType.SELL)

        if buy_signals > sell_signals:
            return "buy"
        elif sell_signals > buy_signals:
            return "sell"
        else:
            return "hold"

    def _get_current_allocation(self) -> Dict[str, float]:
        """Get current portfolio allocation"""
        positions = self.trading_engine.positions

        if not positions:
            return {"cash": 1.0}

        allocation = {}
        total_value = self.portfolio_value

        for symbol, position in positions.items():
            position_value = position.current_price * position.quantity
            allocation[symbol] = position_value / total_value if total_value > 0 else 0

        cash_value = self.portfolio_value - sum(
            pos.current_price * pos.quantity for pos in positions.values()
        )
        allocation["cash"] = max(0, cash_value / total_value) if total_value > 0 else 1.0

        return allocation

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        win_rate = 0.0
        if self.trade_history:
            wins = sum(1 for trade in self.trade_history if trade.get("pnl", 0) > 0)
            win_rate = wins / len(self.trade_history)

        return {
            "portfolio_value": self.portfolio_value,
            "total_trades": len(self.trade_history),
            "win_rate": win_rate,
            "total_pnl": self.metrics.total_revenue_generated,
            "mode": self.trading_engine.mode
        }
