"""
Growth Hacker Agent
Drives organic and viral growth for the DeeJae LeEtta Network through
referral programmes, A/B experiments, retention loops, and network-effect
strategies.
"""

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AgentTask
from config.logging_config import setup_logger

logger = setup_logger(__name__)


class GrowthHackerAgent(BaseAgent):
    """Agent specialised in viral growth, referral mechanics, and experimentation."""

    def __init__(self):
        super().__init__(
            name="Growth Hacker Agent",
            description=(
                "Drives user acquisition and retention through referral programmes, "
                "A/B experiments, viral loops, and cohort-based retention analysis"
            )
        )
        # Referral tracking: referrer_id -> list of converted referral records
        self.referral_records: Dict[str, List[Dict]] = {}
        # A/B experiment store: experiment_id -> experiment state dict
        self.experiments: Dict[str, Dict] = {}
        # Retention cohorts: cohort_label -> list of retention-rate samples
        self.retention_cohorts: Dict[str, List[float]] = {}
        # Channel virality coefficients learned from data
        self.channel_k_factors: Dict[str, List[float]] = {}

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Dispatch to the appropriate growth task handler."""
        handlers = {
            "run_viral_loop":        self._run_viral_loop,
            "create_referral":       self._create_referral,
            "record_referral":       self._record_referral,
            "run_ab_test":           self._run_ab_test,
            "analyse_retention":     self._analyse_retention,
            "growth_experiment":     self._growth_experiment,
        }
        handler = handlers.get(task.task_type)
        if handler is None:
            logger.warning(f"GrowthHackerAgent: unknown task type '{task.task_type}'")
            return {"status": "unknown_task_type"}
        return handler(task.data)

    def learn_from_result(self, task: AgentTask, result: Dict[str, Any]):
        """Update internal models from completed task outcomes."""
        if task.task_type == "run_viral_loop":
            channel = result.get("channel")
            k_factor = result.get("k_factor", 0.0)
            if channel is not None:
                self.channel_k_factors.setdefault(channel, []).append(k_factor)
                logger.info(
                    f"GrowthHackerAgent: learned k-factor {k_factor:.2f} for channel '{channel}'"
                )

        elif task.task_type in ("run_ab_test", "growth_experiment"):
            exp_id = result.get("experiment_id")
            winner = result.get("winning_variant")
            if exp_id and winner and exp_id in self.experiments:
                self.experiments[exp_id]["winner"] = winner
                logger.info(
                    f"GrowthHackerAgent: experiment '{exp_id}' winner recorded as '{winner}'"
                )

        elif task.task_type == "analyse_retention":
            cohort = result.get("cohort")
            rate = result.get("day30_retention", 0.0)
            if cohort is not None:
                self.retention_cohorts.setdefault(cohort, []).append(rate)
                logger.info(
                    f"GrowthHackerAgent: retention {rate:.1%} recorded for cohort '{cohort}'"
                )

        elif task.task_type == "record_referral":
            if result.get("converted"):
                self.metrics.conversions += 1
                revenue = result.get("reward_value", 0.0)
                self.metrics.total_revenue_generated += revenue

    # ------------------------------------------------------------------
    # Task implementations
    # ------------------------------------------------------------------

    def _run_viral_loop(self, data: Dict) -> Dict[str, Any]:
        """Model a viral-loop cycle and return projected reach."""
        channel = data.get("channel", "discord")
        seed_users = int(data.get("seed_users", 100))
        invite_rate = float(data.get("invite_rate", 0.3))   # fraction who send invites
        accept_rate = float(data.get("accept_rate", 0.25))  # fraction of invites accepted

        k_factor = invite_rate * accept_rate
        new_users_wave1 = seed_users * k_factor
        new_users_wave2 = new_users_wave1 * k_factor
        projected_total = seed_users + new_users_wave1 + new_users_wave2

        logger.info(
            f"GrowthHackerAgent: viral loop on '{channel}' — "
            f"k={k_factor:.2f}, projected reach={projected_total:.0f}"
        )

        return {
            "channel": channel,
            "seed_users": seed_users,
            "k_factor": round(k_factor, 4),
            "projected_new_users_wave1": round(new_users_wave1, 1),
            "projected_new_users_wave2": round(new_users_wave2, 1),
            "projected_total_reach": round(projected_total, 1),
            "is_viral": k_factor >= 1.0,
        }

    def _create_referral(self, data: Dict) -> Dict[str, Any]:
        """Generate a referral link/code for a user."""
        referrer_id = data.get("referrer_id", "unknown")
        reward_type = data.get("reward_type", "d33j_tokens")
        reward_value = float(data.get("reward_value", 10.0))

        referral_code = f"REF-{referrer_id.upper()[:8]}"

        if referrer_id not in self.referral_records:
            self.referral_records[referrer_id] = []

        logger.info(
            f"GrowthHackerAgent: referral code '{referral_code}' created "
            f"for user '{referrer_id}' (reward: {reward_value} {reward_type})"
        )

        return {
            "referrer_id": referrer_id,
            "referral_code": referral_code,
            "referral_url": f"https://deejaeleetta.store/join?ref={referral_code}",
            "reward_type": reward_type,
            "reward_value": reward_value,
            "total_referrals_so_far": len(self.referral_records[referrer_id]),
        }

    def _record_referral(self, data: Dict) -> Dict[str, Any]:
        """Record a referral conversion event."""
        referrer_id = data.get("referrer_id", "unknown")
        referee_id = data.get("referee_id", "unknown")
        converted = bool(data.get("converted", False))
        reward_value = float(data.get("reward_value", 10.0))

        record = {
            "referee_id": referee_id,
            "converted": converted,
            "reward_value": reward_value if converted else 0.0,
        }

        self.referral_records.setdefault(referrer_id, []).append(record)

        logger.info(
            f"GrowthHackerAgent: referral recorded — "
            f"referrer={referrer_id}, referee={referee_id}, converted={converted}"
        )

        return {
            "referrer_id": referrer_id,
            "referee_id": referee_id,
            "converted": converted,
            "reward_value": record["reward_value"],
            "referrer_total_conversions": sum(
                1 for r in self.referral_records[referrer_id] if r["converted"]
            ),
        }

    def _run_ab_test(self, data: Dict) -> Dict[str, Any]:
        """Simulate an A/B test and pick a winner by conversion rate."""
        experiment_id = data.get("experiment_id", f"exp_{len(self.experiments) + 1}")
        variants = data.get("variants", [
            {"name": "control", "conversions": 50, "visitors": 500},
            {"name": "variant_a", "conversions": 65, "visitors": 500},
        ])

        results = []
        best_variant: Optional[str] = None
        best_rate = -1.0

        for v in variants:
            name = v.get("name", "unnamed")
            conversions = int(v.get("conversions", 0))
            visitors = int(v.get("visitors", 1))
            rate = conversions / visitors if visitors > 0 else 0.0
            results.append({"variant": name, "conversion_rate": round(rate, 4), "visitors": visitors})
            if rate > best_rate:
                best_rate = rate
                best_variant = name

        self.experiments[experiment_id] = {
            "variants": results,
            "winner": best_variant,
            "status": "completed",
        }

        logger.info(
            f"GrowthHackerAgent: A/B test '{experiment_id}' — winner: '{best_variant}' "
            f"({best_rate:.2%})"
        )

        return {
            "experiment_id": experiment_id,
            "results": results,
            "winning_variant": best_variant,
            "winning_conversion_rate": round(best_rate, 4),
        }

    def _analyse_retention(self, data: Dict) -> Dict[str, Any]:
        """Analyse user retention for a cohort and suggest improvement levers."""
        cohort = data.get("cohort", "default")
        day1 = float(data.get("day1_retention", 0.4))
        day7 = float(data.get("day7_retention", 0.2))
        day30 = float(data.get("day30_retention", 0.1))

        churn_d1_d7 = day1 - day7
        churn_d7_d30 = day7 - day30

        levers = []
        if day1 < 0.5:
            levers.append("Improve onboarding flow to increase Day-1 activation")
        if churn_d1_d7 > 0.2:
            levers.append("Add early-engagement nudges (push/email) in Days 2–7")
        if churn_d7_d30 > 0.1:
            levers.append("Introduce habit-forming features or weekly community events")
        if not levers:
            levers.append("Retention is healthy — focus on top-of-funnel growth")

        logger.info(
            f"GrowthHackerAgent: retention analysis for cohort '{cohort}' — "
            f"D1={day1:.0%}, D7={day7:.0%}, D30={day30:.0%}"
        )

        return {
            "cohort": cohort,
            "day1_retention": day1,
            "day7_retention": day7,
            "day30_retention": day30,
            "churn_day1_to_day7": round(churn_d1_d7, 4),
            "churn_day7_to_day30": round(churn_d7_d30, 4),
            "improvement_levers": levers,
        }

    def _growth_experiment(self, data: Dict) -> Dict[str, Any]:
        """Define and log a structured growth experiment (ICE-scored)."""
        experiment_id = data.get("experiment_id", f"gx_{len(self.experiments) + 1}")
        hypothesis = data.get("hypothesis", "")
        impact = float(data.get("impact", 5.0))       # 1–10
        confidence = float(data.get("confidence", 5.0))  # 1–10
        ease = float(data.get("ease", 5.0))           # 1–10

        ice_score = (impact * confidence * ease) / 10.0
        priority = (
            "high" if ice_score >= 50 else
            "medium" if ice_score >= 20 else
            "low"
        )

        self.experiments[experiment_id] = {
            "hypothesis": hypothesis,
            "ice_score": ice_score,
            "priority": priority,
            "status": "planned",
            "winner": None,
        }

        logger.info(
            f"GrowthHackerAgent: experiment '{experiment_id}' — "
            f"ICE={ice_score:.1f} ({priority})"
        )

        return {
            "experiment_id": experiment_id,
            "hypothesis": hypothesis,
            "ice_score": round(ice_score, 2),
            "priority": priority,
            "status": "planned",
        }

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_top_viral_channels(self, top_n: int = 3) -> List[Dict[str, Any]]:
        """Return the channels with the highest average k-factor."""
        averages = [
            {"channel": ch, "avg_k_factor": sum(ks) / len(ks)}
            for ch, ks in self.channel_k_factors.items()
            if ks
        ]
        averages.sort(key=lambda x: x["avg_k_factor"], reverse=True)
        return averages[:top_n]

    def get_referral_summary(self) -> Dict[str, Any]:
        """Return an aggregated referral programme summary."""
        total_referrers = len(self.referral_records)
        total_referrals = sum(len(v) for v in self.referral_records.values())
        total_conversions = sum(
            1 for records in self.referral_records.values()
            for r in records if r["converted"]
        )
        conversion_rate = total_conversions / total_referrals if total_referrals > 0 else 0.0

        return {
            "total_referrers": total_referrers,
            "total_referrals": total_referrals,
            "total_conversions": total_conversions,
            "conversion_rate": round(conversion_rate, 4),
        }
