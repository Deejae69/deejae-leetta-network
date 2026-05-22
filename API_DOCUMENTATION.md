# API Documentation

## DeeJae LeEtta Network API

Base URL: `http://localhost:5000`

## Authentication

Currently, the API doesn't require authentication for development. Production deployments should implement proper authentication.

## Endpoints

### Health Check

Check API health status.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "DeeJae LeEtta API",
  "version": "1.0.0"
}
```

### Get All Agents

Get status and metrics for all AI agents.

**Endpoint:** `GET /api/agents`

**Response:**
```json
{
  "agents": [
    {
      "name": "MMO Customer Agent",
      "status": "active",
      "tasks_completed": 42
    }
  ]
}
```

### Get Campaign Metrics

Get campaign performance metrics.

**Endpoint:** `GET /api/campaigns`

**Response:**
```json
{
  "total_signups": 1234,
  "total_conversions": 567,
  "total_revenue": 12345.67,
  "top_channels": ["instagram", "twitter"],
  "recent_campaigns": []
}
```

### Get Trading Status

Get current trading status and positions.

**Endpoint:** `GET /api/trading/status`

**Response:**
```json
{
  "mode": "paper",
  "portfolio_value": 10000.0,
  "positions": [],
  "daily_pnl": 123.45,
  "total_pnl": 567.89
}
```

### Get Trading Signals

Get recent trading signals.

**Endpoint:** `GET /api/trading/signals`

**Response:**
```json
{
  "signals": []
}
```

### Get Network Metrics

Get overall network performance metrics.

**Endpoint:** `GET /api/metrics`

**Response:**
```json
{
  "total_users": 1000,
  "active_agents": 6,
  "d33j_holders": 500,
  "total_campaigns": 50,
  "conversion_rate": 0.05,
  "revenue_30d": 5000.0
}
```

## Webhooks

### GitHub Webhook

Receive GitHub events.

**Endpoint:** `POST /webhook/github`

**Headers:**
- `X-Hub-Signature-256`: SHA256 HMAC signature
- `X-GitHub-Event`: Event type

**Supported Events:**
- `push`
- `pull_request`
- `issues`
- `workflow_run`

### Trading Webhook

Receive trading signals.

**Endpoint:** `POST /webhook/trading`

**Body:**
```json
{
  "signal_type": "buy",
  "symbol": "D33J",
  "price": 1.50
}
```

### Campaign Webhook

Track campaign events.

**Endpoint:** `POST /webhook/campaign`

**Body:**
```json
{
  "event_type": "purchase",
  "amount": 50.0,
  "source": "instagram"
}
```

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message description"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request
- `403` - Forbidden
- `500` - Internal Server Error
