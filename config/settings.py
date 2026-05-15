"""
Configuration settings for DeeJae LeEtta Network
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "ml_models"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, MODELS_DIR]:
    directory.mkdir(exist_ok=True)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Blockchain settings
ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/YOUR-PROJECT-ID")
D33J_TOKEN_ADDRESS = os.getenv("D33J_TOKEN_ADDRESS", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")  # Never commit this!

# AI Agent settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MAX_AGENT_RETRIES = int(os.getenv("MAX_AGENT_RETRIES", "3"))

# Trading/Investment settings
TRADING_MODE = os.getenv("TRADING_MODE", "paper")  # paper or live
RISK_TOLERANCE = float(os.getenv("RISK_TOLERANCE", "0.02"))  # 2% max risk per trade
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.5"))  # 50% of portfolio
STOP_LOSS_PERCENTAGE = float(os.getenv("STOP_LOSS_PERCENTAGE", "0.05"))  # 5%
TAKE_PROFIT_PERCENTAGE = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "0.15"))  # 15%

# Webhook settings
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "5000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"

# Database settings (if needed)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///deejae_network.db")

# External integrations
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Campaign tracking
TRACK_CAMPAIGNS = os.getenv("TRACK_CAMPAIGNS", "True").lower() == "true"
CAMPAIGN_CHECK_INTERVAL = int(os.getenv("CAMPAIGN_CHECK_INTERVAL", "3600"))  # 1 hour
