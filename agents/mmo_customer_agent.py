"""
MMO Customer Agent
Focuses on acquiring customers for the MMO game
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentTask
from config.logging_config import setup_logger

logger = setup_logger(__name__)


class MMOCustomerAgent(BaseAgent):
    """Agent specialized in MMO customer acquisition"""

    def __init__(self):
        super().__init__(
            name="MMO Customer Agent",
            description="Acquires and engages customers for the DeeJae LeEtta MMO game"
        )
        self.target_audiences = ["gamers", "crypto_enthusiasts", "mmo_players"]
        self.campaign_history: List[Dict] = []
        self.best_performing_channels = {}

    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute MMO customer acquisition task"""
        task_type = task.task_type

        if task_type == "identify_prospects":
            return self._identify_prospects(task.data)
        elif task_type == "create_campaign":
            return self._create_campaign(task.data)
        elif task_type == "engage_user":
            return self._engage_user(task.data)
        elif task_type == "analyze_conversion":
            return self._analyze_conversion(task.data)
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return {"status": "unknown_task_type"}

    def learn_from_result(self, task: AgentTask, result: Dict[str, Any]):
        """Learn from campaign results"""
        if task.task_type == "analyze_conversion":
            channel = result.get("channel")
            conversion_rate = result.get("conversion_rate", 0)

            if channel:
                if channel not in self.best_performing_channels:
                    self.best_performing_channels[channel] = []

                self.best_performing_channels[channel].append(conversion_rate)

                # Update metrics
                if result.get("converted"):
                    self.metrics.conversions += 1
                    revenue = result.get("revenue", 0)
                    self.metrics.total_revenue_generated += revenue

            logger.info(f"Learned from conversion: {channel} - {conversion_rate:.2%}")

    def _identify_prospects(self, data: Dict) -> Dict[str, Any]:
        """Identify potential MMO customers"""
        audience = data.get("audience", "general")

        logger.info(f"Identifying prospects in {audience} audience")

        # Simulate prospect identification
        prospects = {
            "audience": audience,
            "estimated_size": 1000,
            "engagement_score": 0.75,
            "recommended_channels": ["discord", "twitter", "reddit"]
        }

        return prospects

    def _create_campaign(self, data: Dict) -> Dict[str, Any]:
        """Create MMO marketing campaign"""
        campaign_type = data.get("type", "awareness")
        channel = data.get("channel", "discord")

        logger.info(f"Creating {campaign_type} campaign for {channel}")

        campaign = {
            "campaign_id": f"mmo_{channel}_{len(self.campaign_history) + 1}",
            "type": campaign_type,
            "channel": channel,
            "message": self._generate_campaign_message(campaign_type),
            "target_audience": self.target_audiences[0],
            "estimated_reach": 5000
        }

        self.campaign_history.append(campaign)

        return campaign

    def _engage_user(self, data: Dict) -> Dict[str, Any]:
        """Engage with a potential customer"""
        user_id = data.get("user_id")
        engagement_type = data.get("type", "welcome")

        logger.info(f"Engaging user {user_id} with {engagement_type}")

        return {
            "user_id": user_id,
            "engagement_type": engagement_type,
            "message_sent": True,
            "next_action": "follow_up_24h"
        }

    def _analyze_conversion(self, data: Dict) -> Dict[str, Any]:
        """Analyze conversion data"""
        channel = data.get("channel")
        conversions = data.get("conversions", 0)
        impressions = data.get("impressions", 1)

        conversion_rate = conversions / impressions if impressions > 0 else 0

        logger.info(f"Analyzed conversion: {channel} - {conversion_rate:.2%}")

        return {
            "channel": channel,
            "conversion_rate": conversion_rate,
            "conversions": conversions,
            "impressions": impressions,
            "converted": conversions > 0,
            "revenue": conversions * 50  # Estimate $50 per conversion
        }

    def _generate_campaign_message(self, campaign_type: str) -> str:
        """Generate campaign message based on type"""
        messages = {
            "awareness": "Discover the DeeJae LeEtta MMO - Where gaming meets blockchain! Earn D33J tokens while playing.",
            "engagement": "Join our MMO community! Early access available for D33J holders.",
            "conversion": "Limited time offer: Get exclusive MMO beta access with D33J tokens!"
        }

        return messages.get(campaign_type, "Join the DeeJae LeEtta Network!")

    def get_best_channels(self) -> List[str]:
        """Get best performing channels"""
        if not self.best_performing_channels:
            return []

        # Calculate average conversion rate per channel
        channel_avg = {
            channel: sum(rates) / len(rates)
            for channel, rates in self.best_performing_channels.items()
        }

        # Sort by average conversion rate
        sorted_channels = sorted(channel_avg.items(), key=lambda x: x[1], reverse=True)

        return [channel for channel, _ in sorted_channels]
