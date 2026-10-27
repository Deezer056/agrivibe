from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore

from agrivibe.agents.fieldoracle.prompts import SYSTEM_PROMPT
from agrivibe.agents.fieldoracle.schemas import CitedAnswer
from agrivibe.agents.fieldoracle.tools import make_search_tool


def build_fieldoracle_agent(model: BaseChatModel, vector_store: VectorStore, k: int = 20):
    return create_agent(
        model=model,
        tools=[make_search_tool(vector_store=vector_store, k=k)],
        system_prompt=SYSTEM_PROMPT,
        response_format=CitedAnswer,
        name="FieldOracle",
    )


if __name__ == "__main__":
    from agrivibe.config import Settings
    from agrivibe.core.llm import create_chat_model
    from agrivibe.db.vectorstore import create_vector_store

    settings = Settings()
    agent = build_fieldoracle_agent(create_chat_model(settings), create_vector_store(settings), k=5)
    result = agent.invoke({"messages": [{"role": "user", "content": "What is the best time to plant rice?"}]})
    print(result["structured_response"])