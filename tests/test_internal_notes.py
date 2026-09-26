from conftest import move_to, new_ticket


def post(client, ticket_id, body, **extra):
    return client.post(f"/tickets/{ticket_id}/comments", json={"body": body, **extra})


def bodies(client, ticket_id):
    return [c["body"] for c in client.get(f"/tickets/{ticket_id}/comments").json()]


def test_replies_are_public_by_default(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    assert post(agent_client, ticket_id, "Hello").json()["internal"] is False


def test_agent_can_add_internal_note(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    res = post(agent_client, ticket_id, "VIP customer", internal=True)
    assert res.status_code == 201
    assert res.json()["internal"] is True


def test_customer_cannot_see_internal_notes(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    post(agent_client, ticket_id, "Public reply")
    post(agent_client, ticket_id, "Refund approved by finance", internal=True)

    assert bodies(client, ticket_id) == ["Public reply"]


def test_agent_sees_internal_notes(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    post(agent_client, ticket_id, "Public reply")
    post(agent_client, ticket_id, "Refund approved by finance", internal=True)

    assert bodies(agent_client, ticket_id) == ["Public reply", "Refund approved by finance"]


def test_customer_cannot_post_internal_note(client):
    ticket_id = new_ticket(client).json()["id"]
    res = post(client, ticket_id, "Sneaky", internal=True)
    assert res.status_code == 403


def test_internal_note_allowed_on_closed_ticket(client, agent_client):
    ticket_id = new_ticket(client).json()["id"]
    move_to(agent_client, ticket_id, "closed")
    res = post(agent_client, ticket_id, "Customer called again by phone", internal=True)
    assert res.status_code == 201
