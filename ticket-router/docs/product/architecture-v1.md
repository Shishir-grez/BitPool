# Architecture v1 — 2026 rethink

Supersedes the pipeline in `architecture-core.md`. That document's "Team Experience Graph" and build order still hold.
Evidence for each choice: `../research/sota-2025-2026.md`.

## One line
**Bounded agentic retrieval over a hybrid-indexed, temporal Team Experience Graph. A calibrated LLM judge decides and
abstains when unsure. Every decision is logged as training data.**

## Layers
```
OFFLINE (incremental)
 Sources ─► Normalise & enrich (LLM as feature augmenter) ─► Records ─► Indexes ─► Team Experience Graph
            · section tree (LinkedIn)                        tickets     · BM25 (primary)
            · contextual card (Anthropic CR)                 people      · dense (BGE-M3 / Qwen3-Emb class)
            · SAP entities (controlled vocab)                entities    · entity exact index
            · keep raw + normalised views                    patterns    · typed temporal edges

ONLINE (per ticket)
 1 Understand   ticket → sections + entities + normalised card (same style as stored cards)
 2 Discover     fixed hybrid pass: BM25 + dense + entity ─► RRF ─► rerank ─► top tickets
 3 Expand       graph 1–2 hops ─► candidate people + evidence (code-computed stats, as_of)
 4 Constrain    availability / capacity / seniority rules (code)
 5 Refine       ≤2 agent rounds via typed tools (MCP) if evidence is thin or conflicting; token and round budget
 6 Decide       listwise judge over 3–5 candidates, run on 2 shuffled orders; JSON schema
 7 Calibrate    agreement + score ─► conformal threshold ─► answer | abstain
 8 Explain      reasons cite ticket IDs; validator checks every cited ID
LEARN
 accept/override logs ─► (a) exemplar store for few-shot ─► (b) LoRA SFT of a small reasoning LLM decider (LIA-style)
```

## Context = progressive disclosure (replaces fixed L0/L1/L2 stuffing)
- **L0, stable prefix (cacheable):** rules, output schema, module map, roster digest, tool list (names and one-liners only).
- **L1, pushed per ticket:** the results of steps 2–4, as compact cards with IDs.
- **L2, pulled:** the model asks by identifier (`ticket(id)`, `person_history(id)`, `module_playbook(FI-AP)`).
  Module playbooks are packaged **like Agent Skills**: a name and description are always visible; the body loads on demand.

## Baseline ladder (evaluation, same time-split test set)
| ID | System | Purpose |
|---|---|---|
| B0 | Most-frequent resolver per module | floor |
| B1 | BM25 kNN vote over similar tickets | lexical strength |
| B2 | **LinkedIn-2024 replica:** section tree, dense section-sum scoring, LLM picks | "brute force" baseline |
| B3 | B2 + BM25 hybrid + contextual cards + rerank, no agent | 2025 retrieval upgrades |
| V1 | Full v1 (graph expand, rules, bounded agent, calibrated judge) | target |
| V2 | V1 + fine-tuned decider | learning upgrade |

Metrics:
- retrieval: MRR, Recall@k;
- decision: Hit@1/@3, coverage at the target error (from conformal calibration), ECE;
- cost: tokens and latency per ticket;
- fairness: load spread.

Each rung must beat the one below it, or it gets removed.

## What we deliberately do not do
- LLM-built knowledge graphs (GraphRAG, LightRAG): cost, and worse results on simple lookups.
- Unbounded agents: past 2 rounds, gains are small and the token cost multiplies.
- Long-context stuffing of history: context rot and cost. Only the stable prefix is cached.
- Free-form Cypher or SQL from the model.
