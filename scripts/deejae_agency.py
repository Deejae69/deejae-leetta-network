#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import json
import os
import random
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


SEGMENTS = {
    "store_customer",
    "club_member",
    "mmo_player",
    "art_fan",
    "music_fan",
    "investor",
}

OUTCOMES = {
    "sent",
    "opened",
    "clicked",
    "replied",
    "purchased",
    "subscribed",
    "invested",
    "opted_out",
    "bounced",
}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


@dataclasses.dataclass(frozen=True)
class Lead:
    id: str
    name: str
    segment: str
    handle: str | None = None
    email: str | None = None


@dataclasses.dataclass(frozen=True)
class MessageDraft:
    message_id: str
    created_at: str
    lead_id: str
    segment: str
    template_id: str
    channel: str
    subject: str
    body: str


def load_leads_csv(path: Path) -> list[Lead]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = {"id", "name", "segment"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        leads: list[Lead] = []
        for row in reader:
            lead_id = (row.get("id") or "").strip()
            name = (row.get("name") or "").strip()
            segment = (row.get("segment") or "").strip()
            handle = (row.get("handle") or "").strip() or None
            email = (row.get("email") or "").strip() or None

            if not lead_id or not name or not segment:
                continue
            if segment not in SEGMENTS:
                raise ValueError(f"Unknown segment '{segment}' for lead '{lead_id}'")

            leads.append(Lead(id=lead_id, name=name, segment=segment, handle=handle, email=email))
        return leads


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def outcome_is_success(outcome: str) -> bool | None:
    if outcome in {"replied", "purchased", "subscribed", "invested"}:
        return True
    if outcome in {"opted_out", "bounced"}:
        return False
    if outcome in {"sent", "opened", "clicked"}:
        return None
    raise ValueError(f"Unknown outcome '{outcome}'")


def build_template_library(base_urls: dict[str, str]) -> dict[str, dict[str, dict[str, str]]]:
    store = base_urls["store"]
    club = base_urls["club"]
    mmo = base_urls["mmo"]
    press = base_urls["presskit"]

    return {
        "store_customer": {
            "store_drop": {
                "channel": "email",
                "subject": "New drop on DeejaeLeEtta.store",
                "body": (
                    "Hi {name},\n\n"
                    "I just released a new piece and thought you’d like it. "
                    "If you want first access, it’s live here: {cta}\n\n"
                    "If you tell me what styles you collect, I’ll send a short list tailored to you.\n"
                ),
                "cta": store,
            },
            "store_vip": {
                "channel": "dm",
                "subject": "VIP early access",
                "body": (
                    "Hi {name} — I’m offering VIP early access for the next art/music drops. "
                    "If you want in, this is the link: {cta}\n"
                ),
                "cta": store,
            },
        },
        "club_member": {
            "club_join": {
                "channel": "dm",
                "subject": "Join DeejaeLeEtta.club",
                "body": (
                    "Hi {name},\n\n"
                    "I’m building a private community for supporters, collabs, and early releases. "
                    "If you want access, join here: {cta}\n"
                ),
                "cta": club,
            }
        },
        "mmo_player": {
            "mmo_waitlist": {
                "channel": "dm",
                "subject": "MMO early access waitlist",
                "body": (
                    "Hi {name} — I’m opening early access for an upcoming MMO. "
                    "If you want first invites + updates, join the waitlist: {cta}\n"
                ),
                "cta": mmo,
            },
            "mmo_creator_collab": {
                "channel": "email",
                "subject": "Creator collab for upcoming MMO",
                "body": (
                    "Hi {name},\n\n"
                    "I’m looking for creators to help shape and test an upcoming MMO. "
                    "If you’re open to a quick chat, here’s the info: {cta}\n"
                ),
                "cta": mmo,
            },
        },
        "art_fan": {
            "art_portfolio": {
                "channel": "dm",
                "subject": "New art + portfolio",
                "body": (
                    "Hi {name} — sharing my latest work. "
                    "If you want to see the current portfolio and new drops: {cta}\n"
                ),
                "cta": store,
            }
        },
        "music_fan": {
            "music_release": {
                "channel": "dm",
                "subject": "New music release",
                "body": (
                    "Hi {name} — I just dropped new music. "
                    "If you want to listen and join the community: {cta}\n"
                ),
                "cta": club,
            }
        },
        "investor": {
            "investor_pitch": {
                "channel": "email",
                "subject": "DeeJae LeEtta Network — brief investor intro",
                "body": (
                    "Hi {name},\n\n"
                    "I’m building DeeJae LeEtta Network: a decentralized professional network + MMO economy layer. "
                    "I’d like to share a short deck and discuss investment/partnership. "
                    "Press kit / overview: {cta}\n\n"
                    "If you’re the right contact, who should I speak with?\n"
                ),
                "cta": press,
            },
            "investor_followup": {
                "channel": "email",
                "subject": "Quick follow-up — DeeJae LeEtta Network",
                "body": (
                    "Hi {name},\n\n"
                    "Following up in case this got buried. "
                    "If you’re open to a 15-minute intro, here’s the overview: {cta}\n"
                ),
                "cta": press,
            },
        },
    }


def load_stats(events_path: Path) -> dict[tuple[str, str], tuple[int, int]]:
    stats: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])  # [success, failure]
    for event in read_jsonl(events_path):
        segment = str(event.get("segment") or "").strip()
        template_id = str(event.get("template_id") or "").strip()
        outcome = str(event.get("outcome") or "").strip()
        if not segment or not template_id or not outcome:
            continue
        if segment not in SEGMENTS:
            continue
        try:
            success = outcome_is_success(outcome)
        except ValueError:
            continue
        if success is True:
            stats[(segment, template_id)][0] += 1
        elif success is False:
            stats[(segment, template_id)][1] += 1
    return {k: (v[0], v[1]) for k, v in stats.items()}


