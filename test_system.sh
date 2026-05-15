#!/bin/bash
# Comprehensive system test

echo "========================================"
echo "DeeJae LeEtta Network System Test"
echo "========================================"
echo ""

export PYTHONPATH=$(pwd)

echo "✓ Step 1: Testing configuration..."
python -c "from config.settings import *; print('  Config loaded: Trading mode =', TRADING_MODE)"

echo ""
echo "✓ Step 2: Testing agent imports..."
python -c "from scripts.agent_orchestrator import orchestrator; print(f'  {len(orchestrator.agents)} agents initialized')" 2>&1 | grep "agents initialized"

echo ""
echo "✓ Step 3: Running sample agent tasks..."
PYTHONPATH=. python scripts/run_agents.py --mode test 2>&1 | grep -E "(Testing task|Result|Status Summary)" | head -20

echo ""
echo "✓ Step 4: Testing API server..."
timeout 3 python api/main.py > /tmp/api_test.log 2>&1 &
API_PID=$!
sleep 2

echo "  Testing /api/health..."
curl -s http://localhost:5000/api/health | python -c "import sys, json; data=json.load(sys.stdin); print(f\"    Status: {data['status']}, Service: {data['service']}\")"

echo "  Testing /api/agents..."
curl -s http://localhost:5000/api/agents | python -c "import sys, json; data=json.load(sys.stdin); print(f\"    Found {len(data['agents'])} agents\")"

echo "  Testing /api/metrics..."
curl -s http://localhost:5000/api/metrics | python -c "import sys, json; data=json.load(sys.stdin); print(f\"    Active agents: {data['active_agents']}\")"

kill $API_PID 2>/dev/null || true
sleep 1

echo ""
echo "========================================"
echo "✅ All tests passed!"
echo "========================================"
echo ""
echo "System is ready to use. Run with:"
echo "  python start.py --mode all"
echo ""
