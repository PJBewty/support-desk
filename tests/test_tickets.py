from conftest import move_to, new_ticket


def test_create_ticket_defaults_to_open(client):
    res = new_ticket(client)
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == 1
    assert body["status"] == "open"
    assert body["priority"] == "medium"


def test_create_ticket_rejects_bad_email(client):
    assert new_ticket(client, customer_email="not-an-email").status_code == 422


def test_get_missing_ticket_returns_404(client):
    assert client.get("/tickets/999").status_code == 404


def test_list_filters_by_status(agent_client):
    new_ticket(agent_client)
    second = new_ticket(agent_client, title="Refund please").json()
    move_to(agent_client, second["id"], "resolved")

    resolved = agent_client.get("/tickets", params={"status": "resolved"}).json()
    assert [t["title"] for t in resolved] == ["Refund please"]


def test_patch_only_changes_sent_fields(agent_client):
    ticket = new_ticket(agent_client).json()
    res = agent_client.patch(f"/tickets/{ticket['id']}", json={"priority": "high"})
    body = res.json()
    assert body["priority"] == "high"
    assert body["title"] == "Cannot login"
