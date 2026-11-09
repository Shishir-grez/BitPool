from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

MODULES = ("FI", "CO", "MM", "SD", "PP", "BASIS", "ABAP")
TYPES = ("incident", "service_request", "change")
COMPLEXITIES = ("low", "medium", "high")
PRIORITIES = ("P1", "P2", "P3", "P4")
SENIORITY_LABELS = {1: "junior", 2: "mid", 3: "senior", 4: "lead"}


@dataclass
class Member:
    id: str
    name: str
    seniority: int
    status: str  # active | leave | left
    open_tickets: int
    max_open: int
    skills: dict[str, int] = field(default_factory=dict)  # module -> level 1..4

    @property
    def available(self) -> bool:
        return self.status == "active"


@dataclass
class HistoricTicket:
    ticket_id: str
    created: date
    title: str
    description: str
    module: str
    type: str
    complexity: str
    priority: str
    resolver_id: str
    hours_to_resolve: float
    resolution_notes: str

    @property
    def text(self) -> str:
        return f"{self.title}. {self.description}"


@dataclass
class NewTicket:
    ticket_id: str
    title: str
    description: str
    priority: str = "P3"

    @property
    def text(self) -> str:
        return f"{self.title}. {self.description}"


@dataclass
class Classification:
    module: str
    type: str
    complexity: str
    source: str  # which classifier produced it
    confidence: float = 0.0


@dataclass
class Similar:
    ticket: HistoricTicket
    score: float


@dataclass
class Candidate:
    member: Member
    score: float
    features: dict[str, float]
    evidence: list[Similar]
    rationale: str = ""


@dataclass
class Recommendation:
    ticket: NewTicket
    classification: Classification
    candidates: list[Candidate]
    excluded: dict[str, str]  # member id -> reason
    similar: list[Similar]
