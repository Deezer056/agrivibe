"""Ask FieldOracle a question with FieldSat's live tools loaded over MCP."""

import asyncio
import warnings

from langchain_core._api import LangChainBetaWarning

warnings.filterwarnings("ignore", category=LangChainBetaWarning)

from langchain.mcp import MCPAdapter  # noqa: E402

from agrivibe.agents.fieldoracle.agent import build_fieldoracle_agent  # noqa: E402
from agrivibe.config import Settings  # noqa: E402
from agrivibe.core.llm import create_chat_model  # noqa: E402
from agrivibe.db.vectorstore import create_vector_store  # noqa: E402

QUESTION = "Is this a good week to apply urea in Minneriya?"


async def main() -> None:
    settings = Settings()
    async with MCPAdapter(settings.fieldsat_url) as adapter:
        mcp_tools = await adapter.list_tools()
    print("FieldSat tools:", [t.name for t in mcp_tools])

    agent = build_fieldoracle_agent(
        create_chat_model(settings), create_vector_store(settings), k=settings.search_k, extra_tools=mcp_tools
    )
    # MCP tools are async-only, so the agent must run with ainvoke.
    result = await agent.ainvoke({"messages": [{"role": "user", "content": QUESTION}]})

    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []) or []:
            print("tool call:", call["name"], call["args"])
    answer = result["structured_response"]
    print("found:", answer.found)
    for s in answer.sentences:
        print("-", s.sentence, s.citations)


if __name__ == "__main__":
    asyncio.run(main())