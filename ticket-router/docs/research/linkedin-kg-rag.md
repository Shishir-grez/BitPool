# LinkedIn: RAG with Knowledge Graphs for Customer Service QA (SIGIR 2024)

Xu, Cruz, Guevara, Wang, Deshpande, Wang, Li — arXiv 2404.17723.
Verification level: **V** = confirmed via search snippets of the paper or reliable summaries;
**R** = from recollection of the paper, not re-verified here (direct fetch of arXiv was blocked in this session).

## Problem with plain RAG on tickets (V)
Chunking ticket text loses the ticket's structure (summary, description, steps, resolution) and the links between
tickets (duplicates, clones, related issues). Retrieval accuracy and answer quality suffer.

## Method
1. **Intra-issue tree (V):** each historical Jira ticket is parsed into a tree. Nodes are sections such as summary,
   description, steps to reproduce and resolution; edges are hierarchical. Parsing is rule-based for structured fields,
   with an LLM for free text (R).
2. **Inter-issue graph (V):** trees are linked by **explicit** connections (ticket links such as clone/related, R for exact
   types) and **implicit** connections (semantic similarity between tickets, e.g. title-embedding similarity above a threshold, R).
3. **Node embeddings (V):** each node's text is embedded (embedding model reported as E5, R).
4. **Query parsing (R):** the LLM extracts entities mapped to the ticket sections (e.g. which product, which symptom)
   and detects intent.
5. **Sub-graph retrieval (V):** embedding-based search scores tickets by aggregating similarity of the query's entities
   to matching section nodes, then takes the top-K tickets. The graph is traversed to related tickets.
6. **Sub-graph extraction (R):** the LLM translates the question into a graph query (Cypher on Neo4j) over the retrieved
   ticket sub-graphs to pull the specific sections (e.g. the resolution steps).
7. **Generation (V):** the LLM writes the answer from the retrieved sub-graph content (GPT-4 reported, R).

## Results
Retrieval (V, Table 1):

| Metric | Baseline (text RAG) | KG-RAG |
|---|---|---|
| MRR | 0.522 | **0.927** (+77.6%) |
| Recall@1 / @3 | 0.400 / 0.640 | 0.860 / 1.000 |
| NDCG@1 / @3 | 0.400 / 0.520 | 0.860 / 0.946 |

Generation: BLEU +0.32 over the baseline (V). METEOR and ROUGE were also reported; values not verified here.
Evaluation set: a curated "golden" set of typical queries with authoritative solutions (V). Its size is small
(the Recall values move in steps consistent with ~50 queries, an inference, not a reported figure).

Production (V): deployed in LinkedIn customer service for ~6 months. Resolution time per issue:
median 7h → 5h (−28.6%), mean 40h → 15h, P90 87h → 47h (tool-assisted group vs group without it; group split R).

## Caveats
- Small golden set, and a single company's Jira data.
- The baseline is plain chunked RAG, not a strong hybrid baseline (BM25 + dense + reranker).
- It solves "how do I fix this?" (QA), not "who should fix this?" (assignment). People are not modelled.

## What we take from it
- **Keep ticket structure:** parse each ticket into section nodes (symptom, error, steps, root cause, fix), not flat chunks.
- **Explicit + implicit inter-ticket edges:** duplicates and links, plus similarity.
- **Section-aware retrieval:** match query parts to the right sections and aggregate per ticket.
- **Golden-set evaluation of retrieval** before the answer step.
- Extension for us: add Person / Team / SAP-entity nodes, so the same graph answers "who" and "how".

Sources: arxiv.org/abs/2404.17723 · zenml.io LLMOps database entry · themoonlight.io review · researchgate 380401708
