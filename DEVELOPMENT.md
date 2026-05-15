# DeeJae LeEtta Network - Development Guide

## Project Overview

The DeeJae LeEtta Network is a decentralized professional networking platform with 6 autonomous AI agents working continuously to generate income through customer acquisition, marketing, trading, and investor relations.

## Architecture

### Components

1. **AI Agents (6 agents)**
   - MMO Customer Agent
   - E-Commerce Client Finder
   - Arts Marketing Agent
   - Investor Relations Agent
   - Trading Strategy Agent
   - Campaign Optimizer Agent

2. **Infrastructure**
   - API Server (Flask)
   - Webhook Handler
   - Agent Orchestrator
   - Trading Strategy Engine

3. **Configuration**
   - Logging and error handling
   - Environment-based settings
   - Risk management parameters

## Getting Started

### Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Deejae69/deejae-leetta-network.git
cd deejae-leetta-network
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

For development (tests/lint/security tooling):
```bash
pip install -r requirements-dev.txt
```

4. Copy environment configuration:
```bash
cp .env.example .env
```

5. Edit `.env` with your configuration values

### Running the System

#### Run All Agents

```bash
python scripts/run_agents.py --mode start
```

#### Run Daily Tasks

```bash
python scripts/run_agents.py --mode daily
```

#### Run Tests

```bash
python scripts/run_agents.py --mode test
```

#### Run API Server

```bash
python api/main.py
```

#### Run Webhook Handler

```bash
python api/webhook_handler.py
```

## Development Workflow

### Debugging

The system includes comprehensive logging:

- Log files are stored in `logs/`
- Console output with color-coded levels
- Structured logging for debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
```

### Testing

Run tests with pytest:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

### Linting

```bash
flake8 .
black .
mypy .
```

### Security Scanning

```bash
bandit -r .
safety check
```

## CI/CD Pipeline

GitHub Actions workflows are configured for:

- **CI/CD Pipeline** (`.github/workflows/ci-cd.yml`)
  - Linting and type checking
  - Unit tests with coverage
  - Security scanning
  - Build verification

- **Webhook Handler** (`.github/workflows/webhook.yml`)
  - Processes webhook events
  - Triggers agent tasks

## Agent System

### Agent Architecture

All agents inherit from `BaseAgent` and implement:
- `execute_task()` - Execute specific tasks
- `learn_from_result()` - Learn from task outcomes

### Task Distribution

The `AgentOrchestrator` intelligently routes tasks to appropriate agents based on task type.

### Adding a New Agent

1. Create agent class inheriting from `BaseAgent`
2. Implement `execute_task()` and `learn_from_result()`
3. Add to `AgentOrchestrator._initialize_agents()`
4. Update task routing in `_select_agent_for_task()`

## Trading Strategy

### Risk Management

Configure in `.env`:
- `RISK_TOLERANCE` - Maximum risk per trade (default: 0.02 = 2%)
- `MAX_POSITION_SIZE` - Maximum position size (default: 0.1 = 10%)
- `STOP_LOSS_PERCENTAGE` - Stop loss threshold (default: 0.05 = 5%)
- `TAKE_PROFIT_PERCENTAGE` - Take profit threshold (default: 0.15 = 15%)

### Trading Modes

- `paper` - Paper trading (simulation)
- `live` - Live trading (requires API keys)

### Strategies

- **Momentum Strategy** - Trades based on price momentum
- **Mean Reversion Strategy** - Trades based on deviation from mean

## Webhooks

### Supported Webhooks

1. **GitHub Webhooks** (`/webhook/github`)
   - Push events
   - Pull request events
   - Issue events
   - Workflow events

2. **Trading Webhooks** (`/webhook/trading`)
   - Buy/sell signals
   - Market updates

3. **Campaign Webhooks** (`/webhook/campaign`)
   - Signups
   - Purchases
   - Conversions

### Webhook Security

Set `WEBHOOK_SECRET` in `.env` for signature verification.

## API Endpoints

### Health Check
```
GET /api/health
```

### Get Agents Status
```
GET /api/agents
```

### Get Campaign Metrics
```
GET /api/campaigns
```

### Get Trading Status
```
GET /api/trading/status
```

### Get Network Metrics
```
GET /api/metrics
```

## Monitoring and Metrics

### Agent Metrics

Each agent tracks:
- Tasks completed
- Success rate
- Average completion time
- Revenue generated
- Conversions

### Network Metrics

Overall network tracks:
- Total agents
- Total revenue
- Total conversions
- Average success rate

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check all dependencies are installed

2. **Webhook Signature Verification Fails**
   - Verify `WEBHOOK_SECRET` matches in both systems
   - Check payload encoding

3. **Trading Engine Not Executing**
   - Verify `TRADING_MODE` is set correctly
   - Check API keys if in live mode

### Debug Mode

Enable verbose logging:
```bash
export LOG_LEVEL=DEBUG
python scripts/run_agents.py --mode test
```

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests and linting
4. Submit pull request

## License

© 2026 DeeJae LeEtta Network. All rights reserved.
