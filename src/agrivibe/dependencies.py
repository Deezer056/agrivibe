from functools import lru_cache

from fastapi import Request
from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from agrivibe.agents.advisory import build_advisory_agent
from agrivibe.agents.farm_context import build_farm_context_agent
from agrivibe.agents.fieldoracle.agent import build_fieldoracle_agent
from agrivibe.agents.orchestrator import build_orchestrator
from agrivibe.agents.weather import build_weather_agent
from agrivibe.config import Settings
from agrivibe.core.llm import create_chat_model
from agrivibe.core.mcp import FieldSat
from agrivibe.core.reranker import Reranker
from agrivibe.db.vectorstore import create_vector_store
from agrivibe.service.answering import AnswerService
from agrivibe.service.chatting import ChatService
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


def build_chat_service(settings: Settings, fieldsat: FieldSat) -> ChatService:
    """Builds the specialists and the orchestrator that calls them.

    Called once, from the lifespan in main.py: the FieldSat tools are only known after
    the app has asked the server for them.

    Args:
        settings: Application settings.
        fieldsat: The tools and instructions loaded from the FieldSat MCP server.

    Returns:
        The service behind POST /chat.
    """
    model = create_chat_model(settings)
    weather_agent = build_weather_agent(model, fieldsat)
    farm_context_agent = build_farm_context_agent(model, fieldsat)
    # A second FieldOracle, without a checkpointer: as a specialist it starts fresh on every call.
    # It searches the same way /ask does: vector search, then the cross-encoder.
    knowledge_agent = build_fieldoracle_agent(model, get_vector_store(), k=settings.search_k, reranker=get_reranker())
    advisory_agent = build_advisory_agent(model)
    # Both live in process memory, so they reset when the app restarts.
    # In production they would be database-backed (Postgres, Redis).
    orchestrator = build_orchestrator(
        model,
        fieldsat,
        weather_agent,
        farm_context_agent,
        knowledge_agent,
        advisory_agent,
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )
    return ChatService(orchestrator)


def get_chat_service(request: Request) -> ChatService:
    """Returns the chat service the lifespan built at startup."""
    return request.app.state.chat_service