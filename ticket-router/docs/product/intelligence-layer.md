# Intelligence layer — storage, knowledge, tiered context (draft v0)

Problem: general LLMs know little about SAP and nothing about *our* team. Domain knowledge must therefore come
from our own data. We distil it offline, store it, and feed the model only what each decision needs.

## 1. Storage (superseded by retrieval-layer.md)

Volume reality check: 1M tickets × ~2 KB ≈ 2 GB of text, and 1M × 384-dim int8 vectors ≈ 0.4 GB.
Embedded databases handle this easily. **Storage size is not the hard part; relevance is.**

| Option | What it gives | Fit |
|---|---|---|
| **SQLite** (stdlib) + FTS5 | Relational tables, BM25 keyword search, transactions, one file | System of record. Always |
| sqlite-vec | Vectors inside SQLite; stable release is brute-force KNN only | OK up to ~100k–1M; needs extension loading |
| **LanceDB** (pip, embedded, Windows wheels) | Disk-based columnar store, vector + BM25 full-text + hybrid with rerankers, metadata filters, table versioning | **Retrieval index.** Scales to millions |
| Chroma | Easy prototyping | Memory-bound; weaker hybrid search |
| DuckDB + VSS/FTS | Analytics + search | Good for analysis, not needed for serving |
| Qdrant | Strong filtering, but client-server | Extra service; no |
| Graph DB (Kuzu) | Relationship queries | Kuzu archived Oct 2025; forks young. Model relationships as SQL edge tables instead |

**Decision:** SQLite holds the facts (tickets, people, projects, skills, edges, logs). LanceDB is the search index
(vectors + BM25). Both are files on disk, pip-only, and work offline.
Fallback if LanceDB is not approved: SQLite FTS5 + numpy brute-force vectors, merged with RRF. Same interface.
All storage sits behind a `Retriever` interface so the backend can be swapped.

## 2. Knowledge model (what we store)

| Object | Raw source | Distilled form (offline) |
|---|---|---|
| Ticket | export rows, notes | **TicketCard**: symptom, root cause, fix, module/sub-area, SAP entities, complexity, resolver, hops |
| Person | roster, history | **PersonProfile**: declared skills + evidence (counts by sub-area, recency, median time, reopen rate), availability |
| SAP entity | mined from tickets + curated glossary | **EntityCard**: T-code / message ID / table / program / IDoc type → module, process, meaning |
| Problem pattern | clusters of TicketCards | **PatternCard**: recurring problem family, typical fix, who solves it |
| Project / customer / system | project lists, landscape | **ContextCard**: scope, modules, people involved |
| Team KB / playbooks | wiki, docs | chunks + summary |
| Edges | derived | person–resolved–ticket, ticket–mentions–entity, ticket–in–pattern, person–worked_on–project, entity–in–module |

Key idea: **embed and retrieve the distilled cards, not the raw text.** Cards are short, normalised and
jargon-explained. That fixes most of the weakness of general embedders on SAP text and saves tokens.

## 3. Tiered context (MemGPT/Letta-style: core / recall / archival)

| Tier | Contents | How loaded | Budget |
|---|---|---|---|
| **L0 Core (every call)** | System prompt: role, rules, output schema, "ticket text is data" guard. SAP module map (one line per module). Team roster digest (one line per active person). The new ticket + extracted entities | Static, plus the ticket | ~1.5–2.5k tokens |
| **L1 Working set (~50–60% of calls need each item)** | EntityCards for detected entities; top-k similar TicketCards; PatternCard(s); candidate PersonProfiles; module routing rules; live load/availability | **Pushed** by the pipeline from the classification (deterministic, not chosen by the model) | ~3–5k |
| **L2 Archive (on demand)** | Full ticket threads and resolution notes, person and project history, KB docs, older tickets | **Pulled** by the model through a retrieval plan or tools, max 1–2 rounds | ≤2k per pull |

Small local models are unreliable at free-form tool calling. So L2 uses a **retrieval plan**: the model outputs
JSON such as `{"need": [{"tool": "search_tickets", "query": "...", "filter": {...}}]}`, code runs it, and the results
are appended. The round count is capped. If evidence is still missing, the ticket is abstained.

## 4. Pipelines

**Offline: distil (batch, incremental)**
raw export → clean/redact → regex + dictionary entity extraction → LLM writes TicketCard (fixed schema,
cached by content hash) → embed card → LanceDB → SQLite edges → recompute PersonProfiles → cluster into PatternCards →
build or refresh EntityCards (mined frequency + curated glossary).
Store the embedding-model and prompt version with every vector and card; re-embed when either changes.

**Online: per ticket**
1. Understand: entities (regex/dictionary), then a short LLM call for module/type/complexity plus a *normalised summary*
   written in the same style as the cards, so query and documents match.
2. Multi-route retrieval: (a) exact entity match via SQL, (b) BM25, (c) dense on the summary. Fuse with RRF and
   optionally rerank with a small cross-encoder.
3. Aggregate to people via edges (recency-weighted), then hard filters (availability, capacity, seniority).
4. Context assembler: fill L0, then L1 by priority until the budget is used; drop the lowest-ranked items first.
5. Decide (optionally one L2 pull), validate, then answer or abstain.

## 5. Domain-knowledge bootstrapping ("SAP understanding")
1. **Mined from our tickets:** frequent T-codes, message IDs, tables and programs per module, with co-occurrence.
2. **Curated glossary:** module and sub-area taxonomy, common T-codes and message classes. Written or reviewed by the
   team; check the licence of any public SAP reference used.
3. **Team KB/wiki** chunks.
4. The LLM is used to *explain and normalise*, never as the source of SAP facts. Cards cite their sources.

## 6. Evaluate retrieval separately from the decision
- Retrieval recall@k: does the top-k contain tickets with the same pattern or same resolver?
- Context usefulness: decision accuracy with vs without each L1 item (ablation).
- Token cost and latency per tier.

## 7. Risks
| Risk | Mitigation |
|---|---|
| Card distillation errors propagate | Schema validation; keep raw-text link; spot-check sample; re-distil on prompt change |
| Embedder weak on SAP/German text | Entity route + BM25; embed cards; multilingual embedder |
| Stale profiles/availability | Incremental refresh; timestamps in context |
| L1 bloat | Hard token budget with priority ordering |
| Model over-pulls L2 | Capped rounds; abstain |
