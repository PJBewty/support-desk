import pytest

from conftest import move_to, new_ticket

ALLOWED = [
    ("open", "in_progress"),
    ("in_progress", "resolved"),
    ("in_progress", "open"),
    ("resolved", "closed"),
    ("resolved", "in_progress"),
    ("closed", "in_progress"),
]

FORBIDDEN = [
    ("open", "resolved"),
    ("open", "closed"),
    ("in_progress", "closed"),
    ("resolved", "open"),
    ("closed", "open"),
    ("closed", "resolved"),
]


@pytest.mark.parametrize("current, target", ALLOWED)
def test_allowed_transition_succeeds(agent_client, current, target):
    ticket_id = new_ticket(agent_client).json()["id"]
    move_to(agent_client, ticket_id, current)

    res = agent_client.patch(f"/tickets/{ticket_id}", json={"status": target})

    assert res.status_code == 200
    assert res.json()["status"] == target


@pytest.mark.parametrize("current, target", FORBIDDEN)
def test_forbidden_transition_returns_409(agent_client, current, target):
    ticket_id = new_ticket(agent_client).json()["id"]
    move_to(agent_client, ticket_id, current)

    res = agent_client.patch(f"/tickets/{ticket_id}", json={"status": target})

    assert res.status_code == 409
    assert res.json()["detail"] == f"Cannot change status from {current} to {target}"


def test_forbidden_transition_keeps_ticket_unchanged(agent_client):
    ticket_id = new_ticket(agent_client).json()["id"]

    agent_client.patch(f"/tickets/{ticket_id}", json={"status": "closed", "priority": "high"})

    ticket = agent_client.get(f"/tickets/{ticket_id}").json()
    assert ticket["status"] == "open"
    assert ticket["priority"] == "medium"


def test_same_status_is_allowed(agent_client):
    ticket_id = new_ticket(agent_client).json()["id"]
    res = agent_client.patch(f"/tickets/{ticket_id}", json={"status": "open"})
    assert res.status_code == 200
