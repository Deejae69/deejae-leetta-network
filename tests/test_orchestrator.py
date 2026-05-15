"""
Integration tests for agent orchestrator
"""

import pytest
from scripts.agent_orchestrator import AgentOrchestrator


def test_orchestrator_initialization():
    """Test orchestrator initialization"""
    orchestrator = AgentOrchestrator()

    assert len(orchestrator.agents) == 6
    assert orchestrator.is_running is False


def test_orchestrator_get_agent():
    """Test getting agent by name"""
    orchestrator = AgentOrchestrator()

    agent = orchestrator.get_agent("MMO Customer Agent")

    assert agent is not None
    assert agent.name == "MMO Customer Agent"


def test_orchestrator_distribute_task():
    """Test task distribution"""
    orchestrator = AgentOrchestrator()

    result = orchestrator.distribute_task(
        "identify_prospects",
        {"audience": "gamers"}
    )

    assert "audience" in result
    assert result["audience"] == "gamers"


def test_orchestrator_network_metrics():
    """Test getting network metrics"""
    orchestrator = AgentOrchestrator()

    # Run a sample task
    orchestrator.distribute_task("identify_prospects", {"audience": "gamers"})

    metrics = orchestrator.get_network_metrics()

    assert "total_agents" in metrics
    assert metrics["total_agents"] == 6
    assert "active_agents" in metrics
