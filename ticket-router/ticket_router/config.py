"""Tunable settings. Override any value with an env var, e.g. TR_W_HISTORY=0.5."""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _env(name: str, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return type(default)(raw)


@dataclass
class Settings:
    data_dir: Path = DEFAULT_DATA_DIR

    # Scoring weights (sum need not be 1; scores are relative).
    w_history: float = 0.40  # resolved similar tickets before
    w_skill: float = 0.25  # module skill (declared + derived from history)
    w_load: float = 0.15  # spare capacity
    w_seniority: float = 0.20  # seniority vs complexity fit
    w_growth: float = 0.10  # bonus for juniors on safe tickets

    top_k_similar: int = 15  # neighbours retrieved for each ticket
    min_similarity: float = 0.10  # ignore weaker matches
    recency_half_life_days: float = 180.0
    top_n: int = 3  # recommendations returned

    # Hard rule: minimum seniority by priority.
    min_seniority: dict[str, int] = field(default_factory=lambda: {"P1": 3, "P2": 2, "P3": 1, "P4": 1})

    # Pluggable backends.
    embedder: str = "tfidf"  # tfidf | fastembed
    embed_model: str = "BAAI/bge-small-en-v1.5"  # name or local folder (fastembed)
    classifier: str = "keyword"  # keyword | llm
    llm_model_path: str = ""  # path to a GGUF file (classifier=llm)
    llm_threads: int = 0  # 0 = let llama.cpp decide

    @classmethod
    def from_env(cls) -> "Settings":
        s = cls()
        for f in fields(cls):
            if f.name == "min_seniority":
                continue
            key = "TR_" + f.name.upper()
            cur = getattr(s, f.name)
            if f.name == "data_dir":
                setattr(s, f.name, Path(os.environ.get(key, cur)))
            else:
                setattr(s, f.name, _env(key, cur))
        return s
