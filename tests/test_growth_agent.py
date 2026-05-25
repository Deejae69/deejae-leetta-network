"""
Unit tests for GrowthHackerAgent
"""

import pytest
from agents.growth_hacker_agent import GrowthHackerAgent
from agents.base_agent import AgentTask
from datetime import datetime


def _make_task(task_type: str, data: dict) -> AgentTask:
    return AgentTask(
        task_id="test_" + task_type,
        task_type=task_type,
        priority=5,
        data=data,
        created_at=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_growth_agent_initialization():
    agent = GrowthHackerAgent()

    assert agent.name == "Growth Hacker Agent"
    assert agent.is_active is True
    assert len(agent.task_queue) == 0
    assert agent.referral_records == {}
    assert agent.experiments == {}


# ---------------------------------------------------------------------------
# Viral loop
# ---------------------------------------------------------------------------

def test_run_viral_loop_basic():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("run_viral_loop", {
        "channel": "discord",
        "seed_users": 100,
        "invite_rate": 0.4,
        "accept_rate": 0.5,
    }))

    assert result["channel"] == "discord"
    assert result["k_factor"] == pytest.approx(0.2, abs=1e-4)
    assert result["projected_total_reach"] > 100
    assert "is_viral" in result


def test_viral_loop_k_factor_stored():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("run_viral_loop", {
        "channel": "twitter",
        "seed_users": 50,
        "invite_rate": 0.5,
        "accept_rate": 0.5,
    }))

    assert "twitter" in agent.channel_k_factors
    assert len(agent.channel_k_factors["twitter"]) == 1


def test_viral_loop_is_viral_flag():
    agent = GrowthHackerAgent()
    # k_factor = invite_rate * accept_rate = 0.8 * 1.5 -> capped at logical max; let's use 1.0 * 1.0
    result = agent.process_task(_make_task("run_viral_loop", {
        "channel": "discord",
        "seed_users": 100,
        "invite_rate": 1.0,
        "accept_rate": 1.0,
    }))
    assert result["is_viral"] is True


# ---------------------------------------------------------------------------
# Referrals
# ---------------------------------------------------------------------------

def test_create_referral():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("create_referral", {
        "referrer_id": "user123",
        "reward_type": "d33j_tokens",
        "reward_value": 20.0,
    }))

    assert result["referrer_id"] == "user123"
    assert "referral_code" in result
    assert result["referral_url"].startswith("https://")
    assert result["reward_value"] == 20.0


def test_record_referral_conversion():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("create_referral", {
        "referrer_id": "alice",
        "reward_value": 10.0,
    }))
    result = agent.process_task(_make_task("record_referral", {
        "referrer_id": "alice",
        "referee_id": "bob",
        "converted": True,
        "reward_value": 10.0,
    }))

    assert result["converted"] is True
    assert result["reward_value"] == 10.0
    assert result["referrer_total_conversions"] == 1
    assert agent.metrics.conversions == 1


def test_record_referral_no_conversion():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("record_referral", {
        "referrer_id": "alice",
        "referee_id": "charlie",
        "converted": False,
        "reward_value": 10.0,
    }))

    assert result["converted"] is False
    assert result["reward_value"] == 0.0
    assert agent.metrics.conversions == 0


def test_get_referral_summary():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("record_referral", {
        "referrer_id": "alice", "referee_id": "bob", "converted": True, "reward_value": 5.0,
    }))
    agent.process_task(_make_task("record_referral", {
        "referrer_id": "alice", "referee_id": "eve", "converted": False, "reward_value": 5.0,
    }))

    summary = agent.get_referral_summary()

    assert summary["total_referrers"] == 1
    assert summary["total_referrals"] == 2
    assert summary["total_conversions"] == 1
    assert summary["conversion_rate"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# A/B testing
# ---------------------------------------------------------------------------

def test_ab_test_picks_winner():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("run_ab_test", {
        "experiment_id": "test_ab_1",
        "variants": [
            {"name": "control", "conversions": 40, "visitors": 500},
            {"name": "variant_a", "conversions": 80, "visitors": 500},
        ],
    }))

    assert result["winning_variant"] == "variant_a"
    assert result["winning_conversion_rate"] == pytest.approx(0.16)
    assert "test_ab_1" in agent.experiments


def test_ab_test_stored_in_experiments():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("run_ab_test", {"experiment_id": "exp_001"}))

    assert "exp_001" in agent.experiments
    assert agent.experiments["exp_001"]["status"] == "completed"


# ---------------------------------------------------------------------------
# Retention analysis
# ---------------------------------------------------------------------------

def test_analyse_retention_basic():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("analyse_retention", {
        "cohort": "may_2026",
        "day1_retention": 0.45,
        "day7_retention": 0.22,
        "day30_retention": 0.09,
    }))

    assert result["cohort"] == "may_2026"
    assert "improvement_levers" in result
    assert isinstance(result["improvement_levers"], list)
    assert len(result["improvement_levers"]) >= 1


def test_analyse_retention_stored():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("analyse_retention", {
        "cohort": "june_2026",
        "day30_retention": 0.15,
    }))

    assert "june_2026" in agent.retention_cohorts


# ---------------------------------------------------------------------------
# Growth experiments (ICE scoring)
# ---------------------------------------------------------------------------

def test_growth_experiment_high_priority():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("growth_experiment", {
        "experiment_id": "gx_referral_boost",
        "hypothesis": "Doubling referral reward increases conversions by 30%",
        "impact": 9.0,
        "confidence": 8.0,
        "ease": 9.0,
    }))

    assert result["priority"] == "high"
    assert result["ice_score"] == pytest.approx(64.8, abs=0.1)
    assert result["status"] == "planned"


def test_growth_experiment_low_priority():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("growth_experiment", {
        "experiment_id": "gx_low",
        "impact": 2.0,
        "confidence": 2.0,
        "ease": 2.0,
    }))

    assert result["priority"] == "low"


def test_growth_experiment_stored():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("growth_experiment", {
        "experiment_id": "gx_stored",
        "impact": 5.0,
        "confidence": 5.0,
        "ease": 5.0,
    }))

    assert "gx_stored" in agent.experiments


# ---------------------------------------------------------------------------
# Unknown task type
# ---------------------------------------------------------------------------

def test_unknown_task_type():
    agent = GrowthHackerAgent()
    result = agent.process_task(_make_task("nonexistent_task", {}))
    assert result["status"] == "unknown_task_type"


# ---------------------------------------------------------------------------
# Agent metrics
# ---------------------------------------------------------------------------

def test_agent_metrics_updated_after_tasks():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("run_viral_loop", {"channel": "discord"}))
    agent.process_task(_make_task("run_viral_loop", {"channel": "twitter"}))

    assert agent.metrics.tasks_completed == 2
    assert agent.metrics.success_rate == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Top viral channels
# ---------------------------------------------------------------------------

def test_get_top_viral_channels():
    agent = GrowthHackerAgent()
    agent.process_task(_make_task("run_viral_loop", {
        "channel": "discord", "invite_rate": 0.5, "accept_rate": 0.5,
    }))
    agent.process_task(_make_task("run_viral_loop", {
        "channel": "twitter", "invite_rate": 0.3, "accept_rate": 0.3,
    }))

    top = agent.get_top_viral_channels(top_n=2)

    assert len(top) == 2
    # discord should rank higher (k=0.25 vs 0.09)
    assert top[0]["channel"] == "discord"
