# DeeJae LeEtta Network - Quick Start Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (optional for testing)
```

### 3. Run the System

#### Option A: Run Everything (Recommended for testing)
```bash
python start.py --mode all
```

This starts:
- API Server on http://localhost:5000
- Webhook Handler on http://localhost:8080

#### Option B: Test Individual Components

**Test AI Agents:**
```bash
PYTHONPATH=. python scripts/run_agents.py --mode test
```

**Start API Server Only:**
```bash
python start.py --mode api
# Or directly:
PYTHONPATH=. python api/main.py
```

**Start Webhook Handler Only:**
```bash
python start.py --mode webhook
# Or directly:
PYTHONPATH=. python api/webhook_handler.py
```

**Run Agents as Daemon:**
```bash
python start.py --mode agents-daemon
```

## 🧪 Testing & Debugging

### Health Checks

```bash
# Check API health
curl http://localhost:5000/api/health

# Check agent status
curl http://localhost:5000/api/agents

# Check metrics
curl http://localhost:5000/api/metrics
```

### Run Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

### View Logs

Logs are stored in the `logs/` directory:
```bash
tail -f logs/*.log
```

### Debug Mode

Set environment variables for more verbose output:
```bash
export LOG_LEVEL=DEBUG
export API_DEBUG=True
```

## 📊 System Components

### 6 AI Agents

1. **MMO Customer Agent** - Acquires gaming customers
2. **E-Commerce Client Finder** - Finds e-commerce clients
3. **Arts Marketing Agent** - Promotes arts/music content
4. **Investor Relations Agent** - Manages investor communications
5. **Trading Strategy Agent** - Executes trading strategies
6. **Campaign Optimizer Agent** - Optimizes marketing campaigns

### API Endpoints

- `GET /api/health` - Health check
- `GET /api/agents` - Agent status
- `GET /api/campaigns` - Campaign metrics
- `GET /api/trading/status` - Trading status
- `GET /api/trading/signals` - Trading signals
- `GET /api/metrics` - Overall metrics

### Webhook Endpoints

- `POST /webhook/github` - GitHub events
- `POST /webhook/trading` - Trading signals
- `POST /webhook/campaign` - Campaign events
- `GET /health` - Health check

## 🔧 Development

### Project Structure

```
.
├── agents/              # 6 AI agents
├── api/                 # REST API & webhooks
├── config/              # Configuration & utilities
├── scripts/             # Orchestration & trading
├── tests/               # Unit tests
├── ml_models/           # ML models (future)
├── contracts/           # Smart contracts (future)
├── dashboard/           # Web dashboard (future)
├── logs/                # Log files
└── data/                # Data storage
```

### Adding a New Agent

1. Create agent in `agents/new_agent.py`
2. Inherit from `BaseAgent`
3. Implement `execute_task()` and `learn_from_result()`
4. Register in `scripts/agent_orchestrator.py`

### Environment Variables

Key variables in `.env`:
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `TRADING_MODE` - Trading mode (paper or live)
- `API_PORT` - API server port (default: 5000)
- `WEBHOOK_PORT` - Webhook handler port (default: 8080)

## 🐛 Common Issues

### Import Errors
Make sure to set PYTHONPATH:
```bash
export PYTHONPATH=$(pwd)
# Or prefix commands with:
PYTHONPATH=. python script.py
```

### Port Already in Use
Change ports in `.env`:
```
API_PORT=5001
WEBHOOK_PORT=8081
```

### Dependencies Not Found
Install all dependencies:
```bash
pip install -r requirements.txt
```

## 📈 Monitoring

### Agent Metrics

Each agent tracks:
- Tasks completed
- Success rate
- Average completion time
- Revenue generated
- Conversions

Access via:
```bash
curl http://localhost:5000/api/agents | python -m json.tool
```

### System Status

```bash
# Get overall network metrics
curl http://localhost:5000/api/metrics | python -m json.tool
```

## 🔒 Security

- Webhook signatures are verified using HMAC
- Trading mode defaults to "paper" for safety
- API keys should be set in `.env` (never commit!)
- Stop loss and position limits protect capital

## 📚 Documentation

- [API Documentation](API_DOCUMENTATION.md)
- [Development Guide](DEVELOPMENT.md)
- [Architecture Overview](README.md)

## 🆘 Need Help?

1. Check logs in `logs/` directory
2. Run with `LOG_LEVEL=DEBUG` for more details
3. Test individual components separately
4. Review documentation files

## ✅ Verification Checklist

Run these commands to verify everything works:

```bash
# 1. Test imports
python -c "from config.settings import *; print('✓ Config OK')"
python -c "from agents.base_agent import *; print('✓ Agents OK')"

# 2. Test orchestrator
python -c "from scripts.agent_orchestrator import orchestrator; print(f'✓ {len(orchestrator.agents)} agents initialized')"

# 3. Run agent tests
PYTHONPATH=. python scripts/run_agents.py --mode test

# 4. Start API and test
python start.py --mode api &
sleep 2
curl http://localhost:5000/api/health
kill %1
```

All tests passing? You're ready to go! 🎉
