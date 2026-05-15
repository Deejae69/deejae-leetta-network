# DeeJae LeEtta Network 🌐

> **Decentralized professional networking powered by the Ethereum blockchain and D33J coin.**

---

## What is the DeeJae LeEtta Network?

The DeeJae LeEtta Network is a next-generation professional networking platform built on Ethereum. Unlike traditional platforms that harvest your data and rent you your connections, we give users true ownership over their professional identity — on-chain, verifiable, and censorship-resistant.

## D33J Coin 💰

**D33J** is an ERC-20 utility and governance token on the Ethereum network.

| Property | Details |
|----------|---------|
| Token Name | D33J Coin |
| Standard | ERC-20 |
| Blockchain | Ethereum |
| Use Case | Utility, Governance, Rewards |

### D33J Coin Utility
- 🔐 Access premium network features
- 🗳️ Vote on network governance decisions
- 🤝 Peer-to-peer rewards between members
- 📈 DeFi integrations (staking, liquidity)

## Key Features

- **On-Chain Identity** — Own your professional reputation on Ethereum
- **Community Governance** — D33J holders shape the future of the network
- **DeFi Ready** — Fully composable with the Ethereum DeFi ecosystem
- **MMO Gaming Integration** — D33J coin powers in-game economies with Reown wallet support
- **AI Growth Agent** — Learns from campaign results to improve outreach and acquisition

## Global Improvement Blueprint

To support the upcoming MMO and grow **deejaeleetta.store** + **deejaeleetta.club**, the network will evolve in four connected layers:

1. **Self-Learning AI Agency**
   - Track campaigns (social posts, ads, partnerships, newsletters)
   - Score channels by conversion (wishlist signups, store purchases, club joins)
   - Automatically prioritize highest-performing audience segments

2. **Blockchain Trust + Rewards**
   - Use on-chain reputation for creators, partners, and ambassadors
   - Reward referrals and verified promotion activity with D33J utility incentives
   - Publish transparent campaign and treasury milestones for community trust

3. **Customer Acquisition Engine**
   - MMO-focused funnels: teaser drops, early-access forms, and community quests
   - Cross-promotion of arts/music into MMO worldbuilding campaigns
   - Unified CTA flow into deejaeleetta.store and deejaeleetta.club

4. **Investor Readiness**
   - Maintain a public traction dashboard (users, retention, revenue signals)
   - Define milestone-based funding asks tied to product delivery
   - Keep a concise investor packet with token utility, roadmap, and growth metrics

## Roadmap

- [x] D33J Coin deployed on Ethereum
- [x] DeeJae LeEtta Network launch
- [ ] AI customer-acquisition agent (MVP)
- [ ] Cross-platform promotion pipeline for art, music, and MMO
- [ ] deejaeleetta.store + deejaeleetta.club conversion dashboard
- [ ] Investor traction dashboard + funding packet
- [ ] CoinGecko & CoinMarketCap listing
- [ ] Community governance portal
- [ ] MMO game beta with D33J in-game currency
- [ ] Solar farming & data center expansion (Uyo, Nigeria)
- [ ] DeFi staking launch

## Community

- 🐦 Twitter/X: [@DeeJaeLeEtta](https://twitter.com/DeeJaeLeEtta)
- 💼 LinkedIn: DeeJae LeEtta Network
- 📸 Instagram: @DeeJaeLeEtta

---

## 6-Agent Income Ops (MVP)

This repo now includes a minimal **6-agent runner** focused on:
- Always-on operational workflows (debug/build reports)
- Webhook-based notifications
- Forex strategy signals + risk sizing + paper trading loop

### Quick Start

Run once (good for debugging):

```bash
python -m deejae --config examples/config.example.json --once
```

Run continuously:

```bash
python -m deejae --config examples/config.example.json
```

### Webhooks

Set `webhooks.default_url` in your config to any endpoint that accepts a JSON POST payload (Discord/Slack/custom).

### Agents Included

1. `HeartbeatAgent` – liveness pings (optional webhook)
2. `ForexDataAgent` – loads candle data from CSV into `.deejae/state.json`
3. `ForexStrategyAgent` – generates `long|short|flat` signals (MA crossover or RSI mean reversion)
4. `ForexRiskAgent` – suggests position size from equity + risk %
5. `ForexPaperTradeAgent` – simple entry/exit state machine for paper trading
6. `BuildDebugAgent` – periodic `unittest` self-checks + environment report

*D33J coin is a utility token. This is not financial advice.*

**© 2026 DeeJae LeEtta Network. All rights reserved.**
