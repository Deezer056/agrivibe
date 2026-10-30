# Retrieval quality report

FieldOracle retrieval measured on `eval/bench.json`: 9 answerable questions with evidence phrases copied
from the PDFs, plus 2 unanswerable ones. A chunk counts as relevant if it contains an evidence phrase.
Scores come from `uv run python eval/run_bench.py [vector|hybrid|rerank]`.

## Results (9 answerable questions, k = 5)

| Retrieval | Recall@5 | Precision@5 | MRR |
|---|---|---|---|
| Baseline (vector) | 0.593 | 0.289 | 0.519 |
| Hybrid (vector + BM25, RRF) | 0.370 | 0.200 | 0.467 |
| Hybrid + rerank | 0.593 | 0.311 | 0.648 |

Hybrid on its own made retrieval worse: BM25 rewards chunks that share common words with the question,
and RRF lets those chunks push relevant vector hits out of the top 5. Reranking 20 hybrid candidates with
a cross-encoder gave the best precision and MRR, at the same recall as the baseline.


  | Retrieval | Recall@5 | Precision@5 | MRR |
  |---|---|---|---|
  | Hybrid + stopwords | 0.398 | 0.222 | 0.411 |
  | Hybrid + rerank + stopwords | 0.593 | 0.311 | 0.648 |

## Diagnosis of misses
| Question | Missed in | Cause (query / chunking / index / corpus) | Why |
|---|---|---|---|
| q04 Sammanthurai schedule | baseline, hybrid | query | The word "schedule" matches the CG-06 fertiliser tables, which fill the top 5. The deciding sentence (Ampara is not on the irrigated list) is in FR-00 and POL-03 and never mentions "schedule". Rerank fixes it. |
| q09 urea kg at 6 weeks | all three | query | The question asks for a number, so the CG-06 dosage tables win. The evidence is the POL-01 rule "never state a fertiliser quantity", which shares no words with the question. |
| q07 gall midge | hybrid, rerank | chunking | "Infestation is high in the Dry and Intermediate Zones during Maha" sits at the top of CG-08 page 2, after the page header. Pages are chunked separately, so that chunk never says "gall midge". |
| q08 PMB price | hybrid | query | The evidence chunk says "Guaranteed prices" (plural), and BM25 has no stemming, so "price" in the question does not match it. BM25 ranks other POL chunks first, and RRF pushes the evidence chunk (rank 3 in vector search) out of the top 5. Rerank brings it back. |

## Per-question results

### Baseline (vector)
```
id      R@5   P@5   MRR  top sources
q01    0.50  0.40  1.00  FR-02_, FR-01_, FR-02_, FR-00_, FR-04_
q02    0.33  0.20  0.33  CG-03_, CG-05_, FR-04_, CG-05_, CG-05_
q03    0.50  0.20  0.50  FR-03_, CG-09_, FR-03_, FR-01_, CG-02_
q04    0.00  0.00  0.00  CG-06_, CG-06_, CG-06_, CG-03_, FR-03_
q05    1.00  0.40  1.00  POL-04, FR-02_, POL-04, FR-02_, FR-02_
q06    1.00  0.60  1.00  POL-05, FR-02_, POL-05, POL-05, POL-04
q07    1.00  0.40  0.50  CG-08_, CG-08_, FR-01_, CG-08_, FR-04_
q08    1.00  0.40  0.33  POL-04, POL-06, POL-06, POL-06, FR-01_
q09    0.00  0.00  0.00  CG-06_, CG-06_, CG-06_, CG-06_, CG-06_
q10       -     -     -  FR-00_, FR-00_, CG-04_, CG-03_, CG-06_  (unanswerable)
q11       -     -     -  CG-06_, CG-03_, CG-03_, CG-08_, FR-01_  (unanswerable)
```

### Hybrid + stopwords
```
id      R@5   P@5   MRR  top sources
q01    0.75  0.60  1.00  FR-02_, FR-01_, CG-02_, FR-00_, FR-02_
q02    0.33  0.20  0.20  CG-05_, CG-03_, CG-05_, CG-05_, FR-04_
q03    0.50  0.20  0.50  FR-03_, CG-09_, FR-03_, CG-04_, CG-09_
q04    0.00  0.00  0.00  CG-06_, FR-03_, CG-06_, CG-03_, CG-06_
q05    1.00  0.40  1.00  FR-02_, POL-04, FR-02_, POL-04, POL-05
q06    1.00  0.60  1.00  POL-05, FR-02_, POL-05, FR-02_, POL-05
q07    0.00  0.00  0.00  CG-08_, CG-08_, FR-01_, CG-08_, FR-00_
q08    0.00  0.00  0.00  POL-06, POL-04, FR-01_, POL-04, POL-03
q09    0.00  0.00  0.00  CG-06_, CG-06_, CG-06_, CG-06_, CG-06_
q10       -     -     -  FR-00_, FR-00_, CG-08_, FR-01_, FR-04_  (unanswerable)
q11       -     -     -  CG-08_, CG-09_, CG-09_, POL-02, CG-06_  (unanswerable)
```

### Hybrid + rerank + stopwords
```
id      R@5   P@5   MRR  top sources
q01    0.50  0.40  1.00  FR-02_, FR-01_, FR-02_, FR-04_, FR-00_
q02    1.00  0.60  1.00  FR-04_, CG-03_, CG-05_, FR-04_, CG-05_
q03    0.50  0.20  0.50  FR-03_, CG-09_, FR-03_, POL-03, CG-03_
q04    0.67  0.40  1.00  POL-03, CG-06_, FR-00_, CG-06_, CG-06_
q05    1.00  0.40  1.00  FR-02_, POL-04, POL-05, POL-06, POL-04
q06    0.67  0.40  1.00  POL-05, FR-02_, FR-02_, FR-02_, FR-00_
q07    0.00  0.00  0.00  FR-00_, FR-00_, CG-07_, CG-08_, CG-08_
q08    1.00  0.40  0.33  POL-04, POL-06, POL-06, POL-06, FR-01_
q09    0.00  0.00  0.00  CG-07_, FR-01_, CG-07_, CG-06_, CG-06_
q10       -     -     -  FR-00_, FR-00_, FR-03_, FR-01_, FR-04_  (unanswerable)
q11       -     -     -  CG-08_, CG-09_, CG-07_, CG-09_, CG-04_  (unanswerable)
```

## Next steps
- Chunk across page breaks (or strip the page header) so q07's evidence sits with "gall midge".
- Move hybrid + rerank into `/knowledge/search` and FieldOracle, since it gives the best MRR.
