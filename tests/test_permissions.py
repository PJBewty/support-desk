from conftest import new_ticket


# --- เจ้าหน้าที่เท่านั้น ---

def test_listing_tickets_requires_login(client):
    assert client.get("/tickets").status_code == 401


def test_agent_can_list_tickets(agent_client, client):
    new_ticket(client)
    res = agent_client.get("/tickets")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_updating_ticket_requires_login(client):
    ticket_id = new_ticket(client).json()["id"]
    res = client.patch(f"/tickets/{ticket_id}", json={"status": "in_progress"})
    assert res.status_code == 401


# --- ลูกค้าใช้ได้โดยไม่ต้องล็อกอิน ---

def test_customer_can_open_ticket_without_login(client):
    assert new_ticket(client).status_code == 201


def test_customer_can_view_ticket_by_id_without_login(client):
    ticket_id = new_ticket(client).json()["id"]
    assert client.get(f"/tickets/{ticket_id}").status_code == 200
