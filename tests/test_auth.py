from conftest import AGENT_PASSWORD


def test_login_returns_bearer_token(client, agent):
    res = client.post("/auth/login", json={"email": agent.email, "password": AGENT_PASSWORD})

    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_returns_401(client, agent):
    res = client.post("/auth/login", json={"email": agent.email, "password": "wrong"})
    assert res.status_code == 401


def test_login_with_unknown_email_returns_401(client, agent):
    res = client.post("/auth/login", json={"email": "ghost@example.com", "password": AGENT_PASSWORD})
    assert res.status_code == 401


def test_password_is_not_stored_in_plain_text(agent):
    assert agent.password_hash != AGENT_PASSWORD
    assert AGENT_PASSWORD not in agent.password_hash


def test_me_returns_logged_in_agent_without_password(agent_client, agent):
    res = agent_client.get("/auth/me")

    assert res.status_code == 200
    assert res.json() == {"id": agent.id, "email": agent.email, "name": agent.name}


def test_me_without_token_returns_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_forged_token_returns_401(client):
    res = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401
