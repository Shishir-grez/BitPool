# Core architecture: what we build around (v0)

## Centre of gravity: the Team Experience Graph
A typed, temporal knowledge graph of **what this team has solved, how, and who solved it**, with hybrid text search.
**The graph is the product. The LLM is a replaceable reasoner on top of it.**

Why this is the centre:
- The LLM lacks SAP-specific and team-specific knowledge. All of it has to come from our data.
- Assignment quality depends on evidence quality. The decision step can only be as good as the evidence it is given.
- It survives model swaps: local Phi-4-mini today, a cloud model for the POC, something better next year.
- The same graph powers several features: assignment, resolution hints, duplicate detection, skill-gap view.
- It is measurable on its own, before any LLM decision exists.

```
  Sources ─► Ingest & Distil ─► TEAM EXPERIENCE GRAPH ─► Fact API ─► Context Assembler ─► LLM Decision ─► Guardrails ─► Output
 (tickets,    (parse ticket      (nodes+edges+cards,     (typed,       (L0 core / L1 push /   (model-agnostic  (validate,      (top-3 +
  roster,      tree, entities,    temporal, hybrid        as_of)        L2 pull, token budget) adapter)         abstain)        evidence)
  KB)          cards, edges)      text+vector index)                                                                          │
                     ▲                                                                                                       │
                     └──────────── Feedback (accept/override) ◄── Eval harness (time-travel backtest, golden set) ◄──────────┘
```

## Components
| # | Component | Responsibility | Borrowed from |
|---|---|---|---|
| 1 | Ingest & Distil | Parse each ticket into a section tree (symptom, error, steps, root cause, fix, metadata); extract SAP entities against a controlled vocabulary; write cards; build edges | LinkedIn intra-issue tree |
| 2 | Team Experience Graph | Nodes: Ticket(+sections), Person, Team, SubArea, SapEntity, Pattern, Customer/System, Project. Edges with validity periods and provenance. Hybrid index on sections and cards | LinkedIn inter-issue graph + Zep temporal edges |
| 3 | Fact API | `similar_tickets`, `experts_for`, `person`, `availability`, `ticket`, `docs_for`, all with `as_of` | — |
| 4 | Context Assembler | L0/L1/L2 tiers, token budget, priority truncation | MemGPT/Letta tiers |
| 5 | Decision Engine | Listwise choice over 3–5 candidates, JSON schema output, retrieval plan for L2 | — |
| 6 | Guardrails | IDs and citations validated, rules enforced in code, abstain gate, prompt-injection isolation | — |
| 7 | Eval harness | Time-travel backtest, golden set, retrieval metrics (MRR, Recall@K), decision metrics, ablations | LinkedIn golden-set evaluation |
| 8 | Feedback loop | Overrides become new edges, eval cases and profile corrections | — |

## Build order (each step is useful and measurable on its own)
1. **Graph + ingest + Fact API, no LLM decision.** Metric: the actual resolver is in the `experts_for` top-5 (as of the ticket date) and similar-ticket MRR on a golden set.
2. **Distillation:** section trees and cards via the LLM. Metric: lift over step 1.
3. **Context assembler + LLM decision + guardrails.** Metric: top-1/top-3 vs graph-only ranking and baselines.
4. **UI + feedback.**
5. **Resolution hints** (the LinkedIn use case) from the same graph.

Rule: if the graph-only ranking (step 1) is already close to the LLM decision (step 3), the LLM's value is in
explanation and edge cases, and that decides how much model we need.

## Store
PostgreSQL + pgvector + BM25 full-text, with the graph modelled as typed node/edge tables carrying validity
periods (see `retrieval-layer.md`). Neo4j is the alternative if traversal depth grows.
