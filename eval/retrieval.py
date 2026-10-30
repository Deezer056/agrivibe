"""The three retrieval strategies the bench compares: vector only, hybrid (vector + BM25), hybrid + rerank."""

import re
from pathlib import Path

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from agrivibe.db.vectorstore import search_chunks
from agrivibe.dependencies import get_settings, get_vector_store
from agrivibe.service.knowledge import KnowledgeService, make_doc_id, read_pdf

DATA = Path(__file__).parent.parent / "data"
CANDIDATES = 20  # how many chunks each retriever hands to fusion / the reranker
RRF_K = 60  # the usual constant in reciprocal rank fusion
STOPWORDS = {"the", "a", "an", "is", "are", "this", "that", "for", "of", "to", "in", "on", "at", "and", "or",
             "what", "how", "does", "should", "can", "will", "be", "it", "its", "maha", "paddy", "field"}


def tokenize(text: str) -> list[str]:
    """Lowercase words, so 'Sammanthurai' and 'sammanthurai' match in BM25. Common words are dropped."""
    return [word for word in re.findall(r"\w+", text.lower()) if word not in STOPWORDS]


def load_chunks() -> list[Document]:
    """Chunk the PDFs exactly the way /knowledge/index does, so BM25 sees the same chunks as Pinecone."""
    settings = get_settings()
    splitter = KnowledgeService(None, settings.chunk_size, settings.chunk_overlap).splitter
    chunks = []
    for path in sorted(DATA.glob("*.pdf")):
        data = path.read_bytes()
        pages = read_pdf(data, {"doc_id": make_doc_id(path.name, data), "source": path.name})
        chunks.extend(splitter.split_documents(pages))
    return chunks


class Retrievers:
    def __init__(self):
        self.vector_store = get_vector_store()
        self.bm25 = BM25Retriever.from_documents(load_chunks(), k=CANDIDATES, preprocess_func=tokenize)
        self.cross_encoder = None  # loaded on first use, it takes a few seconds

    def vector(self, query: str, k: int) -> list[Document]:
        return [doc for doc, _ in search_chunks(self.vector_store, query, k)]

    def hybrid(self, query: str, k: int) -> list[Document]:
        """Reciprocal rank fusion: each list gives a chunk 1/(60 + rank); sort by the sum."""
        scores: dict[str, float] = {}
        docs: dict[str, Document] = {}
        for ranked in (self.vector(query, CANDIDATES), self.bm25.invoke(query)):
            for rank, doc in enumerate(ranked, start=1):
                key = doc.page_content  # the same chunk text from both lists counts as one chunk
                scores[key] = scores.get(key, 0.0) + 1 / (RRF_K + rank)
                docs.setdefault(key, doc)
        best = sorted(scores, key=scores.get, reverse=True)[:k]
        return [docs[key] for key in best]

    def rerank(self, query: str, k: int) -> list[Document]:
        """Take 20 hybrid candidates and let a cross-encoder re-order them by reading query and chunk together."""
        if self.cross_encoder is None:
            from sentence_transformers import CrossEncoder

            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
        candidates = self.hybrid(query, CANDIDATES)
        scores = self.cross_encoder.predict([(query, doc.page_content) for doc in candidates])
        ranked = sorted(zip(scores, candidates), key=lambda pair: pair[0], reverse=True)
        return [doc for _, doc in ranked[:k]]
