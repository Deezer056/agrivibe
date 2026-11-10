"""Talk to the orchestrator from the terminal, before /chat uses it.

Start FieldSat first, in your fieldsat-mcp-server repo:
    uv run --with tzdata fieldsat --transport http --port 8001

Then, in this repo:
    uv run python scripts/try_orchestrator.py "What is the urea rate for Bg 352?"
    uv run python scripts/try_orchestrator.py "Should I apply urea on my Minneriya field this week?"
"""

import asyncio
import sys

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from agrivibe.agents.advisory import build_advisory_agent
from agrivibe.agents.farm_context import build_farm_context_agent
from agrivibe.agents.fieldoracle.agent import build_fieldoracle_agent
from agrivibe.agents.orchestrator import build_orchestrator
from agrivibe.agents.orchestrator.memory import FarmerContext
from agrivibe.agents.weather import build_weather_agent
from agrivibe.config import Settings
from agrivibe.core.llm import create_chat_model
from agrivibe.core.mcp import load_fieldsat
from agrivibe.dependencies import get_reranker, get_vector_store


async def main(question):
    settings = Settings()  # pyright: ignore[reportCallIssue]
    model = create_chat_model(settings)
    fieldsat = await load_fieldsat(settings.fieldsat_url)
    knowledge_agent = build_fieldoracle_agent(
        model, get_vector_store(), k=settings.search_k, reranker=get_reranker()
    )
    orchestrator = build_orchestrator(
        model,
        fieldsat,
        weather_agent=build_weather_agent(model, fieldsat),
        farm_context_agent=build_farm_context_agent(model, fieldsat),
        knowledge_agent=knowledge_agent,
        advisory_agent=build_advisory_agent(model),
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    result = await orchestrator.ainvoke(
        {"messages": [{"role": "user", "content": question}]},
        {"configurable": {"thread_id": "try-1"}},
        context=FarmerContext(user_id="farmer-1"),
    )

    for message in result["messages"]:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                print("Orchestrator called:", call["name"], call["args"])
        if isinstance(message, ToolMessage):
            print("  returned:", message.name, message.status)
    print()
    print("Requirements:", result.get("requirements"))
    print("Findings from:", list((result.get("findings") or {}).keys()))
    print()
    print(result["messages"][-1].text)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))