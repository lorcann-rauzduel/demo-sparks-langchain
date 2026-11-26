from fastapi.testclient import TestClient

from assistant.domain.answer import ActionToApprove
from assistant.entrypoints.web_api.app import create_app
from tests.entrypoints.stubs import assistant_answering

KEY = {"X-API-Key": "secret-key"}


def client_answering(text: str, action: ActionToApprove | None = None) -> TestClient:
    assistant, _ = assistant_answering(text, action)
    return TestClient(create_app(assistant, api_key="secret-key"))


def test_ask_returns_the_answer_and_its_sources() -> None:
    response = client_answering("Ten days.").post(
        "/ask", json={"user_id": "42", "question": "Notice?"}, headers=KEY
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "Ten days.", "sources": [], "actions_to_approve": []}


def test_a_request_without_the_right_key_is_refused() -> None:
    client = client_answering("unused")
    body = {"user_id": "42", "question": "Notice?"}

    assert client.post("/ask", json=body).status_code == 401
    assert client.post("/ask", json=body, headers={"X-API-Key": "wrong"}).status_code == 401


def test_an_action_to_approve_is_returned_then_decided() -> None:
    client = client_answering("Leave submitted.", ActionToApprove(("submit_leave_request(...)",)))

    asked = client.post("/ask", json={"user_id": "42", "question": "Book my leave"}, headers=KEY)
    decided = client.post("/decide", json={"user_id": "42", "approved": True}, headers=KEY)

    assert asked.json()["actions_to_approve"] == ["submit_leave_request(...)"]
    assert decided.json()["answer"] == "Leave submitted."
