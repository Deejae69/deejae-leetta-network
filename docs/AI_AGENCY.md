# AI Agency CLI (Local)

This repo includes a small, dependency-free CLI that helps you run outreach campaigns and learn from results.

It is designed to work without API keys or external services; you can later plug in an LLM to rewrite/expand message text if desired.

## What it does

- Imports leads from a CSV
- Generates outreach drafts per segment (store/club/MMO/arts/music/investors)
- Records outcomes and adapts future recommendations (self-learning)

## Inputs

**Leads CSV columns (minimum)**

- `id` (string)
- `name` (string)
- `handle` (optional; social username)
- `email` (optional)
- `segment` (one of: `store_customer`, `club_member`, `mmo_player`, `art_fan`, `music_fan`, `investor`)

## Outputs

- A JSONL file of message drafts (one per lead)
- A JSONL event log of outcomes (for learning)

## Usage

- Generate drafts: `python3 scripts/deejae_agency.py generate --leads examples/leads.csv --out out/messages.jsonl`
- Record outcomes: `python3 scripts/deejae_agency.py record --events out/events.jsonl --lead-id L001 --template investor_pitch --outcome replied`
- Show stats: `python3 scripts/deejae_agency.py report --events out/events.jsonl`

