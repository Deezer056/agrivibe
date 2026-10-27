from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

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


def make_search_tool(vector_store: VectorStore, k: int):
    @tool(response_format="content_and_artifact")
    def search_knowledge(query: str, category: Category | None = None):
        """Search the FieldOracle knowledge base for passages about a question.

        Args:
            query: What to search for, written as a short search query, not the farmer's full message.
            category: Limit the search to one document class. cultivation_guide covers how to grow a
                crop. policy covers government circulars, subsidies and mandates. farm_record covers
                what happened on a specific registered field. Leave empty to search everything.
        """
        docs = [doc for doc, _ in search_chunks(vector_store, query, k, category)]
        return format_passages(docs), docs  # (text the model reads, Documents your code keeps)

    return search_knowledge