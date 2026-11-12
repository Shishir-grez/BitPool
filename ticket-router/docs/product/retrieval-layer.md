# Retrieval layer for facts — first-principles design (v0)

Supersedes §1 (Storage) of `intelligence-layer.md`. Platform constraints are deliberately ignored here.

## 1. Start from the questions, not the technology
Every retrieval need of the router falls into one of these:

| # | Question the system must answer | Nature of the answer | What can answer it |
|---|---|---|---|
| Q1 | Which past tickets look like this one? | fuzzy text similarity | vector + BM25 search |
| Q2 | What fixed this error / T-code before? | unstructured text | text retrieval (RAG) |
| Q3 | Who has solved tickets touching ME21N / IDoc ORDERS05 / pricing? | 2-hop relation + aggregation (person→ticket→entity) | graph / joins |
| Q4 | Who worked on customer X / project Y / system landscape Z? | multi-hop relation | graph traversal |
| Q5 | Is E03 available, what's their load, seniority, team? | exact current state | relational lookup |
| Q6 | How many FI-AP tickets did E03 close in 6 months, median time, reopen rate? | exact aggregation | SQL |
| Q7 | What was true *on date D*? (team, skills, availability) | time-scoped fact | temporal validity on facts |

Consequences:
- **Pure vector RAG fails Q3–Q7.** It returns similar text. It cannot count, give current state, follow relations reliably, or scope to a date.
- **LLMs must not compute Q5–Q6.** The answers are numbers and states, so code computes them and the LLM reads them.
- **Q7 is non-negotiable.** Without "as-of" queries the backtest leaks the future (a person's later skills or tickets used to judge earlier assignments). Every fact needs a validity period.
- The data is *already structured*. Tickets have resolver, module, dates and priority. People have skills and teams. The graph comes mostly from fields, not from LLM extraction.

## 2. Which paradigm?
| Paradigm | What it is | Verdict |
|---|---|---|
| Vector RAG | chunks + embeddings | Needed for Q1–Q2 only |
| Microsoft-style GraphRAG | LLM extracts entities from all text, builds community summaries | **No.** It is built for "global" sense-making questions over a whole corpus, indexing is very expensive (40–57× slower in one report), and the entities are noisy |
| Schemaless LLM KG (LightRAG, HippoRAG 2) | LLM-extracted triples + graph walk | Good for multi-hop QA on documents; our schema is known, so free extraction adds noise |
| Temporal KG (Zep/Graphiti) | facts with valid_from/valid_to, contradictions invalidate rather than delete | **Adopt the idea** (bi-temporal edges); the framework is LLM-heavy chat memory, so not needed |
| **Typed, temporal property graph + hybrid text index** | fixed schema of nodes and edges from ticket fields; text and vectors attached to nodes; seed by search, expand by graph, aggregate by SQL | **Chosen** |

Evidence:
- LinkedIn's customer-service system built a KG from historical tickets (intra-ticket structure + inter-ticket links): +77.6% MRR over baseline and −28.6% median resolution time in production (SIGIR 2024).
- GraphRAG-Bench (ICLR 2026): graph retrieval wins on multi-hop and complex reasoning but roughly ties on single-hop lookup. So use the graph for relations and text search for similarity.
- Ticket-assignment research uses graphs too: knowledge-graph embeddings for support tickets, and IssueCourier, a heterogeneous temporal graph.

## 3. The model (schema)
**Nodes:** Person, Team, Ticket, Module/SubArea, SapEntity (T-code, message ID, table, program, IDoc type, BAPI),
Pattern (problem family), Customer, Project, System (SID/client), Skill, Document (KB/resolution chunk).

**Edges (each with `valid_from`, `valid_to`, `source`, `confidence`):**
`RESOLVED`(Person→Ticket, hours, reopened) · `ASSIGNED`/`REASSIGNED`(Ticket→Person, hop#) · `MENTIONS`(Ticket→SapEntity) ·
`IN_MODULE`(Ticket/SapEntity→SubArea) · `INSTANCE_OF`(Ticket→Pattern) · `FOR`(Ticket→Customer/System) ·
`MEMBER_OF`(Person→Team) · `HAS_SKILL`(Person→Skill, level, declared|derived) · `WORKED_ON`(Person→Project) ·
`DUPLICATE_OF`/`RELATED`(Ticket→Ticket) · `DESCRIBES`(Document→Ticket|SapEntity).

**Attached to nodes:** raw text, distilled card text, embedding, BM25 index.

How edges get built:
- **Deterministic** from fields: RESOLVED, ASSIGNED, FOR, MEMBER_OF.
- **Rules and dictionary** with a *controlled vocabulary*: MENTIONS, IN_MODULE.
- **LLM-assisted**, offline, validated against the schema: Pattern clustering, card text, derived skills.
- Every edge records where it came from (provenance).

## 4. Query flow (graph-guided retrieval)
1. **Seed:** hybrid search (BM25 + vector, fused by RRF) over Ticket cards finds similar tickets. Exact SapEntity
   match finds entity nodes.
2. **Expand:** 1–2 hops from the seeds. Ticket→RESOLVED←Person, SapEntity←MENTIONS←Ticket←RESOLVED←Person,
   Ticket→INSTANCE_OF→Pattern.
3. **Score people:** recency-weighted aggregation over paths, in SQL.
   - Upgrade path: Personalized PageRank from the seed nodes over the Person–Ticket–Entity graph (the HippoRAG idea), which ranks experts natively.
4. **Constrain:** current-state facts (availability, load, seniority) with `as_of = now`, or the ticket date in backtests.
5. **Return evidence, not prose:** typed objects with IDs and provenance, which become the L1 context.

The LLM sees the facts through a small **typed fact API**, not raw database access:
`similar_tickets(text, filters, as_of)` · `experts_for(entity|pattern|subarea, as_of)` · `person(id, as_of)` ·
`person_history(id, filters)` · `ticket(id)` · `docs_for(entity)` · `availability(ids, as_of)`.

## 5. Which database
Requirements derived above:
- typed relations at 2–3 hops;
- exact aggregations;
- temporal filters on everything;
- vector + BM25 on the same records;
- transactions (facts must stay consistent);
- moderate scale (10⁴–10⁶ tickets).

| Option | Graph | Aggregation | Vector + BM25 | Temporal | Verdict |
|---|---|---|---|---|---|
| **PostgreSQL + pgvector + BM25 FTS** (nodes/edges tables; recursive CTE, optional Apache AGE for Cypher) | good at 2–3 hops | best | yes, same table | native (ranges, indexes) | **Primary pick**: one store, all seven query types |
| Neo4j (native graph + vector index + Lucene full-text) | best for deep or exploratory traversal | good | yes | modelled on edges | Pick if 3+ hop exploration or graph visualisation becomes central |
| Vector DB + separate graph DB | split | split | yes | split | Two stores to keep in sync; no |
| Vector DB only | no | no | yes | weak | Fails Q3–Q7 |

**Decision:** one relational store modelled as a typed temporal property graph, with hybrid text and vector indexes
on the same rows. Move to (or mirror into) Neo4j only if traversal depth or exploration demands it. The schema
maps 1:1, so this is a migration, not a redesign.

## 6. Not doing
- Microsoft GraphRAG community summaries.
- Schemaless LLM triple extraction as the source of truth.
- Letting the LLM count or decide availability.
- Free-form text-to-SQL or Cypher by the model.

## 7. Evaluate the retrieval layer on its own
- Seed recall@k: same Pattern or same resolver in the top-k.
- Expert ranking: does the actual resolver appear in the top-5 `experts_for`, as of the ticket date?
- Ablations: text-only vs graph-only vs both. Time-leak check: the backtest must use `as_of`.
