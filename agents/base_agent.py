"""
Base Agent Framework for DeeJae LeEtta Network
Provides common functionality for all AI agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from config.logging_config import setup_logger
from config.error_handlers import AgentError, retry_on_failure, ErrorContext

logger = setup_logger(__name__)


@dataclass
class AgentTask:
    """Represents a task for an agent to complete"""
    task_id: str
    task_type: str
    priority: int
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Dict] = None


@dataclass
class AgentMetrics:
    """Metrics for agent performance tracking"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = 0.0
    avg_completion_time: float = 0.0
    total_revenue_generated: float = 0.0
    conversions: int = 0


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.metrics = AgentMetrics()
        self.is_active = True
        self.task_queue: List[AgentTask] = []
        logger.info(f"Agent '{name}' initialized: {description}")

    @abstractmethod
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a specific task

        Args:
            task: Task to execute

        Returns:
            Task results
        """
        pass

    @abstractmethod
    def learn_from_result(self, task: AgentTask, result: Dict[str, Any]):
        """
        Learn from task results to improve future performance

        Args:
            task: Completed task
            result: Task result
        """
        pass

    @retry_on_failure(max_retries=3)
    def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a task with error handling and learning

        Args:
            task: Task to process

        Returns:
            Task results
        """
        with ErrorContext(f"Agent {self.name} processing task {task.task_id}"):
            start_time = datetime.now()

            try:
                logger.info(f"{self.name}: Starting task {task.task_id} ({task.task_type})")

                task.status = "in_progress"
                result = self.execute_task(task)

                task.status = "completed"
                task.result = result

                # Update metrics
                completion_time = (datetime.now() - start_time).total_seconds()
                self.metrics.tasks_completed += 1
                self._update_avg_completion_time(completion_time)
                self._update_success_rate()

                # Learn from result
                self.learn_from_result(task, result)

                logger.info(f"{self.name}: Completed task {task.task_id} in {completion_time:.2f}s")

                return result

            except Exception as e:
                task.status = "failed"
                self.metrics.tasks_failed += 1
                self._update_success_rate()

                logger.error(f"{self.name}: Failed task {task.task_id}: {str(e)}")
                raise AgentError(f"Task execution failed: {str(e)}")

    def add_task(self, task: AgentTask):
        """Add a task to the agent's queue"""
        self.task_queue.append(task)
        logger.debug(f"{self.name}: Added task {task.task_id} to queue")

    def process_queue(self):
        """Process all tasks in the queue"""
        logger.info(f"{self.name}: Processing {len(self.task_queue)} tasks in queue")

        while self.task_queue and self.is_active:
            task = self.task_queue.pop(0)
            try:
                self.process_task(task)
            except Exception as e:
                logger.error(f"{self.name}: Error processing task: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics"""
        return {
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "queue_length": len(self.task_queue),
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": f"{self.metrics.success_rate:.2%}",
                "avg_completion_time": f"{self.metrics.avg_completion_time:.2f}s",
                "total_revenue_generated": f"${self.metrics.total_revenue_generated:.2f}",
                "conversions": self.metrics.conversions
            }
        }

    def _update_avg_completion_time(self, new_time: float):
        """Update average completion time"""
        total_tasks = self.metrics.tasks_completed
        self.metrics.avg_completion_time = (
            (self.metrics.avg_completion_time * (total_tasks - 1) + new_time) / total_tasks
        )

    def _update_success_rate(self):
        """Update success rate"""
        total = self.metrics.tasks_completed + self.metrics.tasks_failed
        if total > 0:
            self.metrics.success_rate = self.metrics.tasks_completed / total
