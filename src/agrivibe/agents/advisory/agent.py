from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel

from agrivibe.agents.advisory.prompts import SYSTEM_PROMPT


def build_advisory_agent(model: BaseChatModel, guardrails=()):
    """Builds the Advisory Agent: one grounded recommendation from the other agents' evidence.

    It has no tools. Everything it may use arrives in the message, taken from central memory.
    Its last message is the recommendation.

    Args:
        model: The chat model that writes the recommendation.
        guardrails: Middleware on its answer, such as the dose range check.
    """
    return create_agent(
        model, tools=[], system_prompt=SYSTEM_PROMPT, middleware=list(guardrails), name="advisory_agent"
    )
