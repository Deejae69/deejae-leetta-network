"""
Growth API Blueprint for DeeJae LeEtta Network.

Exposes:
    GET  /api/growth/traction         — aggregated traction / KPI dashboard
    GET  /api/growth/referrals        — referral programme summary
    POST /api/growth/referrals        — create a new referral code for a user
    POST /api/growth/referrals/record — record a referral conversion event
    GET  /api/growth/experiments      — list growth experiments (with ICE scores)
    POST /api/growth/experiments      — register a new growth experiment
    GET  /api/growth/viral            — viral-loop channel leaderboard
    POST /api/growth/viral            — run a viral-loop projection
    GET  /api/growth/retention        — retention cohort summary
    POST /api/growth/retention        — submit retention data for analysis
"""

from flask import Blueprint, request, jsonify

from agents.growth_hacker_agent import GrowthHackerAgent
from agents.base_agent import AgentTask
from config.logging_config import setup_logger

import uuid
from datetime import datetime

logger = setup_logger(__name__)

growth_bp = Blueprint("growth", __name__, url_prefix="/api/growth")

# Module-level singleton so state is shared across requests within a process.
_growth_agent = GrowthHackerAgent()


# ---------------------------------------------------------------------------
# Traction dashboard
# ---------------------------------------------------------------------------

@growth_bp.route("/traction", methods=["GET"])
def get_traction():
    """Return an aggregated traction / KPI dashboard."""
    try:
        referral_summary = _growth_agent.get_referral_summary()
        top_channels = _growth_agent.get_top_viral_channels()

        # Retention overview: last known D30 per cohort
        retention_overview = {
            cohort: round(rates[-1], 4)
            for cohort, rates in _growth_agent.retention_cohorts.items()
            if rates
        }

        # Experiment counts
        experiments = _growth_agent.experiments
        exp_summary = {
            "total": len(experiments),
            "planned": sum(1 for e in experiments.values() if e.get("status") == "planned"),
            "completed": sum(1 for e in experiments.values() if e.get("status") == "completed"),
        }

        return jsonify({
            "referrals": referral_summary,
            "top_viral_channels": top_channels,
            "retention_overview": retention_overview,
            "experiments": exp_summary,
            "agent_metrics": _growth_agent.get_status()["metrics"],
        }), 200
    except Exception as e:
        logger.error(f"Error fetching growth traction: {e}")
        return jsonify({"error": "Internal error"}), 500


# ---------------------------------------------------------------------------
# Referral programme
# ---------------------------------------------------------------------------

@growth_bp.route("/referrals", methods=["GET"])
def get_referrals():
    """Return referral programme summary."""
    try:
        return jsonify(_growth_agent.get_referral_summary()), 200
    except Exception as e:
        logger.error(f"Error fetching referrals: {e}")
        return jsonify({"error": "Internal error"}), 500


@growth_bp.route("/referrals", methods=["POST"])
def create_referral():
    """Create a referral code for a user."""
    try:
        data = request.get_json(force=True) or {}
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="create_referral",
            priority=5,
            data=data,
            created_at=datetime.now(),
        )
        result = _growth_agent.process_task(task)
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Error creating referral: {e}")
        return jsonify({"error": "Internal error"}), 500


@growth_bp.route("/referrals/record", methods=["POST"])
def record_referral():
    """Record a referral conversion event."""
    try:
        data = request.get_json(force=True) or {}
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="record_referral",
            priority=5,
            data=data,
            created_at=datetime.now(),
        )
        result = _growth_agent.process_task(task)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error recording referral: {e}")
        return jsonify({"error": "Internal error"}), 500


# ---------------------------------------------------------------------------
# Growth experiments
# ---------------------------------------------------------------------------

@growth_bp.route("/experiments", methods=["GET"])
def list_experiments():
    """List all growth experiments."""
    try:
        experiments = [
            {"experiment_id": eid, **state}
            for eid, state in _growth_agent.experiments.items()
        ]
        return jsonify({"experiments": experiments, "total": len(experiments)}), 200
    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        return jsonify({"error": "Internal error"}), 500


@growth_bp.route("/experiments", methods=["POST"])
def create_experiment():
    """Register a new growth experiment (ICE-scored)."""
    try:
        data = request.get_json(force=True) or {}
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="growth_experiment",
            priority=5,
            data=data,
            created_at=datetime.now(),
        )
        result = _growth_agent.process_task(task)
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        return jsonify({"error": "Internal error"}), 500


# ---------------------------------------------------------------------------
# Viral loops
# ---------------------------------------------------------------------------

@growth_bp.route("/viral", methods=["GET"])
def get_viral_channels():
    """Return the viral-loop channel leaderboard."""
    try:
        top = _growth_agent.get_top_viral_channels(top_n=10)
        return jsonify({"channels": top, "total": len(top)}), 200
    except Exception as e:
        logger.error(f"Error fetching viral channels: {e}")
        return jsonify({"error": "Internal error"}), 500


@growth_bp.route("/viral", methods=["POST"])
def run_viral_loop():
    """Run a viral-loop projection for a channel."""
    try:
        data = request.get_json(force=True) or {}
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="run_viral_loop",
            priority=5,
            data=data,
            created_at=datetime.now(),
        )
        result = _growth_agent.process_task(task)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error running viral loop: {e}")
        return jsonify({"error": "Internal error"}), 500


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

@growth_bp.route("/retention", methods=["GET"])
def get_retention():
    """Return retention cohort overview."""
    try:
        cohorts = [
            {
                "cohort": cohort,
                "samples": len(rates),
                "latest_day30_retention": round(rates[-1], 4) if rates else None,
                "avg_day30_retention": round(sum(rates) / len(rates), 4) if rates else None,
            }
            for cohort, rates in _growth_agent.retention_cohorts.items()
        ]
        return jsonify({"cohorts": cohorts, "total": len(cohorts)}), 200
    except Exception as e:
        logger.error(f"Error fetching retention: {e}")
        return jsonify({"error": "Internal error"}), 500


@growth_bp.route("/retention", methods=["POST"])
def analyse_retention():
    """Submit retention data for a cohort and receive improvement recommendations."""
    try:
        data = request.get_json(force=True) or {}
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="analyse_retention",
            priority=5,
            data=data,
            created_at=datetime.now(),
        )
        result = _growth_agent.process_task(task)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error analysing retention: {e}")
        return jsonify({"error": "Internal error"}), 500
