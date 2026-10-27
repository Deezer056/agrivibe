from pydantic import BaseModel, Field

from agrivibe.db.vectorstore import Category


class IndexResponse(BaseModel):
    doc_id: str
    filename: str
    category: Category
    pages: int
    chunks: int


class Source(BaseModel):
    id: str
    source: str
    page: int
    category: Category
    text: str


class SearchHit(Source):
    score: float


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    category: Category | None = None
    k: int = Field(default=4, ge=1, le=20)


class SearchResponse(BaseModel):
    hits: list[SearchHit]
