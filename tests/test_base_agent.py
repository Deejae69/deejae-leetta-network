"""
Unit tests for base agent functionality
"""

import pytest
from datetime import datetime
from agents.base_agent import BaseAgent, AgentTask, AgentMetrics


class TestAgent(BaseAgent):
    """Test agent implementation"""

    def execute_task(self, task):
        return {"status": "completed", "data": task.data}

    def learn_from_result(self, task, result):
        pass


def test_agent_initialization():
    """Test agent initialization"""
    agent = TestAgent("Test Agent", "A test agent")

    assert agent.name == "Test Agent"
    assert agent.description == "A test agent"
    assert agent.is_active is True
    assert len(agent.task_queue) == 0


def test_agent_add_task():
    """Test adding tasks to agent queue"""
    agent = TestAgent("Test Agent", "A test agent")

    task = AgentTask(
        task_id="test_1",
        task_type="test",
        priority=5,
        data={"test": "data"}
    )

    agent.add_task(task)

    assert len(agent.task_queue) == 1
    assert agent.task_queue[0].task_id == "test_1"


def test_agent_process_task():
    """Test processing a task"""
    agent = TestAgent("Test Agent", "A test agent")

    task = AgentTask(
        task_id="test_1",
        task_type="test",
        priority=5,
        data={"test": "data"}
    )

    result = agent.process_task(task)

    assert result["status"] == "completed"
    assert task.status == "completed"
    assert agent.metrics.tasks_completed == 1


def test_agent_metrics():
    """Test agent metrics tracking"""
    agent = TestAgent("Test Agent", "A test agent")

    task = AgentTask(
        task_id="test_1",
        task_type="test",
        priority=5,
        data={"test": "data"}
    )

    agent.process_task(task)

    status = agent.get_status()

    assert status["metrics"]["tasks_completed"] == 1
    assert status["metrics"]["tasks_failed"] == 0
    assert "100.00%" in status["metrics"]["success_rate"]
