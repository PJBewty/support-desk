import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from support_desk.database import get_session
from support_desk.main import app


@pytest.fixture
def client():
    # ใช้ SQLite ในหน่วยความจำ เทสแต่ละครั้งได้ DB ใหม่ ไม่ปนกับข้อมูลจริง
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def new_ticket(client, **overrides):
    payload = {
        "title": "Cannot login",
        "description": "I forgot my password",
        "customer_email": "alice@example.com",
        **overrides,
    }
    return client.post("/tickets", json=payload)
