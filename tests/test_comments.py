from conftest import move_to, new_ticket


def reply(client, ticket_id, body="We are checking this", **extra):
    return client.post(f"/tickets/{ticket_id}/comments", json={"body": body, **extra})


def test_conversation_is_listed_in_order(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    reply(agent_client, ticket_id, body="Please try resetting")
    reply(client, ticket_id, body="It worked, thanks!")

    comments = client.get(f"/tickets/{ticket_id}/comments").json()
    assert [(c["author_role"], c["body"]) for c in comments] == [
        ("agent", "Please try resetting"),
        ("customer", "It worked, thanks!"),
    ]


def test_agent_reply_uses_logged_in_agent_name(client, agent_client, agent):
    ticket_id = new_ticket(client).json()["id"]
    body = reply(agent_client, ticket_id).json()
    assert body["author_role"] == "agent"
    assert body["author_name"] == agent.name


def test_customer_reply_uses_ticket_email_as_name(client):
    ticket_id = new_ticket(client, customer_email="bob@example.com").json()["id"]
    body = reply(client, ticket_id).json()
    assert body["author_role"] == "customer"
    assert body["author_name"] == "bob@example.com"


def test_customer_cannot_pretend_to_be_agent(client):
    ticket_id = new_ticket(client).json()["id"]
    body = reply(client, ticket_id, author_role="agent", author_name="Boss").json()
    assert body["author_role"] == "customer"
    assert body["author_name"] == "alice@example.com"


def test_comment_on_missing_ticket_returns_404(client):
    assert reply(client, 999).status_code == 404


def test_cannot_comment_on_closed_ticket(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    move_to(agent_client, ticket_id, "closed")
    assert reply(client, ticket_id).status_code == 409


def test_customer_reply_reopens_resolved_ticket(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    move_to(agent_client, ticket_id, "resolved")

    reply(client, ticket_id, body="Still broken")

    assert client.get(f"/tickets/{ticket_id}").json()["status"] == "in_progress"


def test_agent_reply_keeps_resolved_ticket_resolved(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    move_to(agent_client, ticket_id, "resolved")

    reply(agent_client, ticket_id, body="Glad it's fixed!")

    assert client.get(f"/tickets/{ticket_id}").json()["status"] == "resolved"