def choose_template(
    segment: str,
    templates: dict[str, dict[str, str]],
    stats: dict[tuple[str, str], tuple[int, int]],
    rng: random.Random,
) -> str:
    best_template_id: str | None = None
    best_score = -1.0
    for template_id in templates.keys():
        wins, losses = stats.get((segment, template_id), (0, 0))
        alpha = 1 + wins
        beta = 1 + losses
        score = rng.betavariate(alpha, beta)
        if score > best_score:
            best_score = score
            best_template_id = template_id
    if best_template_id is None:
        raise ValueError(f"No templates for segment '{segment}'")
    return best_template_id


def generate_drafts(
    leads: list[Lead],
    library: dict[str, dict[str, dict[str, str]]],
    stats: dict[tuple[str, str], tuple[int, int]],
    rng: random.Random,
) -> list[MessageDraft]:
    drafts: list[MessageDraft] = []
    created_at = utc_now_iso()
    for lead in leads:
        templates = library[lead.segment]
        template_id = choose_template(lead.segment, templates, stats, rng)
        template = templates[template_id]

        cta = template["cta"]
        subject = template["subject"]
        body = template["body"].format(name=lead.name, cta=cta)
        drafts.append(
            MessageDraft(
                message_id=str(uuid.uuid4()),
                created_at=created_at,
                lead_id=lead.id,
                segment=lead.segment,
                template_id=template_id,
                channel=template["channel"],
                subject=subject,
                body=body,
            )
        )
    return drafts


def cmd_generate(args: argparse.Namespace) -> int:
    leads_path = Path(args.leads)
    out_path = Path(args.out)
    events_path = Path(args.events)
    seed = args.seed

    rng = random.Random(seed)
    leads = load_leads_csv(leads_path)
    base_urls = {
        "store": args.store_url,
        "club": args.club_url,
        "mmo": args.mmo_url,
        "presskit": args.presskit_url,
    }
    library = build_template_library(base_urls)
    stats = load_stats(events_path)
    drafts = generate_drafts(leads, library, stats, rng)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for draft in drafts:
            f.write(json.dumps(dataclasses.asdict(draft), ensure_ascii=False) + "\n")

    print(f"Wrote {len(drafts)} drafts to {out_path}", file=sys.stderr)
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    events_path = Path(args.events)
    outcome = args.outcome
    if outcome not in OUTCOMES:
        raise ValueError(f"Invalid outcome '{outcome}' (expected one of {', '.join(sorted(OUTCOMES))})")

    record = {
        "event_id": str(uuid.uuid4()),
        "created_at": utc_now_iso(),
        "lead_id": args.lead_id,
        "segment": args.segment,
        "template_id": args.template_id,
        "outcome": outcome,
        "notes": args.notes or "",
    }
    append_jsonl(events_path, record)
    print(f"Appended event to {events_path}", file=sys.stderr)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    events_path = Path(args.events)
    stats = load_stats(events_path)

    by_segment: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    for (segment, template_id), (wins, losses) in sorted(stats.items()):
        by_segment[segment].append((template_id, wins, losses))

    if not by_segment:
        print("No learning data yet. Record outcomes to improve recommendations.")
        return 0

    for segment in sorted(by_segment.keys()):
        print(f"\n== {segment} ==")
        rows = by_segment[segment]
        for template_id, wins, losses in sorted(rows, key=lambda r: (-(r[1] / max(1, r[1] + r[2])), r[0])):
            total = wins + losses
            rate = (wins / total) if total else 0.0
            print(f"- {template_id}: {wins} success, {losses} fail ({rate:.0%})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deejae-agency",
        description="Local AI-agency helper for DeeJae LeEtta Network outreach.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate outreach message drafts from a leads CSV.")
    gen.add_argument("--leads", required=True, help="Path to leads CSV.")
    gen.add_argument("--out", required=True, help="Output JSONL path for drafts.")
    gen.add_argument("--events", default="out/events.jsonl", help="JSONL outcomes log (used for learning).")
    gen.add_argument("--seed", type=int, default=None, help="Random seed for reproducible selection.")
    gen.add_argument("--store-url", default=os.getenv("DEEJAE_STORE_URL", "https://deejaeleetta.store"))
    gen.add_argument("--club-url", default=os.getenv("DEEJAE_CLUB_URL", "https://deejaeleetta.club"))
    gen.add_argument("--mmo-url", default=os.getenv("DEEJAE_MMO_URL", "https://deejaeleetta.club/mmo"))
    gen.add_argument("--presskit-url", default=os.getenv("DEEJAE_PRESSKIT_URL", "https://deejaeleetta.club/press"))
    gen.set_defaults(func=cmd_generate)

    rec = sub.add_parser("record", help="Record an outcome event for learning.")
    rec.add_argument("--events", default="out/events.jsonl", help="JSONL outcomes log path.")
    rec.add_argument("--lead-id", required=True)
    rec.add_argument("--segment", required=True, choices=sorted(SEGMENTS))
    rec.add_argument("--template-id", required=True)
    rec.add_argument("--outcome", required=True, choices=sorted(OUTCOMES))
    rec.add_argument("--notes", default="")
    rec.set_defaults(func=cmd_record)

    rep = sub.add_parser("report", help="Show learning stats from outcomes log.")
    rep.add_argument("--events", default="out/events.jsonl", help="JSONL outcomes log path.")
    rep.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

