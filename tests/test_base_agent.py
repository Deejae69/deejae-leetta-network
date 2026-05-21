"""
Unit tests for base agent functionality
"""

import pytest
from datetime import datetime
from agents.base_agent import BaseAgent, AgentTask, AgentMetrics


class ConcreteAgent(BaseAgent):
    """Concrete agent for testing (avoids pytest collecting the class as a test suite)"""

    def __init__(self, fail=False):
        super().__init__("Concrete Agent", "A concrete test agent")
        self._fail = fail

    def execute_task(self, task):
        if self._fail:
            raise ValueError("Simulated failure")
        return {"status": "completed", "data": task.data}

    def learn_from_result(self, task, result):
        pass


def _make_task(task_id="t1", task_type="test", priority=5, data=None):
    return AgentTask(
        task_id=task_id,
        task_type=task_type,
        priority=priority,
        data=data or {"key": "value"},
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_agent_initialization():
    """Test agent initialization"""
    agent = ConcreteAgent()

    assert agent.name == "Concrete Agent"
    assert agent.description == "A concrete test agent"
    assert agent.is_active is True
    assert len(agent.task_queue) == 0


def test_agent_initial_metrics_are_zero():
    agent = ConcreteAgent()
    assert agent.metrics.tasks_completed == 0
    assert agent.metrics.tasks_failed == 0
    assert agent.metrics.success_rate == 0.0
    assert agent.metrics.conversions == 0
    assert agent.metrics.total_revenue_generated == 0.0


# ---------------------------------------------------------------------------
# Task queue
# ---------------------------------------------------------------------------

def test_agent_add_task():
    """Test adding tasks to agent queue"""
    agent = ConcreteAgent()

    task = _make_task()
    agent.add_task(task)

    assert len(agent.task_queue) == 1
    assert agent.task_queue[0].task_id == "t1"


def test_agent_add_multiple_tasks():
    agent = ConcreteAgent()
    for i in range(3):
        agent.add_task(_make_task(task_id=f"t{i}"))
    assert len(agent.task_queue) == 3


# ---------------------------------------------------------------------------
# Task processing — success path
# ---------------------------------------------------------------------------

def test_agent_process_task():
    """Test processing a task"""
    agent = ConcreteAgent()
    task = _make_task()

    result = agent.process_task(task)

    assert result["status"] == "completed"
    assert task.status == "completed"
    assert agent.metrics.tasks_completed == 1
    assert agent.metrics.tasks_failed == 0


def test_agent_process_task_updates_success_rate():
    agent = ConcreteAgent()
    agent.process_task(_make_task("t1"))
    agent.process_task(_make_task("t2"))
    assert agent.metrics.success_rate == pytest.approx(1.0)


def test_agent_process_task_result_stored_on_task():
    agent = ConcreteAgent()
    task = _make_task(data={"x": 42})
    agent.process_task(task)
    assert task.result is not None
    assert task.result["status"] == "completed"


# ---------------------------------------------------------------------------
# Task processing — failure path
# ---------------------------------------------------------------------------

def test_agent_failed_task_increments_failed_counter():
    agent = ConcreteAgent(fail=True)
    task = _make_task()
    with pytest.raises(Exception):
        agent.process_task(task)
    # retry_on_failure retries 3 times, incrementing tasks_failed each attempt
    assert agent.metrics.tasks_failed == 3
    assert agent.metrics.tasks_completed == 0


def test_agent_failed_task_sets_status_failed():
    agent = ConcreteAgent(fail=True)
    task = _make_task()
    with pytest.raises(Exception):
        agent.process_task(task)
    assert task.status == "failed"


def test_agent_success_rate_mixed():
    """50% success rate when one success, one failure"""
    success_agent = ConcreteAgent(fail=False)
    success_agent.process_task(_make_task("s1"))

    fail_agent = ConcreteAgent(fail=True)
    with pytest.raises(Exception):
        fail_agent.process_task(_make_task("f1"))

    # Check an agent that has both via metrics manipulation
    agent = ConcreteAgent()
    agent.metrics.tasks_completed = 1
    agent.metrics.tasks_failed = 1
    agent._update_success_rate()
    assert agent.metrics.success_rate == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Queue processing
# ---------------------------------------------------------------------------

def test_agent_process_queue_drains_queue():
    agent = ConcreteAgent()
    for i in range(3):
        agent.add_task(_make_task(task_id=f"q{i}"))
    agent.process_queue()
    assert len(agent.task_queue) == 0
    assert agent.metrics.tasks_completed == 3


def test_agent_inactive_stops_queue_processing():
    agent = ConcreteAgent()
    agent.is_active = False
    agent.add_task(_make_task())
    agent.process_queue()
    # Queue is not drained because agent is inactive
    assert len(agent.task_queue) == 1
    assert agent.metrics.tasks_completed == 0


# ---------------------------------------------------------------------------
# Metrics / status
# ---------------------------------------------------------------------------

def test_agent_metrics():
    """Test agent metrics tracking"""
    agent = ConcreteAgent()
    agent.process_task(_make_task())

    status = agent.get_status()

    assert status["metrics"]["tasks_completed"] == 1
    assert status["metrics"]["tasks_failed"] == 0
    assert "100.00%" in status["metrics"]["success_rate"]


def test_agent_get_status_structure():
    agent = ConcreteAgent()
    status = agent.get_status()
    assert "name" in status
    assert "description" in status
    assert "is_active" in status
    assert "queue_length" in status
    assert "metrics" in status


def test_agent_avg_completion_time_updated():
    agent = ConcreteAgent()
    agent.process_task(_make_task("t1"))
    agent.process_task(_make_task("t2"))
    assert agent.metrics.avg_completion_time >= 0.0
