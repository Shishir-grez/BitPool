from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import HistoricTicket, Member, NewTicket


def _read(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def parse_skills(raw: str) -> dict[str, int]:
    """'FI:4;CO:3' -> {'FI': 4, 'CO': 3}"""
    out: dict[str, int] = {}
    for part in filter(None, (p.strip() for p in raw.split(";"))):
        mod, _, lvl = part.partition(":")
        out[mod.strip().upper()] = int(lvl or 1)
    return out


def load_team(path: Path) -> list[Member]:
    return [
        Member(
            id=r["id"],
            name=r["name"],
            seniority=int(r["seniority"]),
            status=r.get("status", "active").lower() or "active",
            open_tickets=int(r.get("open_tickets") or 0),
            max_open=int(r.get("max_open") or 8),
            skills=parse_skills(r.get("skills", "")),
        )
        for r in _read(path)
    ]


def load_history(path: Path) -> list[HistoricTicket]:
    return [
        HistoricTicket(
            ticket_id=r["ticket_id"],
            created=date.fromisoformat(r["created"]),
            title=r["title"],
            description=r.get("description", ""),
            module=r["module"].upper(),
            type=r.get("type", "incident"),
            complexity=r.get("complexity", "medium"),
            priority=r.get("priority", "P3"),
            resolver_id=r["resolver_id"],
            hours_to_resolve=float(r.get("hours_to_resolve") or 0),
            resolution_notes=r.get("resolution_notes", ""),
        )
        for r in _read(path)
    ]


def load_new_tickets(path: Path) -> list[NewTicket]:
    return [
        NewTicket(r["ticket_id"], r["title"], r.get("description", ""), r.get("priority") or "P3")
        for r in _read(path)
    ]
