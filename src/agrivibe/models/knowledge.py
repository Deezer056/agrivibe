from pydantic import BaseModel, Field

from agrivibe.db.vectorstore import Category

class IndexResponse(BaseModel):
    doc_id: str
    filename: str
    category: category
    text:str

class SearchHit(Source):
    score:float

class SearchHit(Source):
    score: float

class SearchResponse( BaseModel):
    query:str = Field(min_length=1)
    category: category | None = None
    k: int = Field(default=4, ge=1,  le=20)

class SearchResponse(BaseModel):
    hits: list[SearchHit]    


