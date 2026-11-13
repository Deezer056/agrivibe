from typing import Any

from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.vectorstores import VectorStore

from agrivibe.core.reranker import Reranker
from agrivibe.db.vectorstore import Category, search_chunks


def format_passages(docs: list[Document]) -> str:
    """One block per chunk, headed by [id] so the model has an exact id to cite."""
    if not docs:
        return "No passages found."
    blocks = []
    for doc in docs:
        meta = doc.metadata
        blocks.append(f"[{doc.id}] {meta['source']}, page {meta['page']}\n{doc.page_content}")
    return "\n\n".join(blocks)


def cited_sources(messages: list[BaseMessage], citations: list[str]) -> list[dict[str, Any]]:
    """Returns the passages an answer cites, as the search tool retrieved them.

    The search tool returns the documents as its artifact, so the cited passages are read
    from the agent's messages rather than searched again.

    Args:
        messages: The agent's message history for one run.
        citations: The record ids (`<doc_id>-<n>`) the answer cites, in order.

    Returns:
        One dict per cited passage: id, source, page, category, text and rerank_score.
    """
    retrieved = {}
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == "search_knowledge":
            for doc in message.artifact or []:
                retrieved[doc.id] = doc
    return [
        {
            "id": doc.id,
            "source": doc.metadata["source"],
            "page": doc.metadata["page"],
            "category": doc.metadata["category"],
            "text": doc.page_content,
            "rerank_score": doc.metadata.get("rerank_score"),
        }
        for citation in citations
        if (doc := retrieved.get(citation)) is not None
    ]


def make_search_tool(vector_store: VectorStore, k: int, reranker: Reranker | None = None):
    @tool(response_format="content_and_artifact")
    def search_knowledge(query: str, category: Category | None = None):
        """Search the FieldOracle knowledge base for passages about a question.

        Args:
            query: What to search for, written as a short search query, not the farmer's full message.
            category: Limit the search to one document class. cultivation_guide covers how to grow a
                crop. policy covers government circulars, subsidies and mandates. farm_record covers
                what happened on a specific registered field. Leave empty to search everything.
        """
        docs = [doc for doc, _ in search_chunks(vector_store, query, k, category, reranker)]
        return format_passages(docs), docs  # (text the model reads, Documents your code keeps)

    return search_knowledge