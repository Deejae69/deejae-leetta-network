"""
Campaign Optimizer Agent
Optimizes marketing campaigns based on performance data
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentTask
from config.logging_config import setup_logger

logger = setup_logger(__name__)


class CampaignOptimizerAgent(BaseAgent):
    """Agent specialized in campaign optimization and ML-driven decisions"""

    def __init__(self):
        super().__init__(
            name="Campaign Optimizer Agent",
            description="Optimizes campaigns using machine learning and performance data"
        )
        self.campaign_performance = {}
        self.channel_scores = {}
        self.optimization_history = []

    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute campaign optimization task"""
        task_type = task.task_type

        if task_type == "analyze_campaign":
            return self._analyze_campaign(task.data)
        elif task_type == "optimize_budget":
            return self._optimize_budget(task.data)
        elif task_type == "predict_performance":
            return self._predict_performance(task.data)
        elif task_type == "recommend_channels":
            return self._recommend_channels(task.data)
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return {"status": "unknown_task_type"}

    def learn_from_result(self, task: AgentTask, result: Dict[str, Any]):
        """Learn from campaign optimization results"""
        if task.task_type == "analyze_campaign":
            campaign_id = result.get("campaign_id")
            performance_score = result.get("performance_score", 0)

            if campaign_id:
                self.campaign_performance[campaign_id] = performance_score

            # Update channel scores
            channel = result.get("channel")
            if channel:
                if channel not in self.channel_scores:
                    self.channel_scores[channel] = []
                self.channel_scores[channel].append(performance_score)

            logger.info(f"Learned from campaign {campaign_id}: score={performance_score}")

    def _analyze_campaign(self, data: Dict) -> Dict[str, Any]:
        """Analyze campaign performance"""
        campaign_id = data.get("campaign_id")
        metrics = data.get("metrics", {})

        logger.info(f"Analyzing campaign {campaign_id}")

        impressions = metrics.get("impressions", 0)
        clicks = metrics.get("clicks", 0)
        conversions = metrics.get("conversions", 0)
        cost = metrics.get("cost", 0)

        # Calculate KPIs
        ctr = clicks / impressions if impressions > 0 else 0
        conversion_rate = conversions / clicks if clicks > 0 else 0
        cpa = cost / conversions if conversions > 0 else float('inf')
        roi = ((conversions * metrics.get("avg_order_value", 0)) - cost) / cost if cost > 0 else 0

        # Calculate performance score (0-100)
        performance_score = self._calculate_performance_score(ctr, conversion_rate, roi)

        analysis = {
            "campaign_id": campaign_id,
            "channel": data.get("channel"),
            "performance_score": performance_score,
            "kpis": {
                "ctr": ctr,
                "conversion_rate": conversion_rate,
                "cpa": cpa,
                "roi": roi
            },
            "recommendation": self._generate_recommendation(performance_score, roi),
            "optimization_opportunities": self._identify_optimizations(metrics)
        }

        return analysis

    def _optimize_budget(self, data: Dict) -> Dict[str, Any]:
        """Optimize budget allocation across campaigns"""
        total_budget = data.get("total_budget", 10000)
        campaigns = data.get("campaigns", [])

        logger.info(f"Optimizing budget: ${total_budget} across {len(campaigns)} campaigns")

        if not campaigns:
            return {"status": "no_campaigns", "allocation": {}}

        # Calculate performance-weighted allocation
        campaign_scores = {}
        total_score = 0

        for campaign in campaigns:
            campaign_id = campaign.get("campaign_id")
            performance = self.campaign_performance.get(campaign_id, 50)  # Default to 50
            campaign_scores[campaign_id] = performance
            total_score += performance

        # Allocate budget proportionally to performance
        allocation = {}
        for campaign_id, score in campaign_scores.items():
            if total_score > 0:
                allocation[campaign_id] = (score / total_score) * total_budget
            else:
                allocation[campaign_id] = total_budget / len(campaigns)

        optimization = {
            "total_budget": total_budget,
            "allocation": allocation,
            "expected_roi": self._estimate_roi(allocation),
            "optimization_strategy": "performance_weighted"
        }

        self.optimization_history.append(optimization)

        return optimization

    def _predict_performance(self, data: Dict) -> Dict[str, Any]:
        """Predict campaign performance"""
        campaign_config = data.get("config", {})
        channel = campaign_config.get("channel")

        logger.info(f"Predicting performance for {channel} campaign")

        # Use historical data to predict
        historical_performance = self.channel_scores.get(channel, [50])
        avg_performance = sum(historical_performance) / len(historical_performance)

        # Simple prediction model (in production, would use ML model)
        predicted_ctr = avg_performance / 1000  # Rough estimate
        predicted_conversions = campaign_config.get("budget", 1000) * 0.02  # 2% conversion

        prediction = {
            "channel": channel,
            "predicted_performance_score": avg_performance,
            "predicted_ctr": predicted_ctr,
            "predicted_conversions": predicted_conversions,
            "confidence": 0.7 if len(historical_performance) > 5 else 0.4,
            "recommendation": "proceed" if avg_performance > 60 else "test_small"
        }

        return prediction

    def _recommend_channels(self, data: Dict) -> Dict[str, Any]:
        """Recommend best channels for a campaign"""
        campaign_type = data.get("type", "general")
        target_audience = data.get("target_audience", "general")

        logger.info(f"Recommending channels for {campaign_type} campaign")

        # Rank channels by historical performance
        ranked_channels = []

        for channel, scores in self.channel_scores.items():
            avg_score = sum(scores) / len(scores)
            ranked_channels.append({
                "channel": channel,
                "score": avg_score,
                "sample_size": len(scores)
            })

        # Sort by score
        ranked_channels.sort(key=lambda x: x["score"], reverse=True)

        # If no historical data, use defaults
        if not ranked_channels:
            ranked_channels = [
                {"channel": "instagram", "score": 70, "sample_size": 0},
                {"channel": "twitter", "score": 65, "sample_size": 0},
                {"channel": "discord", "score": 60, "sample_size": 0}
            ]

        recommendation = {
            "campaign_type": campaign_type,
            "target_audience": target_audience,
            "recommended_channels": ranked_channels[:3],  # Top 3
            "budget_allocation": self._suggest_channel_budget(ranked_channels[:3])
        }

        return recommendation

    def _calculate_performance_score(self, ctr: float, conversion_rate: float, roi: float) -> float:
        """Calculate overall performance score (0-100)"""
        # Weighted average of normalized metrics
        ctr_score = min(ctr * 1000, 10) * 10  # Up to 10% of score
        conversion_score = min(conversion_rate * 100, 20) * 5  # Up to 100% of conversion rate
        roi_score = min(max(roi, 0), 2) * 50  # ROI from 0-2x

        total_score = (ctr_score * 0.2) + (conversion_score * 0.3) + (roi_score * 0.5)

        return min(total_score, 100)

    def _generate_recommendation(self, performance_score: float, roi: float) -> str:
        """Generate recommendation based on performance"""
        if performance_score > 75 and roi > 1.5:
            return "scale_up"
        elif performance_score > 60 and roi > 0.5:
            return "continue"
        elif performance_score > 40:
            return "optimize"
        else:
            return "pause_or_restructure"

    def _identify_optimizations(self, metrics: Dict) -> List[str]:
        """Identify optimization opportunities"""
        opportunities = []

        ctr = metrics.get("clicks", 0) / metrics.get("impressions", 1)
        conversion_rate = metrics.get("conversions", 0) / metrics.get("clicks", 1)

        if ctr < 0.02:
            opportunities.append("Improve ad creative and targeting to increase CTR")

        if conversion_rate < 0.05:
            opportunities.append("Optimize landing page and offer to improve conversions")

        if not opportunities:
            opportunities.append("Performance is good, consider scaling")

        return opportunities

    def _estimate_roi(self, allocation: Dict[str, float]) -> float:
        """Estimate ROI from budget allocation"""
        # Simplified ROI estimation
        total_expected = 0
        total_budget = sum(allocation.values())

        for campaign_id, budget in allocation.items():
            performance = self.campaign_performance.get(campaign_id, 50)
            expected_return = budget * (performance / 50)  # Assumes 50 = 1x return
            total_expected += expected_return

        return (total_expected - total_budget) / total_budget if total_budget > 0 else 0

    def _suggest_channel_budget(self, channels: List[Dict]) -> Dict[str, str]:
        """Suggest budget allocation percentages for channels"""
        if not channels:
            return {}

        total_score = sum(ch["score"] for ch in channels)

        allocation = {}
        for channel in channels:
            percentage = (channel["score"] / total_score * 100) if total_score > 0 else 33.3
            allocation[channel["channel"]] = f"{percentage:.1f}%"

        return allocation
