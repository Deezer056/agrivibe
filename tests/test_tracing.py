import re

from langchain_core.callbacks import BaseCallbackHandler
from langfuse import Langfuse

from agrivibe.config import Settings
from agrivibe.core.tracing import (
    PHONE_MASK,
    Observability,
    create_observability,
    mask_phones,
    run_config,
)
from agrivibe.dependencies import get_chat_service, get_thread_service
from agrivibe.main import app
from agrivibe.service.chatting import ChatService
from tests.test_chat import FIELD_STATE, as_farmer, chat, use_orchestrator


class RecordingTracer(BaseCallbackHandler):
    """Stands in for Langfuse's handler: records every run it is told about."""

    def __init__(self):
        self.runs = []

    def on_chain_start(self, serialized, inputs, *, metadata=None, **kwargs):
        self.runs.append((kwargs.get("name"), metadata or {}))

    def on_chat_model_start(self, serialized, messages, *, metadata=None, **kwargs):
        self.runs.append(("chat model", metadata or {}))


def test_no_langfuse_keys_means_no_tracing():
    # _env_file=None: ignore a local .env that has the keys.
    assert create_observability(Settings(_env_file=None)) is None  # pyright: ignore[reportCallIssue]


def test_run_config_without_a_tracer_only_names_the_thread():
    assert run_config("chat", "t-1", None, "frm_1") == {"configurable": {"thread_id": "t-1"}, "run_name": "chat"}


def test_run_config_groups_a_turn_by_thread_farmer_and_tags():
    tracer = RecordingTracer()

    config = run_config("chat", "t-1", tracer, "frm_1", ["demo"])

    assert config["callbacks"] == [tracer]
    assert config["metadata"] == {"langfuse_session_id": "t-1", "langfuse_user_id": "frm_1", "langfuse_tags": ["demo"]}


def test_one_chat_is_one_trace_with_the_farmer_and_the_thread(client, vector_store):
    agent, _ = use_orchestrator(vector_store, **FIELD_STATE)  # skips without TEST_DATABASE_URL
    tracer = RecordingTracer()
    threads = app.dependency_overrides[get_thread_service]()
    app.dependency_overrides[get_chat_service] = lambda: ChatService(agent, threads, tracer=tracer)
    as_farmer("frm_traced")

    body = chat(client, "Is my Minneriya field stressed?")

    names = [name for name, _ in tracer.runs]
    assert names[0] == "orchestrator"
    # The specialists run inside their tools, so their model calls reach the same tracer.
    assert names.count("chat model") == 7
    for _, metadata in tracer.runs:
        assert metadata["langfuse_session_id"] == body["thread_id"]
        assert metadata["langfuse_user_id"] == "frm_traced"


def test_phone_numbers_are_masked_however_deeply_nested():
    data = {"messages": [{"content": "Call me on 077 123 4567 or +94 11 234 5678"}], "field": "SL-PADDY-MINNERIYA"}

    assert mask_phones(data=data) == {
        "messages": [{"content": f"Call me on {PHONE_MASK} or {PHONE_MASK}"}],
        "field": "SL-PADDY-MINNERIYA",
    }


def test_numbers_that_are_not_phones_are_kept():
    text = "Apply 50 kg/ha of urea; 112 mm of rain in 7 days; field SL-PADDY-MINNERIYA, 2026-11-19"

    assert mask_phones(data=text) == text


def test_each_turn_is_its_own_trace():
    # tracing_enabled=False: the real client and spans, nothing sent over the network.
    client = Langfuse(public_key="pk-lf-test", secret_key="sk-lf-test", tracing_enabled=False)
    observability = Observability(client, "pk-lf-test")

    with observability.turn(message="Hi", farmer_id="frm_1", thread_id="t-1") as first:
        first.finish("Hello", {"tools_called": []})
    with observability.turn(message="Hi again", farmer_id="frm_1", thread_id="t-1") as second:
        pass

    assert re.fullmatch(r"[0-9a-f]{32}", first.trace_id)
    assert first.trace_id != second.trace_id
