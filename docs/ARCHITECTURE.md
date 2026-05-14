# DeeJae LeEtta Network — Architecture

This repo tracks the high-level product/technical design for the DeeJae LeEtta Network and includes a small local “AI agency” CLI to help:

- Find and convert customers for `deejaeleetta.store` and `deejaeleetta.club`
- Grow interest for the upcoming MMO (and its community)
- Promote arts and music releases
- Build an investor pipeline (pitch + follow-ups)

## Goal

Build a self-improving growth system that can run daily campaigns, learn from outcomes, and produce measurable results without locking the product into a single vendor.

## System Overview

**Modules**

1. **Lead ingestion**: import leads from CSV/JSON (manual lists, event attendees, partners, waitlists).
2. **Segmentation**: classify each lead into one or more segments:
   - `store_customer`, `club_member`, `mmo_player`, `art_fan`, `music_fan`, `investor`
3. **Outreach planning**: choose channel + message template + call-to-action (CTA).
4. **Message generation**: produce personalized outreach copy (email/DM/short text).
5. **Feedback capture**: record outcomes (opened/replied/purchased/invested).
6. **Self-learning loop**: use feedback to improve planning (which channel/template to use next).

**Data flow**

`Leads → Plan (segment/channel/template) → Messages → Outcomes → Learning stats → Better plan`

## Self-Learning (Practical Definition)

“Self-learning” here means a feedback-driven optimizer:

- Each segment has multiple message templates and channels.
- Outcomes update simple performance stats.
- Future suggestions prioritize historically better performing choices while still exploring alternatives.

The implementation in this repo uses a lightweight multi-armed bandit approach (Beta/Bernoulli) so it can improve without external ML infrastructure.

## Blockchain Integration (Phased)

The core growth loop does not require on-chain activity. Blockchain is used where it adds *verifiability* or *ownership*:

- **On-chain identity**: optional wallet-based identity for MMO + network profiles.
- **Proof-of-relationship**: optional on-chain attestations that a partnership/outreach relationship exists (privacy-preserving and opt-in).
- **Token-gated benefits**: D33J holders unlock community perks and in-game utilities.

Phasing keeps the system shippable even before smart contracts are finalized.

## Privacy and Compliance

- Keep PII (emails, phone numbers) local and minimize what is stored.
- Store outcomes as aggregate events linked to internal lead IDs.
- Make consent and opt-out a first-class field in lead records.

