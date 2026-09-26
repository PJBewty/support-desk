import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from support_desk.database import get_session
from support_desk.main import app

AGENT_PASSWORD = "correct-horse-battery"


@pytest.fixture
def engine():
    # ใช้ SQLite ในหน่วยความจำ เทสแต่ละครั้งได้ DB ใหม่ ไม่ปนกับข้อมูลจริง
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine):
    """client ของลูกค้า (ไม่ได้ล็อกอิน)"""

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_agent(session, email="nun@example.com", name="Nun"):
    from support_desk.security import create_agent

    return create_agent(session, email=email, name=name, password=AGENT_PASSWORD)


def login(client, email):
    res = client.post("/auth/login", json={"email": email, "password": AGENT_PASSWORD})
    assert res.status_code == 200, res.json()
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def agent(session):
    return make_agent(session)


@pytest.fixture
def agent_client(client, agent):
    """client ของเจ้าหน้าที่ที่ล็อกอินแล้ว"""
    return TestClient(app, headers=login(client, agent.email))


def new_ticket(client, **overrides):
    payload = {
        "title": "Cannot login",
        "description": "I forgot my password",
        "customer_email": "alice@example.com",
        **overrides,
    }
    return client.post("/tickets", json=payload)


# เส้นทางที่ถูกกฎจาก open ไปยังแต่ละสถานะ
PATH_TO = {
    "open": [],
    "in_progress": ["in_progress"],
    "resolved": ["in_progress", "resolved"],
    "closed": ["in_progress", "resolved", "closed"],
}


def move_to(client, ticket_id, status):
    """พา ticket ไปยังสถานะที่ต้องการ โดยเดินตามเส้นทางที่ถูกกฎ"""
    for step in PATH_TO[status]:
        res = client.patch(f"/tickets/{ticket_id}", json={"status": step})
        assert res.status_code == 200, res.json()
