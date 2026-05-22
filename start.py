#!/usr/bin/env python3
"""
Quick start script for DeeJae LeEtta Network
Runs all components and provides a simple CLI
"""

import sys
import os
import subprocess
import time
import signal

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.logging_config import setup_logger
from config.settings import API_PORT, WEBHOOK_PORT

logger = setup_logger(__name__)

processes = []


def start_api_server():
    """Start the REST API server"""
    logger.info("Starting API server...")
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.Popen(
        [sys.executable, 'api/main.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append(('API Server', proc))
    logger.info(f"API server started on http://localhost:{API_PORT}")
    return proc


def start_webhook_handler():
    """Start the webhook handler"""
    logger.info("Starting webhook handler...")
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.Popen(
        [sys.executable, 'api/webhook_handler.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append(('Webhook Handler', proc))
    logger.info(f"Webhook handler started on http://localhost:{WEBHOOK_PORT}")
    return proc


def run_agents_test():
    """Run agents in test mode"""
    logger.info("Running agents in test mode...")
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(
        [sys.executable, 'scripts/run_agents.py', '--mode', 'test'],
        env=env
    )


def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    logger.info("Shutting down all processes...")
    for name, proc in processes:
        logger.info(f"Stopping {name}...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="DeeJae LeEtta Network Quick Start")
    parser.add_argument(
        '--mode',
        choices=['all', 'api', 'webhook', 'agents-test', 'agents-daemon'],
        default='all',
        help='What to run'
    )

    args = parser.parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        if args.mode in ['all', 'api']:
            start_api_server()
            time.sleep(1)

        if args.mode in ['all', 'webhook']:
            start_webhook_handler()
            time.sleep(1)

        if args.mode == 'agents-test':
            run_agents_test()
            return

        if args.mode == 'agents-daemon':
            logger.info("Starting agents in daemon mode...")
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
            proc = subprocess.Popen(
                [sys.executable, 'scripts/run_agents.py', '--mode', 'start'],
                env=env
            )
            processes.append(('Agent Daemon', proc))

        if args.mode == 'all':
            logger.info("="*60)
            logger.info("DeeJae LeEtta Network is running!")
            logger.info("="*60)
            logger.info(f"API Server:       http://localhost:{API_PORT}/api/health")
            logger.info(f"Webhook Handler:  http://localhost:{WEBHOOK_PORT}/health")
            logger.info("="*60)
            logger.info("Press Ctrl+C to stop")

            # Keep running
            while True:
                time.sleep(1)
                # Check if any process died
                for name, proc in processes:
                    if proc.poll() is not None:
                        logger.error(f"{name} has stopped unexpectedly!")
                        cleanup()

    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        logger.error(f"Error: {e}")
        cleanup()


if __name__ == '__main__':
    main()
