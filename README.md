# DeeJae LeEtta Network

A decentralized digital network for creators, artists, musicians, builders, and collaborators. This repository now includes the foundational blockchain and network layer for the platform, with room for growth into a creator economy, crypto rewards system, marketplace, and collaboration infrastructure.

## Vision

DeeJae LeEtta Network is a creator-first network where people can:
- connect and collaborate
- showcase art, music, and projects
- trade digital products and services
- earn ecosystem value through creator activity
- access a governance and rewards model powered by crypto
- build a global community rooted in love, growth, and progress

## What is included

This repo now includes:
- Solidity smart contracts for token, verification, and marketplace logic
- Hardhat deployment setup for Ethereum-compatible chains
- a simple frontend launch page and signup flow
- API/service structure for future network integrations
- a roadmap for expanding into community features, DAO governance, and digital economy tools

## Blockchain foundation

### Contracts
- `contracts/D33JToken.sol` — ERC-20 token for network value, governance, and rewards
- `contracts/CreatorRegistry.sol` — creator identity and verification management
- `contracts/CreatorMarketplace.sol` — digital product and service marketplace with crypto transactions

### Deployment and tooling
- `hardhat.config.js` — Hardhat configuration for local and test networks
- `package.json` — project dependencies and scripts
- `scripts/deploy.js` — deployment helper for the network contracts

## Frontend starter

The repo includes a lightweight landing page and signup starter in:
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

This gives you a web presence for the network while the full production app grows.

## Local development

### 1) Install blockchain tooling
```bash
npm install
```

### 2) Start local blockchain
```bash
npx hardhat node
```

### 3) Deploy contracts
In another terminal:
```bash
npx hardhat run scripts/deploy.js --network localhost
```

### 4) Serve the landing page
From the repo root:
```bash
python3 -m http.server 8000 --directory frontend
```

Then open:
```text
http://localhost:8000
```

## Core token concept

The network is designed around ecosystem value creation:
- creators earn rewards for contribution and participation
- users can support creators through transactions and donations
- digital products and services can be traded in the marketplace
- token utility can expand into governance, access, and creator benefits

## Next expansion areas

Planned next steps include:
- creator dashboard and profile system
- on-chain reputation and verification layers
- staking and rewards engine
- DAO voting and governance portal
- digital art/music commerce flow
- wallets and cross-chain support
- collaboration tooling for teams and projects

## Important note

This is a foundation for product development and experimentation. Token economics, governance, and legal compliance should be reviewed carefully before public launch.

## Project status

- [x] Network concept and direction defined
- [x] Blockchain foundation created
- [x] Public repo established
- [x] Startup landing page and signup starter added
- [ ] Full production app and creator dashboard
- [ ] Wallet auth and user onboarding flow
- [ ] DAO governance implementation
- [ ] Advanced marketplace features and monetization engine

---

Built for the DeeJae LeEtta Network vision: building together, united under love, growth, and progress.
