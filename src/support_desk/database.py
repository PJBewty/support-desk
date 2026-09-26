import os
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from . import models  # noqa: F401  ต้อง import ให้ตารางลงทะเบียนก่อน create_all

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///support.db")

# check_same_thread=False: SQLite ปกติห้ามใช้ connection ข้าม thread แต่ FastAPI ใช้หลาย thread
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency: เปิด session ต่อ 1 request แล้วปิดให้อัตโนมัติ"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
