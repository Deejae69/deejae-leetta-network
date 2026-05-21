"""
Agent Orchestrator
Coordinates all AI agents and manages task distribution
"""

from typing import List, Dict, Any
import threading
from queue import Queue
from agents.base_agent import BaseAgent, AgentTask
from agents.mmo_customer_agent import MMOCustomerAgent
from agents.ecommerce_client_finder import ECommerceClientFinder
from agents.arts_marketing_agent import ArtsMarketingAgent
from agents.investor_relations_agent import InvestorRelationsAgent
from agents.trading_strategy_agent import TradingStrategyAgent
from agents.campaign_optimizer_agent import CampaignOptimizerAgent
from agents.growth_hacker_agent import GrowthHackerAgent
from config.logging_config import setup_logger
from config.error_handlers import ErrorContext

logger = setup_logger(__name__)


class AgentOrchestrator:
    """Orchestrates all AI agents in the DeeJae LeEtta Network"""

    def __init__(self):
        self.agents: List[BaseAgent] = []
        self.task_queue = Queue()
        self.is_running = False
        self._initialize_agents()
        logger.info("AgentOrchestrator initialized with 7 agents")

    def _initialize_agents(self):
        """Initialize all agents"""
        self.agents = [
            MMOCustomerAgent(),
            ECommerceClientFinder(),
            ArtsMarketingAgent(),
            InvestorRelationsAgent(),
            TradingStrategyAgent(),
            CampaignOptimizerAgent(),
            GrowthHackerAgent(),
        ]

    def start(self):
        """Start the orchestrator"""
        self.is_running = True
        logger.info("AgentOrchestrator started")

        # Start processing tasks in background threads
        for agent in self.agents:
            thread = threading.Thread(target=self._agent_worker, args=(agent,))
            thread.daemon = True
            thread.start()

    def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        logger.info("AgentOrchestrator stopped")

    def add_task(self, agent_name: str, task: AgentTask):
        """
        Add a task for a specific agent

        Args:
            agent_name: Name of the agent
            task: Task to execute
        """
        agent = self.get_agent(agent_name)
        if agent:
            agent.add_task(task)
            logger.info(f"Task {task.task_id} added to {agent_name}")
        else:
            logger.error(f"Agent {agent_name} not found")

    def get_agent(self, agent_name: str) -> BaseAgent:
        """Get agent by name"""
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        return None

    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        return [agent.get_status() for agent in self.agents]

    def distribute_task(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently distribute a task to the most appropriate agent

        Args:
            task_type: Type of task
            data: Task data

        Returns:
            Result from agent
        """
        agent = self._select_agent_for_task(task_type)

        if not agent:
            logger.error(f"No suitable agent found for task type: {task_type}")
            return {"error": "No suitable agent found"}

        from datetime import datetime
        import uuid

        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            priority=data.get("priority", 5),
            data=data,
            created_at=datetime.now()
        )

        logger.info(f"Distributing task {task.task_id} to {agent.name}")

        return agent.process_task(task)

    def _select_agent_for_task(self, task_type: str) -> BaseAgent:
        """Select the best agent for a task type"""
        task_routing = {
            # MMO Customer Agent tasks
            "identify_prospects": "MMO Customer Agent",
            "create_campaign": "MMO Customer Agent",
            "engage_user": "MMO Customer Agent",

            # E-Commerce Client Finder tasks
            "find_clients": "E-Commerce Client Finder",
            "segment_customers": "E-Commerce Client Finder",
            "optimize_funnel": "E-Commerce Client Finder",
            "track_purchase": "E-Commerce Client Finder",

            # Arts Marketing Agent tasks
            "create_content": "Arts Marketing Agent",
            "schedule_post": "Arts Marketing Agent",
            "analyze_engagement": "Arts Marketing Agent",
            "collaborate": "Arts Marketing Agent",

            # Investor Relations Agent tasks
            "identify_investors": "Investor Relations Agent",
            "create_pitch": "Investor Relations Agent",
            "track_traction": "Investor Relations Agent",
            "prepare_update": "Investor Relations Agent",

            # Trading Strategy Agent tasks
            "analyze_market": "Trading Strategy Agent",
            "execute_trade": "Trading Strategy Agent",
            "monitor_positions": "Trading Strategy Agent",
            "rebalance_portfolio": "Trading Strategy Agent",

            # Campaign Optimizer Agent tasks
            "analyze_campaign": "Campaign Optimizer Agent",
            "optimize_budget": "Campaign Optimizer Agent",
            "predict_performance": "Campaign Optimizer Agent",
            "recommend_channels": "Campaign Optimizer Agent",
            "analyze_conversion": "Campaign Optimizer Agent",

            # Growth Hacker Agent tasks
            "run_viral_loop":    "Growth Hacker Agent",
            "create_referral":   "Growth Hacker Agent",
            "record_referral":   "Growth Hacker Agent",
            "run_ab_test":       "Growth Hacker Agent",
            "analyse_retention": "Growth Hacker Agent",
            "growth_experiment": "Growth Hacker Agent",
        }

        agent_name = task_routing.get(task_type)
        return self.get_agent(agent_name) if agent_name else None

    def _agent_worker(self, agent: BaseAgent):
        """Worker thread for processing agent tasks"""
        while self.is_running:
            try:
                if agent.task_queue:
                    agent.process_queue()
                else:
                    import time
                    time.sleep(1)  # Sleep if no tasks
            except Exception as e:
                logger.error(f"Error in agent worker for {agent.name}: {e}")

    def run_daily_tasks(self):
        """Run daily automated tasks for all agents"""
        logger.info("Running daily tasks for all agents")

        with ErrorContext("Daily tasks execution"):
            # Example daily tasks
            tasks = [
                ("MMO Customer Agent", "identify_prospects", {"audience": "gamers"}),
                ("Campaign Optimizer Agent", "analyze_campaign", {
                    "campaign_id": "daily_check",
                    "metrics": {"impressions": 1000, "clicks": 50, "conversions": 5, "cost": 100}
                }),
                ("Investor Relations Agent", "track_traction", {
                    "users": 1000,
                    "revenue": 5000,
                    "d33j_holders": 200
                }),
                ("Trading Strategy Agent", "monitor_positions", {"market_data": {}})
            ]

            results = []
            for agent_name, task_type, data in tasks:
                try:
                    result = self.distribute_task(task_type, data)
                    results.append({"agent": agent_name, "task": task_type, "result": result})
                except Exception as e:
                    logger.error(f"Error running task {task_type} for {agent_name}: {e}")
                    results.append({"agent": agent_name, "task": task_type, "error": str(e)})

            return results

    def get_network_metrics(self) -> Dict[str, Any]:
        """Get overall network metrics from all agents"""
        metrics = {
            "total_agents": len(self.agents),
            "active_agents": sum(1 for agent in self.agents if agent.is_active),
            "total_tasks_completed": sum(agent.metrics.tasks_completed for agent in self.agents),
            "total_revenue_generated": sum(agent.metrics.total_revenue_generated for agent in self.agents),
            "total_conversions": sum(agent.metrics.conversions for agent in self.agents),
            "avg_success_rate": sum(agent.metrics.success_rate for agent in self.agents) / len(self.agents),
            "agents": self.get_all_agents_status()
        }

        return metrics


# Singleton instance
orchestrator = AgentOrchestrator()
