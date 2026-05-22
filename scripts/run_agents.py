"""
Main entry point for running DeeJae LeEtta Network agents
"""

import sys
import argparse
from config.logging_config import setup_logger
from config.error_handlers import ErrorContext
from scripts.agent_orchestrator import orchestrator

logger = setup_logger(__name__)


def main():
    """Main function to run agents"""
    parser = argparse.ArgumentParser(description="DeeJae LeEtta Network Agent System")
    parser.add_argument(
        "--mode",
        choices=["start", "test", "daily"],
        default="test",
        help="Mode to run: start (daemon), test (single run), daily (daily tasks)"
    )
    parser.add_argument(
        "--agent",
        help="Specific agent to test (if mode=test)"
    )
    parser.add_argument(
        "--task",
        help="Specific task type to run (if mode=test)"
    )

    args = parser.parse_args()

    logger.info(f"Starting DeeJae LeEtta Network in {args.mode} mode")

    with ErrorContext("Agent system execution"):
        if args.mode == "start":
            run_daemon()
        elif args.mode == "daily":
            run_daily_tasks()
        elif args.mode == "test":
            run_test(args.agent, args.task)


def run_daemon():
    """Run agents as a daemon"""
    logger.info("Starting agent orchestrator daemon")

    try:
        orchestrator.start()
        logger.info("All agents started successfully")
        logger.info("Press Ctrl+C to stop")

        # Keep running
        import time
        while True:
            time.sleep(60)
            # Could add periodic health checks here

    except KeyboardInterrupt:
        logger.info("Shutting down agent orchestrator")
        orchestrator.stop()


def run_daily_tasks():
    """Run daily automated tasks"""
    logger.info("Running daily automated tasks")

    results = orchestrator.run_daily_tasks()

    logger.info(f"Daily tasks completed. Results:")
    for result in results:
        logger.info(f"  - {result['agent']}: {result['task']} - {result.get('result', result.get('error'))}")

    # Print network metrics
    metrics = orchestrator.get_network_metrics()
    logger.info(f"\nNetwork Metrics:")
    logger.info(f"  Total Revenue: ${metrics['total_revenue_generated']:.2f}")
    logger.info(f"  Total Conversions: {metrics['total_conversions']}")
    logger.info(f"  Tasks Completed: {metrics['total_tasks_completed']}")
    logger.info(f"  Average Success Rate: {metrics['avg_success_rate']:.2%}")


def run_test(agent_name: str = None, task_type: str = None):
    """Run a test task"""
    logger.info("Running test mode")

    if not task_type:
        logger.info("No task specified, running sample tasks for all agents")
        run_sample_tasks()
        return

    if agent_name:
        logger.info(f"Testing agent: {agent_name}")
        agent = orchestrator.get_agent(agent_name)
        if not agent:
            logger.error(f"Agent '{agent_name}' not found")
            return

    # Run specific task
    test_data = get_test_data(task_type)
    result = orchestrator.distribute_task(task_type, test_data)

    logger.info(f"Test result: {result}")


def run_sample_tasks():
    """Run sample tasks for all agents"""
    sample_tasks = [
        ("identify_prospects", {"audience": "gamers"}),
        ("find_clients", {"category": "art", "source": "organic"}),
        ("create_content", {"type": "music", "theme": "blockchain"}),
        ("identify_investors", {"stage": "seed", "focus": "blockchain"}),
        ("analyze_market", {"market_data": {"symbol": "D33J", "price": 1.5, "historical_prices": [1.3, 1.4, 1.45, 1.5]}}),
        ("analyze_campaign", {
            "campaign_id": "test_1",
            "channel": "instagram",
            "metrics": {
                "impressions": 10000,
                "clicks": 500,
                "conversions": 50,
                "cost": 500,
                "avg_order_value": 50
            }
        })
    ]

    logger.info(f"Running {len(sample_tasks)} sample tasks")

    for task_type, data in sample_tasks:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing task: {task_type}")
        logger.info(f"{'='*60}")

        try:
            result = orchestrator.distribute_task(task_type, data)
            logger.info(f"Result: {result}")
        except Exception as e:
            logger.error(f"Error running task {task_type}: {e}")

    # Print agent status
    logger.info(f"\n{'='*60}")
    logger.info("Agent Status Summary")
    logger.info(f"{'='*60}")

    for agent_status in orchestrator.get_all_agents_status():
        logger.info(f"\n{agent_status['name']}:")
        logger.info(f"  Status: {'Active' if agent_status['is_active'] else 'Inactive'}")
        logger.info(f"  Tasks Completed: {agent_status['metrics']['tasks_completed']}")
        logger.info(f"  Success Rate: {agent_status['metrics']['success_rate']}")
        logger.info(f"  Revenue Generated: {agent_status['metrics']['total_revenue_generated']}")


def get_test_data(task_type: str) -> dict:
    """Get test data for different task types"""
    test_data_map = {
        "identify_prospects": {"audience": "gamers"},
        "find_clients": {"category": "art"},
        "create_content": {"type": "music", "theme": "test"},
        "analyze_market": {"market_data": {"symbol": "TEST", "price": 100}},
        "analyze_campaign": {
            "campaign_id": "test",
            "metrics": {"impressions": 1000, "clicks": 50, "conversions": 5, "cost": 100}
        }
    }

    return test_data_map.get(task_type, {})


if __name__ == "__main__":
    main()
