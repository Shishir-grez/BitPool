# LinkedIn: RAG with Knowledge Graphs for Customer Service QA (SIGIR 2024)

Xu, Cruz, Guevara, Wang, Deshpande, Wang, Li. arXiv 2404.17723, DOI 10.1145/3626772.3661370. 5 pages.
**Verified against the full paper text (arXiv PDF).**

## Problem
- **Limitation 1, structure lost:** Jira tickets have sections and links ("A is related to / copied from / caused by B").
  Chunking them as plain text loses both.
- **Limitation 2, segmentation hurts answers:** fixed-length chunks can split the issue (at the top) from its
  solution (at the bottom), giving incomplete answers.

## Method
### KG construction
- **Dual-level graph.**
  - The **intra-issue tree** has one node per ticket section, identified by (ticket, section). Edges are hierarchical and
    typed: HAS_SUMMARY, HAS_DESCRIPTION, HAS_STEPS_TO_REPRODUCE, HAS_PRIORITY, HAS_ROOT_CAUSE, HAS_IMPACT_AREA,
    HAS_COMMENTS, HAS_FIELDS.
  - The **inter-issue graph** has explicit links taken from Jira fields (e.g. CLONE_FROM / CLONE_TO) and implicit
    SIMILAR_TO links, created where cos(embed(title_i), embed(title_j)) ≥ θ. The value of θ is not reported.
- **Parsing is hybrid.**
  - Rules extract predefined fields (e.g. code sections found by keyword).
  - For the remaining free text, an LLM guided by a **YAML graph template** (the sections support staff routinely use)
    maps the text into the tree.
- **Embeddings:** one per text-rich node (summary, description, steps to reproduce…), using BERT/E5-class models,
  stored in a vector DB (Qdrant given as an example). Long sections are chunked within the section, which is safe because
  each chunk belongs to a single section.
- **Graph DB:** Neo4j (queried with Cypher).

### Retrieval and QA
1. **Entity and intent parsing (LLM):** query → P = Map(section → value) plus an intent set I (which sections the user
   wants). Example: "issue summary" → "login issue", "issue description" → "user can't log in", I = {"fix solution"}.
2. **Ticket scoring (EBR):** for each (section k, value v) in P, cosine(v, every node of section k). Scores are summed per ticket:
   `S(T_i) = Σ_(k,v)∈P Σ_n∈T_i 1{n.sec = k} · cos(embed(v), embed(n.text))`, and the top-K tickets are kept.
   Assumption stated: several matching entities indicate relevance.
3. **LLM-driven sub-graph extraction:** the query is rewritten to include the retrieved ticket ID, then translated
   to **Cypher**, e.g. `MATCH (j:Ticket {ticket_ID:'ENT-22970'})-[:HAS_DESCRIPTION]->(d)-[:HAS_STEPS_TO_REPRODUCE]->(s) RETURN s.value`.
   This works within one ticket's tree or across trees.
4. **Answer generation:** the LLM writes the answer from the retrieved node values. **Fallback:** if the graph query fails,
   the system reverts to baseline text retrieval.

## Evaluation
- Curated "golden" dataset of typical queries, support tickets and authoritative solutions. **Size not reported.**
- Control: conventional text-chunk EBR. Same LLM (**GPT-4**) and embedder (**E5**) for both.

| Retrieval | Baseline | KG-RAG |
|---|---|---|
| MRR | 0.522 | **0.927** (+77.6%) |
| Recall@1 / @3 | 0.400 / 0.640 | 0.860 / 1.000 |
| NDCG@1 / @3 | 0.400 / 0.520 | 0.860 / 0.946 |

| Answer quality | Baseline | KG-RAG |
|---|---|---|
| BLEU | 0.057 | 0.377 |
| METEOR | 0.279 | 0.613 |
| ROUGE | 0.183 | 0.546 |

## Production
- Deployed for about 6 months in LinkedIn customer service, across multiple product lines.
- The **team was split randomly into two groups**: one used the tool, the other kept manual methods.
- Group sizes, ticket counts and significance tests are **not reported**.

| Resolution time | Mean | P50 | P90 |
|---|---|---|---|
| Tool not used | 40 h | 7 h | 87 h |
| Tool used | 15 h | 5 h (−28.6%) | 47 h |

## Limitations (ours) and future work (theirs)
- Ours:
  - The golden set size is unknown and probably small.
  - The baseline is plain chunked EBR, not a hybrid BM25 + dense + reranker setup.
  - θ and K are not reported.
  - Production results have no sample sizes or confidence intervals.
  - Randomising staff, rather than tickets, can be confounded by individual skill.
  - The system answers "how to fix", not "who should fix"; people are not modelled.
- Theirs:
  - automatic extraction of graph templates;
  - dynamic KG updates from user queries;
  - applying the method beyond customer service.

## What we take from it
1. **A section template (YAML) for SAP tickets:** symptom, error/message ID, T-code, steps, root cause, fix, module,
   priority, comments. Rules first, LLM for the rest.
2. **Section-aware scoring:** parse the new ticket into the same sections and sum similarity per section per past ticket.
   This directly replaces "embed the whole ticket".
3. **Explicit links (duplicate, parent/child, related) plus implicit SIMILAR_TO links** with a tuned θ.
4. **Text-retrieval fallback** whenever the graph path fails.
5. **Golden set plus randomised pilot** as the evaluation pattern.
6. **Change for us:** the LLM does not write free-form Cypher. It picks from a typed Fact API, which is safer with small
   local models. We also add Person/Team/SAP-entity nodes so the graph answers "who".
