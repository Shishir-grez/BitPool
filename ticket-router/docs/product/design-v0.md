# Ticket Router — product design v0 (draft for discussion)

Recommend the best team member for a new SAP support ticket, with reasons and evidence.
Environment-agnostic: runs the same on a local CPU model or a hosted model.

## 1. Users and jobs
| User | Job |
|---|---|
| Dispatcher / team lead (primary) | Assign incoming tickets quickly and fairly; see why a person is suggested |
| Assignee | See similar past tickets and how they were resolved |
| Admin | Maintain roster, skills, availability, rules |

**v1 principle:** recommend only. A human confirms every assignment.

## 2. Features
**MVP (v0.1)**
1. Ingest a ticket-history export (CSV/Excel) and a team roster.
2. Understand a new ticket: module, sub-area, type, complexity, urgency, SAP entities (T-codes, message IDs, IDocs, dumps).
3. Find similar resolved tickets (hybrid lexical + semantic search).
4. Build and refresh member profiles from history plus declared skills.
5. Filter out people who can't take it (leave, left, at capacity, too junior for the priority).
6. LLM picks the top 3 from a shortlist, with reasons citing ticket IDs, plus a confidence level.
7. Abstain and route to the lead when evidence is thin.
8. Backtest harness: replay history in time order and score.

**v0.2:** accept/override capture with reason, duplicate/related open-ticket detection, resolution hints for the assignee, workload fairness view.
**v0.3:** ticketing-system integration (ServiceNow / SolMan / Jira), batch queue mode, growth assignments (stretch tickets for juniors).

## 3. Inputs
| Input | Required fields | Nice to have |
|---|---|---|
| Resolved ticket history | id, created, title, description, priority, resolver, resolved_at | module/category, assignment group, reassignment history, resolution notes, hours spent, reopen count |
| Team roster | member id, status, seniority, modules | skill levels, certifications, shift/timezone, languages, capacity, leave calendar |
| Live workload | open tickets per member | effort-weighted load |
| New ticket | title, description, priority | module, reporter/company, system/client (PRD/QAS) |
| Rules (YAML) | priority→min seniority, capacity caps | customer/system access restrictions |

## 4. Outputs
```
Recommendation {
  ticket_id, understood: {module, sub_area, type, complexity, entities[]},
  ranked: [{member_id, rank, reason, evidence_ticket_ids[], risk_flags[]}],  # top 3
  confidence: high|medium|low, abstain: bool, abstain_reason,
  related_open_tickets[], resolution_hints[], audit: {model, prompt_version, latency_ms}
}
```
Delivered as UI card, CSV/JSON, and an audit log row.

## 5. Pipelines
**A. Index build (batch, nightly or on demand)**
load export → clean/normalise → redact PII → dedupe → extract attributes (LLM + regex, cached) →
build "problem text" (title + description) → embed + BM25 index → store resolution text separately.

**B. Profile build**
Roster + history → per member per module/sub-area: ticket count, recency-weighted count, median hours,
reopen rate, last active. Merge with declared skills. Render a short profile card for each member.

**C. Recommend (online, per ticket)**
1. Validate and redact input.
2. Understand: regex SAP entities, then LLM classification into fixed option sets.
3. Retrieve the top-k similar resolved tickets (hybrid, recency-weighted, filtered by module when confident).
4. Candidates = resolvers of similar tickets ∪ members skilled in the module.
5. Hard filters from rules and availability. This step is deterministic and never left to the LLM.
6. Evidence pack per candidate: profile card, their similar tickets, current load. Counts are computed in code, not by the LLM.
7. LLM decides: listwise choice over 3–5 candidates, JSON schema output.
8. Validate the output: ids exist, cited tickets are in the pack, schema is valid; retry once, else abstain.
9. Confidence and abstain gate.

**D. Feedback (v0.2)**
Accept/override plus reason → log. Use for evaluation, few-shot examples and profile corrections.

**E. Evaluation**
- Time-split backtest: train on the past, test on later tickets.
- Metrics: top-1 and top-3 hit rate vs the actual resolver, abstain rate, accuracy when not abstaining, latency, load spread.
- Baselines: most-frequent resolver per module; kNN vote over retrieved tickets; LLM with no retrieval.
- Ablations: no BM25, no profiles, no filters.
- Caveat: the actual resolver is not always the *best* choice. Add a small set of tickets labelled by the lead as "acceptable assignees".

## 6. Architecture decisions (ADR candidates)
| # | Decision | Recommendation | Why |
|---|---|---|---|
| 1 | Target | Two-stage: module/group, then person | Errors are easier to see; shrinks the candidate set |
| 2 | Who decides | LLM decides among the shortlist; code filters and computes evidence | LLMs are poor at counting and at enforcing rules; good at weighing text evidence |
| 3 | Decision format | Listwise pick over 3–5 candidates (pointwise scoring later, for calibration) | One call; fits the CPU token budget |
| 4 | Retrieval | Hybrid BM25 + dense | SAP codes (ME21N, F5 301, IDoc 51) are lexical; symptoms are semantic |
| 5 | Embedded text | Problem text only; resolution kept separate | Matches how a new ticket looks |
| 6 | Store | SQLite + in-memory vectors (numpy) | <100k tickets; zero extra infra |
| 7 | LLM interface | Own thin adapter: local ONNX ↔ hosted API | Same product on both targets; no `litellm` |
| 8 | Output control | JSON schema, then validation, then 1 retry, then abstain | Small models drift |
| 9 | Untrusted text | Ticket text is data: delimit it, never follow instructions in it; output only IDs from the shortlist | Prompt-injection risk |
| 10 | Rules | YAML config, versioned | Lead can tune without code |
| 11 | Interface | CLI for pipelines and eval (BitPool-style subcommands + REPL); Streamlit for the demo UI | Fast to build, pip-only |
| 12 | Prompt/model versioning | Every output logs model + prompt version | Comparable backtests |

## 7. Tech stack (pip-only, Python)
pandas, pydantic, PyYAML, SQLite (stdlib), numpy, a BM25 implementation (rank-bm25 or our own TF-IDF),
onnxruntime (embeddings), LLM adapter (onnxruntime-genai locally / HTTP client for the cloud), typer (CLI),
streamlit (UI), pytest.

## 8. Known failure points → mitigations
| Risk | Mitigation |
|---|---|
| Wrong module classification cascades | Retrieve unfiltered too; show module confidence; two-stage review |
| Popularity bias (seniors get everything) | Load cap filter; load in evidence; fairness metric |
| Cold start (new member, new module) | Declared skills; "growth" flag; abstain |
| Label noise (reassignments, wrong resolver) | Use final resolver + hop count; down-weight hopped tickets |
| Vague tickets ("system slow") | Ask-for-info flag; abstain |
| Hallucinated IDs/evidence | Output validation against the shortlist and evidence pack |
| Stale availability/workload | Timestamp the inputs; warn if older than N hours |
| Mixed language / German text | Multilingual embedder; test set includes them |
| CPU latency | Small evidence pack (4–8k tokens); cache understanding step |

## 9. Open product questions
1. Recommend an individual directly, or group first?
2. Who is the user: a central dispatcher, or team leads per module?
3. Which ticketing system and which export fields exist (especially reassignment history and resolution notes)?
4. Acceptable time per recommendation (seconds vs a minute or two)?
5. Is a per-customer or per-system access restriction needed?

## 10. Existing scaffold
`ticket_router/` (models, config, data loader, synthetic generator) predates this design. Its weighted-score
config (w_history, w_skill…) becomes the **baseline scorer** for evaluation, not the decider. Rework it after this design is agreed.
