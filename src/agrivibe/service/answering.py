from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from agrivibe.agents.fieldoracle.schemas import CitedAnswer
from agrivibe.models.ask import AskResponse
from agrivibe.models.knowledge import Source


def to_source(doc: Document) -> Source:
    meta = doc.metadata
    return Source(id=doc.id, source=meta["source"], page=meta["page"], category=meta["category"], text=doc.page_content)


def retrieved_chunks(messages: list[BaseMessage]) -> dict[str, Document]:
    """Every chunk the search tool returned during one run, keyed by id (read from the tool artifacts)."""
    chunks = {}
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == "search_knowledge":
            for doc in message.artifact or []:
                chunks[doc.id] = doc
    return chunks


def search_queries(messages: list[BaseMessage]) -> list[str]:
    """The queries the agent chose to search for, in order."""
    return [
        call["args"]["query"]
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
        if call["name"] == "search_knowledge"
    ]


class AnswerService:
    def __init__(self, rag_agent):
        self.rag_agent = rag_agent

    def ask(self, question: str) -> AskResponse:
        result = self.rag_agent.invoke({"messages": [{"role": "user", "content": question}]})
        answer: CitedAnswer = result["structured_response"]
        messages = result["messages"]

        cited = {chunk_id for s in answer.sentences for chunk_id in s.citations}
        chunks = retrieved_chunks(messages)

        return AskResponse(
            question=question,
            found=answer.found,
            answer=" ".join(f"{s.sentence} [{', '.join(s.citations)}]" for s in answer.sentences),
            sentences=answer.sentences,
            sources=[to_source(doc) for chunk_id, doc in chunks.items() if chunk_id in cited],
            searches=search_queries(messages),
        )