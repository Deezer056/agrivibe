from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: SecretStr
    pinecone_api_key: SecretStr
    database_url: SecretStr

    # The farmer this app acts for. Identity is decided here, on the server, never by the request:
    # see current_farmer in dependencies.py, the one place a real auth service would plug in.
    farmer_id: str = "frm_7f3a9c2e"
    farmer_name: str = "Nimal Perera"

    chat_model: str = "openai:gpt-5.6-terra"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    pinecone_index: str = "fieldoracle"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    chunk_size: int = 1000
    chunk_overlap: int = 150
    search_k: int = 4

    # Two-stage retrieval: fetch RERANK_CANDIDATES chunks, re-score them with a
    # cross-encoder and keep the best SEARCH_K. "none" skips the second stage.
    reranker: Literal["pinecone", "none"] = "pinecone"
    rerank_model: str = "bge-reranker-v2-m3"
    rerank_candidates: int = 20

    fieldsat_url: str = "http://127.0.0.1:8001/mcp"
