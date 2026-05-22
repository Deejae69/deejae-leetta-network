"""Tests for scripts/run_agents.py."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_agents as run_agents


class TestRunAgentsHelpers(unittest.TestCase):
    def test_get_test_data_known_and_unknown(self):
        known = run_agents.get_test_data("identify_prospects")
        unknown = run_agents.get_test_data("does_not_exist")
        self.assertEqual(known, {"audience": "gamers"})
        self.assertEqual(unknown, {})


class TestRunAgentsFlow(unittest.TestCase):
    def test_run_test_without_task_runs_samples(self):
        with patch("scripts.run_agents.run_sample_tasks") as sample_tasks:
            run_agents.run_test(agent_name=None, task_type=None)
        sample_tasks.assert_called_once()

    def test_run_test_with_unknown_agent_returns_early(self):
        with patch.object(run_agents, "orchestrator") as orch:
            orch.get_agent.return_value = None
            run_agents.run_test(agent_name="Missing", task_type="identify_prospects")
            orch.distribute_task.assert_not_called()

    def test_run_test_with_specific_task_distributes(self):
        with patch.object(run_agents, "orchestrator") as orch:
            orch.get_agent.return_value = object()
            orch.distribute_task.return_value = {"ok": True}
            run_agents.run_test(agent_name="Any", task_type="identify_prospects")
            orch.distribute_task.assert_called_once_with("identify_prospects", {"audience": "gamers"})

    def test_run_daily_tasks_uses_orchestrator_and_metrics(self):
        with patch.object(run_agents, "orchestrator") as orch:
            orch.run_daily_tasks.return_value = [{"agent": "A", "task": "T", "result": "done"}]
            orch.get_network_metrics.return_value = {
                "total_revenue_generated": 10.0,
                "total_conversions": 2,
                "total_tasks_completed": 3,
                "avg_success_rate": 0.5,
            }
            run_agents.run_daily_tasks()
            orch.run_daily_tasks.assert_called_once()
            orch.get_network_metrics.assert_called_once()

    def test_run_daemon_stops_on_keyboard_interrupt(self):
        with patch.object(run_agents, "orchestrator") as orch, patch("time.sleep", side_effect=KeyboardInterrupt):
            run_agents.run_daemon()
            orch.start.assert_called_once()
            orch.stop.assert_called_once()

    def test_run_sample_tasks_handles_success_and_error(self):
        statuses = [
            {
                "name": "Agent1",
                "is_active": True,
                "metrics": {
                    "tasks_completed": 1,
                    "success_rate": 1.0,
                    "total_revenue_generated": 10.0,
                },
            }
        ]
        with patch.object(run_agents, "orchestrator") as orch:
            orch.distribute_task.side_effect = [{"ok": True}, Exception("boom"), {"ok": True}, {"ok": True}, {"ok": True}, {"ok": True}]
            orch.get_all_agents_status.return_value = statuses
            run_agents.run_sample_tasks()
            self.assertEqual(orch.distribute_task.call_count, 6)
            orch.get_all_agents_status.assert_called_once()


class TestRunAgentsMain(unittest.TestCase):
    @patch("scripts.run_agents.ErrorContext")
    @patch("scripts.run_agents.argparse.ArgumentParser")
    def test_main_dispatches_start_mode(self, parser_cls, _ctx):
        parser = MagicMock()
        parser.parse_args.return_value = SimpleNamespace(mode="start", agent=None, task=None)
        parser_cls.return_value = parser
        with patch("scripts.run_agents.run_daemon") as run_daemon:
            run_agents.main()
        run_daemon.assert_called_once()

    @patch("scripts.run_agents.ErrorContext")
    @patch("scripts.run_agents.argparse.ArgumentParser")
    def test_main_dispatches_daily_mode(self, parser_cls, _ctx):
        parser = MagicMock()
        parser.parse_args.return_value = SimpleNamespace(mode="daily", agent=None, task=None)
        parser_cls.return_value = parser
        with patch("scripts.run_agents.run_daily_tasks") as run_daily:
            run_agents.main()
        run_daily.assert_called_once()

    @patch("scripts.run_agents.ErrorContext")
    @patch("scripts.run_agents.argparse.ArgumentParser")
    def test_main_dispatches_test_mode(self, parser_cls, _ctx):
        parser = MagicMock()
        parser.parse_args.return_value = SimpleNamespace(mode="test", agent="X", task="identify_prospects")
        parser_cls.return_value = parser
        with patch("scripts.run_agents.run_test") as run_test:
            run_agents.main()
        run_test.assert_called_once_with("X", "identify_prospects")


if __name__ == "__main__":
    unittest.main()
