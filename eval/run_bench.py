"""Score retrieval on eval/bench.json: Recall@5, Precision@5 and MRR.

Run from the agrivibe folder:  uv run python eval/run_bench.py
It calls the same KnowledgeService that /knowledge/search uses, so the app doesn't need to be running.
"""

import json
import re
from pathlib import Path

from agrivibe.dependencies import get_knowledge_service

K = 5
BENCH = Path(__file__).parent / "bench.json"


def normalise(text: str) -> str:
    """Lowercase and squash whitespace, so PDF line breaks don't stop a phrase from matching."""
    return re.sub(r"\s+", " ", text).lower()


def score_question(texts: list[str], evidence: list[str]) -> dict:
    texts = [normalise(t) for t in texts]
    phrases = [normalise(e) for e in evidence]

    # A chunk is relevant if it contains at least one evidence phrase.
    relevant = [any(p in t for p in phrases) for t in texts]
    found = [p for p in phrases if any(p in t for t in texts)]
    first = next((rank for rank, ok in enumerate(relevant, start=1) if ok), None)

    return {
        "recall": len(found) / len(phrases),  # share of evidence phrases found in the top K
        "precision": sum(relevant) / K,  # share of the top K chunks that are relevant
        "mrr": 1 / first if first else 0.0,  # 1 / rank of the first relevant chunk
    }


def main() -> None:
    service = get_knowledge_service()
    bench = json.loads(BENCH.read_text(encoding="utf-8"))
    rows = []

    print(f"{'id':<5}{'R@5':>6}{'P@5':>6}{'MRR':>6}  top sources")
    for q in bench:
        hits = service.search(q["question"], K).hits
        sources = ", ".join(h.source[:6] for h in hits)
        if not q["answerable"]:
            print(f"{q['id']:<5}{'-':>6}{'-':>6}{'-':>6}  {sources}  (unanswerable, top score {hits[0].score:.3f})")
            continue
        s = score_question([h.text for h in hits], q["evidence"])
        rows.append(s)
        print(f"{q['id']:<5}{s['recall']:>6.2f}{s['precision']:>6.2f}{s['mrr']:>6.2f}  {sources}")

    n = len(rows)
    print(
        f"\nMean over {n} answerable questions: "
        f"Recall@{K} {sum(r['recall'] for r in rows) / n:.3f} | "
        f"Precision@{K} {sum(r['precision'] for r in rows) / n:.3f} | "
        f"MRR {sum(r['mrr'] for r in rows) / n:.3f}"
    )


if __name__ == "__main__":
    main()
