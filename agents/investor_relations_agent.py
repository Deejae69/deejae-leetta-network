"""
Investor Relations Agent
Manages investor communications and tracks traction metrics
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentTask
from config.logging_config import setup_logger

logger = setup_logger(__name__)


class InvestorRelationsAgent(BaseAgent):
    """Agent specialized in investor relations and fundraising"""

    def __init__(self):
        super().__init__(
            name="Investor Relations Agent",
            description="Manages investor communications and tracks growth metrics"
        )
        self.investor_pool = []
        self.traction_metrics = {
            "users": 0,
            "revenue": 0.0,
            "d33j_holders": 0,
            "monthly_growth": 0.0
        }
        self.funding_milestones = []

    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute investor relations task"""
        task_type = task.task_type

        if task_type == "identify_investors":
            return self._identify_investors(task.data)
        elif task_type == "create_pitch":
            return self._create_pitch(task.data)
        elif task_type == "track_traction":
            return self._track_traction(task.data)
        elif task_type == "prepare_update":
            return self._prepare_update(task.data)
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return {"status": "unknown_task_type"}

    def learn_from_result(self, task: AgentTask, result: Dict[str, Any]):
        """Learn from investor interactions"""
        if task.task_type == "track_traction":
            # Update internal traction metrics
            for key, value in result.items():
                if key in self.traction_metrics:
                    self.traction_metrics[key] = value

            logger.info(f"Updated traction metrics: {result}")

    def _identify_investors(self, data: Dict) -> Dict[str, Any]:
        """Identify potential investors"""
        investment_stage = data.get("stage", "seed")
        industry_focus = data.get("focus", "blockchain")

        logger.info(f"Identifying {investment_stage} investors focused on {industry_focus}")

        investors = {
            "stage": investment_stage,
            "focus": industry_focus,
            "potential_investors": [
                {"name": "Crypto Ventures", "type": "VC", "ticket_size": "500K-2M"},
                {"name": "Blockchain Capital", "type": "VC", "ticket_size": "1M-5M"},
                {"name": "Angel Investor Network", "type": "Angel", "ticket_size": "50K-250K"}
            ],
            "recommended_approach": "warm_intro"
        }

        self.investor_pool.extend(investors["potential_investors"])

        return investors

    def _create_pitch(self, data: Dict) -> Dict[str, Any]:
        """Create investor pitch deck"""
        pitch_type = data.get("type", "deck")

        logger.info(f"Creating {pitch_type} pitch")

        pitch = {
            "type": pitch_type,
            "sections": [
                "Problem Statement",
                "Solution (DeeJae LeEtta Network)",
                "Market Opportunity",
                "Business Model (D33J Token Economy)",
                "Traction & Metrics",
                "Team",
                "Roadmap",
                "Funding Ask"
            ],
            "key_metrics": self.traction_metrics,
            "funding_ask": data.get("funding_amount", "1M"),
            "use_of_funds": [
                "Product Development (40%)",
                "Marketing & User Acquisition (30%)",
                "Team Expansion (20%)",
                "Operations (10%)"
            ]
        }

        return pitch

    def _track_traction(self, data: Dict) -> Dict[str, Any]:
        """Track business traction metrics"""
        metric_type = data.get("metric_type", "all")

        logger.info(f"Tracking traction: {metric_type}")

        # Update metrics based on data
        if "users" in data:
            self.traction_metrics["users"] = data["users"]
        if "revenue" in data:
            self.traction_metrics["revenue"] = data["revenue"]
        if "d33j_holders" in data:
            self.traction_metrics["d33j_holders"] = data["d33j_holders"]

        # Calculate growth
        previous_users = data.get("previous_users", 0)
        if previous_users > 0:
            growth = (self.traction_metrics["users"] - previous_users) / previous_users
            self.traction_metrics["monthly_growth"] = growth

        return {
            "current_metrics": self.traction_metrics,
            "growth_trend": "positive" if self.traction_metrics["monthly_growth"] > 0 else "neutral",
            "investor_readiness_score": self._calculate_investor_readiness()
        }

    def _prepare_update(self, data: Dict) -> Dict[str, Any]:
        """Prepare investor update"""
        update_period = data.get("period", "monthly")

        logger.info(f"Preparing {update_period} investor update")

        update = {
            "period": update_period,
            "highlights": self._generate_highlights(),
            "metrics": self.traction_metrics,
            "milestones_achieved": self._get_recent_milestones(),
            "challenges": data.get("challenges", []),
            "next_steps": self._generate_next_steps(),
            "funding_status": "seeking" if len(self.investor_pool) > 0 else "not_seeking"
        }

        return update

    def _calculate_investor_readiness(self) -> float:
        """Calculate investor readiness score (0-1)"""
        score = 0.0

        # Users metric (up to 0.3)
        if self.traction_metrics["users"] > 1000:
            score += 0.3
        elif self.traction_metrics["users"] > 100:
            score += 0.15

        # Revenue metric (up to 0.3)
        if self.traction_metrics["revenue"] > 10000:
            score += 0.3
        elif self.traction_metrics["revenue"] > 1000:
            score += 0.15

        # Growth metric (up to 0.2)
        if self.traction_metrics["monthly_growth"] > 0.2:
            score += 0.2
        elif self.traction_metrics["monthly_growth"] > 0.1:
            score += 0.1

        # Token holders (up to 0.2)
        if self.traction_metrics["d33j_holders"] > 500:
            score += 0.2
        elif self.traction_metrics["d33j_holders"] > 100:
            score += 0.1

        return score

    def _generate_highlights(self) -> List[str]:
        """Generate key highlights for investor update"""
        highlights = []

        if self.traction_metrics["users"] > 0:
            highlights.append(f"Reached {self.traction_metrics['users']} users")

        if self.traction_metrics["revenue"] > 0:
            highlights.append(f"Generated ${self.traction_metrics['revenue']:.2f} in revenue")

        if self.traction_metrics["monthly_growth"] > 0:
            highlights.append(f"{self.traction_metrics['monthly_growth']:.1%} month-over-month growth")

        if not highlights:
            highlights.append("Building core product and infrastructure")

        return highlights

    def _get_recent_milestones(self) -> List[str]:
        """Get recently achieved milestones"""
        return self.funding_milestones[-5:] if self.funding_milestones else []

    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for the business"""
        return [
            "Launch AI customer acquisition MVP",
            "Scale marketing campaigns",
            "Expand team with key hires",
            "Achieve profitability milestone"
        ]
