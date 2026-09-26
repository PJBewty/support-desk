from conftest import new_ticket


def reply(client, ticket_id, role="agent", body="We are checking this"):
    return client.post(
        f"/tickets/{ticket_id}/comments",
        json={"author_role": role, "author_name": "Bob", "body": body},
    )


def test_conversation_is_listed_in_order(client):
    ticket_id = new_ticket(client).json()["id"]
    reply(client, ticket_id, role="agent", body="Please try resetting")
    reply(client, ticket_id, role="customer", body="It worked, thanks!")

    comments = client.get(f"/tickets/{ticket_id}/comments").json()
    assert [(c["author_role"], c["body"]) for c in comments] == [
        ("agent", "Please try resetting"),
        ("customer", "It worked, thanks!"),
    ]


def test_comment_on_missing_ticket_returns_404(client):
    assert reply(client, 999).status_code == 404


def test_cannot_comment_on_closed_ticket(client):
    ticket_id = new_ticket(client).json()["id"]
    client.patch(f"/tickets/{ticket_id}", json={"status": "closed"})
    assert reply(client, ticket_id).status_code == 409


def test_invalid_role_is_rejected(client):
    ticket_id = new_ticket(client).json()["id"]
    assert reply(client, ticket_id, role="hacker").status_code == 422
