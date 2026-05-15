# Webhooks (MVP)

The agent runner can POST JSON to a webhook URL for events like:
- runner start
- heartbeats
- forex signals
- build/debug reports
- agent failures (best-effort)

## Configuration

Set `webhooks.default_url` in your JSON config (see `examples/config.example.json`).

Payload shape:

```json
{
  "event": "forex_signal",
  "title": "FX signal EURUSD: long",
  "body": "ts=2026-05-14T02:45:00+00:00",
  "agent_id": "forex_strategy",
  "extra": { "symbol": "EURUSD", "signal": "long" }
}
```

