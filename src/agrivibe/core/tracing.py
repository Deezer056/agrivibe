"""Langfuse tracing: one trace per chat turn, with a known id.

With no Langfuse keys in .env the app runs without tracing: the functions here return None.
Follows Langfuse's LangChain guide: https://langfuse.com/integrations/frameworks/langchain
and its trace best practices: https://langfuse.com/docs/observability/best-practices
"""

import re
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse, LangfuseSpan, propagate_attributes
from langfuse.langchain import CallbackHandler

from agrivibe.config import Settings
from agrivibe.core.guardrails import PHONE_PATTERN

TRACE_NAME = "chat"

PHONE = re.compile(PHONE_PATTERN)  # the same rule as the PII guardrail (core/guardrails.py)
PHONE_MASK = "<phone>"


def mask_phones(*, data: Any, **_: Any) -> Any:
    """Replaces phone numbers before anything is sent to Langfuse.

    Langfuse calls this on every input, output and metadata value. A farmer may type their
    number into a message; it is personal data the traces don't need.
    """
    if isinstance(data, str):
        return PHONE.sub(PHONE_MASK, data)
    if isinstance(data, dict):
        return {key: mask_phones(data=value) for key, value in data.items()}
    if isinstance(data, list | tuple):
        return type(data)(mask_phones(data=value) for value in data)
    return data


def create_langfuse(settings: Settings) -> Langfuse | None:
    """Creates the Langfuse client, or None when the Langfuse keys are not set.

    The keys are passed here because pydantic-settings reads `.env` without putting its values in
    the environment, where Langfuse would look for them. `environment` separates development traces
    from production ones.
    """
    if settings.langfuse_public_key is None or settings.langfuse_secret_key is None:
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key.get_secret_value(),
        base_url=settings.langfuse_base_url,
        environment=settings.langfuse_environment,
        mask=mask_phones,
    )


@dataclass
class TracedTurn:
    """One chat turn being traced: its id, the handler for the agents and the root observation."""

    trace_id: str
    handler: CallbackHandler
    root: LangfuseSpan

    def finish(self, answer: str, metadata: dict[str, Any]) -> None:
        """Sets the trace's output to the answer, so the tracing table reads like the chat."""
        self.root.update(output=answer, metadata=metadata)


class Observability:
    """One Langfuse trace per chat turn, with a known id.

    Knowing the trace id lets the API return it, so the frontend can later send 👍/👎 for that
    exact trace (Step 13), and lets the service attach scores to it (Step 12).
    """

    def __init__(self, client: Langfuse, public_key: str):
        self.client = client
        self.public_key = public_key

    @contextmanager
    def turn(
        self, *, message: str, farmer_id: str, thread_id: str, tags: list[str] | None = None
    ) -> Iterator[TracedTurn]:
        """Opens the trace for one chat turn.

        The root observation's input is the farmer's message, and `TracedTurn.finish` sets its
        output to the answer: Langfuse shows these as the trace's input and output. The agents'
        runs, recorded by the handler, nest under it. The thread is the session and the farmer
        the user, on every observation in the trace.
        """
        trace_id = self.client.create_trace_id()
        with (
            self.client.start_as_current_observation(
                trace_context={"trace_id": trace_id}, name=TRACE_NAME, as_type="span", input=message
            ) as root,
            propagate_attributes(user_id=farmer_id, session_id=thread_id, tags=tags, trace_name=TRACE_NAME),
        ):
            yield TracedTurn(trace_id, CallbackHandler(public_key=self.public_key), root)

    def feedback(self, trace_id: str, positive: bool, comment: str | None = None) -> None:
        """Stores a farmer's 👍/👎 on a trace as the `user_feedback` score."""
        self.client.create_score(
            trace_id=trace_id,
            name="user_feedback",
            value=1.0 if positive else 0.0,
            data_type="BOOLEAN",
            comment=comment,
        )

    def record_events(self, trace_id: str, events: list[tuple[str, str]]) -> None:
        """Turns the turn's guardrail events into scores: one categorical score per guardrail that fired,
        and a numeric `tool_errors` count on every trace (zero included, so the rate can be computed)."""
        counts = Counter(name for name, _ in events)
        self.client.create_score(trace_id=trace_id, name="tool_errors", value=float(counts.pop("tool_error", 0)))
        for name, detail in events:
            if name in counts:
                self.client.create_score(
                    trace_id=trace_id, name="guardrail", value=name, data_type="CATEGORICAL", comment=detail
                )

    def trace_url(self, trace_id: str) -> str | None:
        """The trace's page in the Langfuse UI."""
        return self.client.get_trace_url(trace_id=trace_id)


def create_observability(settings: Settings) -> Observability | None:
    """The Observability helper, or None when the Langfuse keys are not set."""
    client = create_langfuse(settings)
    if client is None or settings.langfuse_public_key is None:
        return None
    return Observability(client, settings.langfuse_public_key)


def run_config(
    name: str,
    thread_id: str,
    tracer: BaseCallbackHandler | None,
    user_id: str | None = None,
    tags: list[str] | None = None,
) -> RunnableConfig:
    """The config for one agent run: the thread to continue and, when tracing is on, Langfuse.

    Args:
        name: The trace's name in Langfuse, for example "chat".
        thread_id: The conversation. It is also the Langfuse session, so a chat's turns are grouped.
        tracer: A Langfuse handler, or None.
        user_id: The farmer, shown as the trace's user in Langfuse.
        tags: Trace tags to filter by in Langfuse.

    Returns:
        The config to pass to `invoke` or `ainvoke`.
    """
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}, "run_name": name}
    if tracer is not None:
        config["callbacks"] = [tracer]
        config["metadata"] = {"langfuse_session_id": thread_id}
        if user_id:
            config["metadata"]["langfuse_user_id"] = user_id
        if tags:
            config["metadata"]["langfuse_tags"] = tags
    return config
