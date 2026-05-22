"""
REST API for DeeJae LeEtta Network
Provides endpoints for agents, campaigns, trading strategies, admin dashboard,
and developer debugging tools.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from config.logging_config import setup_logger
from config.error_handlers import ErrorContext, handle_errors
from config.settings import API_HOST, API_PORT, API_DEBUG
from api.admin import admin_bp
from api.dev_tools import dev_bp

logger = setup_logger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard access

# Register admin dashboard and developer tools blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(dev_bp)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "DeeJae LeEtta API",
        "version": "1.0.0"
    }), 200


@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get status of all AI agents"""
    try:
        with ErrorContext("Fetching agent status"):
            # This would return actual agent status from database or service
            agents = [
                {"name": "MMO Customer Agent", "status": "active", "tasks_completed": 0},
                {"name": "E-Commerce Client Finder", "status": "active", "tasks_completed": 0},
                {"name": "Arts Marketing Agent", "status": "active", "tasks_completed": 0},
                {"name": "Investor Relations Agent", "status": "active", "tasks_completed": 0},
                {"name": "Trading Strategy Agent", "status": "active", "tasks_completed": 0},
                {"name": "Campaign Optimizer Agent", "status": "active", "tasks_completed": 0},
            ]
            return jsonify({"agents": agents}), 200
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        return jsonify({"error": "Internal error"}), 500


@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    """Get campaign metrics and performance"""
    try:
        with ErrorContext("Fetching campaign data"):
            # This would return actual campaign data from database
            campaigns = {
                "total_signups": 0,
                "total_conversions": 0,
                "total_revenue": 0.0,
                "top_channels": [],
                "recent_campaigns": []
            }
            return jsonify(campaigns), 200
    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}")
        return jsonify({"error": "Internal error"}), 500


@app.route('/api/trading/status', methods=['GET'])
def get_trading_status():
    """Get trading strategy status and positions"""
    try:
        with ErrorContext("Fetching trading status"):
            # This would return actual trading data
            status = {
                "mode": "paper",
                "portfolio_value": 0.0,
                "positions": [],
                "daily_pnl": 0.0,
                "total_pnl": 0.0
            }
            return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error fetching trading status: {e}")
        return jsonify({"error": "Internal error"}), 500


@app.route('/api/trading/signals', methods=['GET'])
def get_trading_signals():
    """Get recent trading signals"""
    try:
        with ErrorContext("Fetching trading signals"):
            signals = []
            return jsonify({"signals": signals}), 200
    except Exception as e:
        logger.error(f"Error fetching trading signals: {e}")
        return jsonify({"error": "Internal error"}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get overall network metrics"""
    try:
        with ErrorContext("Fetching network metrics"):
            metrics = {
                "total_users": 0,
                "active_agents": 6,
                "d33j_holders": 0,
                "total_campaigns": 0,
                "conversion_rate": 0.0,
                "revenue_30d": 0.0
            }
            return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return jsonify({"error": "Internal error"}), 500


if __name__ == '__main__':
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)
