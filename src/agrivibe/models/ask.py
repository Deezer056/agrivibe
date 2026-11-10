from pydantic import BaseModel, Field

from agrivibe.agents.fieldoracle.schemas import CitedSentence
from agrivibe.models.knowledge import Source


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    thread_id: str | None = Field(default=None, max_length=200)


class AskResponse(BaseModel):
    question: str
    thread_id: str
    found: bool
    answer: str
    sentences: list[CitedSentence]
    sources: list[Source]
    searches: list[str]
