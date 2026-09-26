from fastapi.testclient import TestClient

from conftest import login, make_agent, new_ticket
from support_desk.main import app


def test_new_ticket_is_unassigned(client):
    assert new_ticket(client).json()["assignee_id"] is None


def test_agent_can_assign_ticket(client, agent_client, agent):
    ticket_id = new_ticket(client).json()["id"]

    res = agent_client.patch(f"/tickets/{ticket_id}", json={"assignee_id": agent.id})

    assert res.status_code == 200
    assert res.json()["assignee_id"] == agent.id


def test_agent_can_unassign_ticket(client, agent_client, agent):
    ticket_id = new_ticket(client).json()["id"]
    agent_client.patch(f"/tickets/{ticket_id}", json={"assignee_id": agent.id})

    res = agent_client.patch(f"/tickets/{ticket_id}", json={"assignee_id": None})

    assert res.json()["assignee_id"] is None


def test_assigning_to_unknown_agent_returns_422(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    res = agent_client.patch(f"/tickets/{ticket_id}", json={"assignee_id": 999})
    assert res.status_code == 422


def test_mine_filter_returns_only_my_tickets(client, session, agent_client, agent):
    other = make_agent(session, email="bee@example.com", name="Bee")
    mine = new_ticket(client, title="Mine").json()["id"]
    theirs = new_ticket(client, title="Theirs").json()["id"]
    new_ticket(client, title="Nobody's")
    agent_client.patch(f"/tickets/{mine}", json={"assignee_id": agent.id})
    agent_client.patch(f"/tickets/{theirs}", json={"assignee_id": other.id})

    res = agent_client.get("/tickets", params={"mine": True})

    assert [t["title"] for t in res.json()] == ["Mine"]


def test_mine_filter_depends_on_who_is_logged_in(client, session, agent_client, agent):
    other = make_agent(session, email="bee@example.com", name="Bee")
    ticket_id = new_ticket(client).json()["id"]
    agent_client.patch(f"/tickets/{ticket_id}", json={"assignee_id": agent.id})

    other_client = TestClient(app, headers=login(client, other.email))

    assert other_client.get("/tickets", params={"mine": True}).json() == []


def test_agent_can_list_all_agents(agent_client, session, agent):
    make_agent(session, email="bee@example.com", name="Bee")

    res = agent_client.get("/agents")

    assert res.status_code == 200
    assert [a["name"] for a in res.json()] == ["Bee", "Nun"]
    assert "password_hash" not in res.json()[0]


def test_listing_agents_requires_login(client):
    assert client.get("/agents").status_code == 401
