"""
Webhook handler for DeeJae LeEtta Network
Handles incoming webhooks from GitHub, external services, and triggers agent tasks
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import json
from typing import Dict, Any
from config.logging_config import setup_logger
from config.error_handlers import ErrorContext, WebhookError, handle_errors
from config.settings import WEBHOOK_SECRET, WEBHOOK_PORT

logger = setup_logger(__name__)

app = Flask(__name__)


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verify webhook signature for security

    Args:
        payload_body: Raw request body
        signature_header: Signature from request header

    Returns:
        True if signature is valid, False otherwise
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not configured, skipping signature verification")
        return True

    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "DeeJae LeEtta Webhook Handler"}), 200


@app.route('/webhook/github', methods=['POST'])
@handle_errors(error_type=Exception, default_return=(jsonify({"error": "Internal error"}), 500))
def handle_github_webhook():
    """
    Handle GitHub webhooks (push, PR, issues, etc.)
    """
    with ErrorContext("GitHub webhook processing"):
        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not verify_signature(request.data, signature):
            logger.error("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 403

        event_type = request.headers.get('X-GitHub-Event', 'unknown')
        payload = request.json

        logger.info(f"Received GitHub webhook: {event_type}")

        # Process different event types
        if event_type == 'push':
            handle_push_event(payload)
        elif event_type == 'pull_request':
            handle_pr_event(payload)
        elif event_type == 'issues':
            handle_issue_event(payload)
        elif event_type == 'workflow_run':
            handle_workflow_event(payload)
        else:
            logger.info(f"Unhandled GitHub event type: {event_type}")

        return jsonify({"status": "processed", "event": event_type}), 200


@app.route('/webhook/trading', methods=['POST'])
@handle_errors(error_type=Exception, default_return=(jsonify({"error": "Internal error"}), 500))
def handle_trading_webhook():
    """
    Handle trading signals and market data webhooks
    """
    with ErrorContext("Trading webhook processing"):
        payload = request.json

        if not payload:
            return jsonify({"error": "Invalid payload"}), 400

        logger.info(f"Received trading webhook: {payload.get('signal_type', 'unknown')}")

        # Process trading signal
        signal_type = payload.get('signal_type')
        if signal_type == 'buy':
            handle_buy_signal(payload)
        elif signal_type == 'sell':
            handle_sell_signal(payload)
        elif signal_type == 'market_update':
            handle_market_update(payload)
        else:
            logger.warning(f"Unknown trading signal type: {signal_type}")

        return jsonify({"status": "processed"}), 200


@app.route('/webhook/campaign', methods=['POST'])
@handle_errors(error_type=Exception, default_return=(jsonify({"error": "Internal error"}), 500))
def handle_campaign_webhook():
    """
    Handle campaign events (conversions, signups, purchases)
    """
    with ErrorContext("Campaign webhook processing"):
        payload = request.json

        if not payload:
            return jsonify({"error": "Invalid payload"}), 400

        logger.info(f"Received campaign webhook: {payload.get('event_type', 'unknown')}")

        # Track campaign event
        event_type = payload.get('event_type')
        if event_type == 'signup':
            track_signup(payload)
        elif event_type == 'purchase':
            track_purchase(payload)
        elif event_type == 'conversion':
            track_conversion(payload)
        else:
            logger.warning(f"Unknown campaign event type: {event_type}")

        return jsonify({"status": "tracked"}), 200


def handle_push_event(payload: Dict[str, Any]):
    """Process GitHub push events"""
    repo = payload.get('repository', {}).get('full_name', 'unknown')
    ref = payload.get('ref', 'unknown')
    commits = payload.get('commits', [])

    logger.info(f"Push to {repo} on {ref} with {len(commits)} commits")

    # Trigger CI/CD or agent tasks based on push
    # This could trigger code analysis, tests, or deployment


def handle_pr_event(payload: Dict[str, Any]):
    """Process GitHub pull request events"""
    action = payload.get('action', 'unknown')
    pr_number = payload.get('pull_request', {}).get('number', 'unknown')

    logger.info(f"PR #{pr_number} {action}")

    # Could trigger PR review, testing, or agent analysis


def handle_issue_event(payload: Dict[str, Any]):
    """Process GitHub issue events"""
    action = payload.get('action', 'unknown')
    issue_number = payload.get('issue', {}).get('number', 'unknown')

    logger.info(f"Issue #{issue_number} {action}")

    # Could trigger agent to analyze and respond to issues


def handle_workflow_event(payload: Dict[str, Any]):
    """Process GitHub workflow run events"""
    workflow_name = payload.get('workflow', {}).get('name', 'unknown')
    conclusion = payload.get('workflow_run', {}).get('conclusion', 'unknown')

    logger.info(f"Workflow '{workflow_name}' concluded with: {conclusion}")

    # Could trigger notifications or follow-up actions


def handle_buy_signal(payload: Dict[str, Any]):
    """Process buy trading signals"""
    symbol = payload.get('symbol', 'unknown')
    price = payload.get('price', 0)

    logger.info(f"Buy signal for {symbol} at {price}")

    # Would integrate with trading strategy execution


def handle_sell_signal(payload: Dict[str, Any]):
    """Process sell trading signals"""
    symbol = payload.get('symbol', 'unknown')
    price = payload.get('price', 0)

    logger.info(f"Sell signal for {symbol} at {price}")

    # Would integrate with trading strategy execution


def handle_market_update(payload: Dict[str, Any]):
    """Process market data updates"""
    logger.info("Processing market update")

    # Would update market data and trigger analysis


def track_signup(payload: Dict[str, Any]):
    """Track campaign signups"""
    source = payload.get('source', 'unknown')
    logger.info(f"New signup from {source}")

    # Would update campaign metrics and ML models


def track_purchase(payload: Dict[str, Any]):
    """Track campaign purchases"""
    amount = payload.get('amount', 0)
    source = payload.get('source', 'unknown')

    logger.info(f"New purchase: ${amount} from {source}")

    # Would update revenue tracking and agent learning


def track_conversion(payload: Dict[str, Any]):
    """Track campaign conversions"""
    conversion_type = payload.get('type', 'unknown')
    source = payload.get('source', 'unknown')

    logger.info(f"Conversion: {conversion_type} from {source}")

    # Would update conversion metrics and optimize campaigns


if __name__ == '__main__':
    logger.info(f"Starting webhook handler on port {WEBHOOK_PORT}")
    app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False)
