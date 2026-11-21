from agrivibe.dependencies import get_chat_service
from agrivibe.main import app
from agrivibe.service.chatting import ChatService


class RecordingObservability:
    """Stands in for Langfuse: remembers the feedback it was given."""

    def __init__(self):
        self.scores = []

    def feedback(self, trace_id, positive, comment=None):
        self.scores.append((trace_id, positive, comment))


def test_feedback_is_stored_on_the_trace(client):
    observability = RecordingObservability()
    app.dependency_overrides[get_chat_service] = lambda: ChatService(
        None, None, observability=observability
    )  # type: ignore[arg-type]

    response = client.post(
        "/feedback",
        json={"trace_id": "abc123", "positive": False, "comment": "Wrong field"},
    )

    assert response.status_code == 204
    assert observability.scores == [("abc123", False, "Wrong field")]


def test_feedback_without_langfuse_is_refused(client):
    app.dependency_overrides[get_chat_service] = lambda: ChatService(None, None)  # type: ignore[arg-type]

    response = client.post("/feedback", json={"trace_id": "abc123", "positive": True})

    assert response.status_code == 503


def test_feedback_needs_a_trace_id(client):
    app.dependency_overrides[get_chat_service] = lambda: ChatService(None, None)  # type: ignore[arg-type]

    assert (
        client.post("/feedback", json={"trace_id": "", "positive": True}).status_code
        == 422
    )
