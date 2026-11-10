from functools import lru_cache

from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import InMemorySaver

from agrivibe.agents.fieldoracle.agent import build_fieldoracle_agent
from agrivibe.config import Settings
from agrivibe.core.llm import create_chat_model
from agrivibe.core.reranker import Reranker
from agrivibe.db.vectorstore import create_vector_store
from agrivibe.service.answering import AnswerService
from agrivibe.service.knowledge import KnowledgeService


@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_vector_store() -> PineconeVectorStore:
    return create_vector_store(get_settings())

@lru_cache
def get_reranker() -> Reranker | None:
    settings = get_settings()
    return None if settings.reranker == "none" else Reranker(settings)

@lru_cache
def get_knowledge_service() -> KnowledgeService:
    settings = get_settings()
    return KnowledgeService(
        vector_store=get_vector_store(),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        reranker=get_reranker(),
    )

@lru_cache
def get_answer_service() -> AnswerService:
    settings = get_settings()
    # Threads live in process memory: they reset when the app restarts.
    agent = build_fieldoracle_agent(
        create_chat_model(settings),
        get_vector_store(),
        k=settings.search_k,
        checkpointer=InMemorySaver(),
        reranker=get_reranker(),
    )
    return AnswerService(agent)