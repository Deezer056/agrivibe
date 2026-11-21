import time
from contextlib import nullcontext
from datetime import UTC, datetime
from uuid import uuid4

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from agrivibe.agents.orchestrator.memory import FarmerContext
from agrivibe.core.tracing import Observability, run_config
from agrivibe.models.chat import ChatResponse, Turn
from agrivibe.service.threads import ThreadService


def current_turn(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Drops the earlier turns of a thread, keeping the latest message onwards.

    Args:
        messages: The thread's full message history after a run.

    Returns:
        The messages from the last user message to the end.
    """
    starts = [i for i, message in enumerate(messages) if isinstance(message, HumanMessage)]
    return messages[starts[-1]:] if starts else messages


def tools_called(messages: list[BaseMessage]) -> list[str]:
    """Lists the tools the orchestrator called, in order.

    Args:
        messages: The orchestrator's messages for one turn.

    Returns:
        The tool names. A specialist's own tool calls are not here: they stay inside
        the specialist's run.
    """
    return [call["name"] for message in messages if isinstance(message, AIMessage) for call in message.tool_calls]


class ChatService:
    """Runs the farmer's messages through the orchestrator and records each turn."""

    def __init__(
        self,
        orchestrator,
        threads: ThreadService,
        tracer: BaseCallbackHandler | None = None,
        observability: Observability | None = None,
        tags: list[str] | None = None,
    ):
        """Initializes the service.

        Args:
            orchestrator: The agent built by `build_orchestrator`.
            threads: Records each turn and checks that a thread is the farmer's.
            tracer: A callback handler to trace with, or None. Tests pass a recording one.
            observability: Langfuse, one trace per turn with a known id. Takes precedence over `tracer`.
            tags: Tags for every trace.
        """
        self.orchestrator = orchestrator
        self.threads = threads
        self.tracer = tracer
        self.observability = observability
        self.tags = tags or []

    async def chat(self, message: str, farmer_id: str, thread_id: str | None = None) -> ChatResponse:
        """Sends one message to the orchestrator, records the turn and returns it.

        Args:
            message: What the farmer wrote.
            farmer_id: Who wrote it, as decided by the server. Keys the farmer's threads and memory.
            thread_id: One of the farmer's conversations to continue. A new one is started when empty.

        Returns:
            The reply, the tools the orchestrator called for it, the saved requirements and
            the specialists' findings.

        Raises:
            ThreadNotFound: thread_id is not one of this farmer's conversations.
        """
        if thread_id:
            await self.threads.summary(farmer_id, thread_id)  # someone else's thread is never continued
        else:
            thread_id = str(uuid4())

        traced_turn = (
            self.observability.turn(message=message, farmer_id=farmer_id, thread_id=thread_id, tags=self.tags)
            if self.observability is not None
            else nullcontext()
        )
        with traced_turn as traced:
            started_at, started = datetime.now(UTC), time.monotonic()
            result = await self.orchestrator.ainvoke(
                # The empty findings clear the last question's evidence (see merge_findings).
                {"messages": [{"role": "user", "content": message}], "findings": {}},
                run_config("orchestrator", thread_id, traced.handler if traced else self.tracer, farmer_id, self.tags),
                context=FarmerContext(user_id=farmer_id),
            )
            turn = Turn(
                message=message,
                answer=result["messages"][-1].text,
                tools_called=tools_called(current_turn(result["messages"])),
                requirements=result.get("requirements"),
                findings=result["findings"],
                started_at=started_at,
                seconds=round(time.monotonic() - started, 1),
            )
            if traced:
                traced.finish(
                    turn.answer,
                    {
                        "tools_called": turn.tools_called,
                        "field_id": (turn.requirements or {}).get("field_id"),
                        "specialists": sorted(turn.findings),
                        "seconds": turn.seconds,
                    },
                )
        await self.threads.record_turn(farmer_id, thread_id, turn)
        trace_id = traced.trace_id if traced else None
        return ChatResponse(**turn.model_dump(), thread_id=thread_id, trace_id=trace_id)
