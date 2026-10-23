from ast import Return
from functools import lru_cache
from this import d

from langchain_pinecone import PineconeVectorStore

from agrivibe.config import Settings
from agrivibe.db.vectorstore import create_vector_store
from agrivibe.service.knowledge import KnowledgeService

@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_vector_store() -> PineconeVectorStore:
    return create_vector_store(get_settings())

@lru_cache
def get_knowledge_service() -> KnowledgeService:
    Settings = get_settings()
    return KnowledgeService(
        vector_store=get_vector_store(),
        chunk_size=Settings.chunk_size,
        chunk_overlap=Settings.chunk_overlap,
    )