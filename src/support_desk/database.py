import os

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///support.db")

# check_same_thread=False: SQLite ปกติห้ามใช้ connection ข้าม thread แต่ FastAPI ใช้หลาย thread
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency: เปิด session ต่อ 1 request แล้วปิดให้อัตโนมัติ"""
    with Session(engine) as session:
        yield session
