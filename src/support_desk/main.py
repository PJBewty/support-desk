from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import create_db_and_tables
from .routers import auth, comments, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # สร้างตารางตอนเปิดเซิร์ฟเวอร์
    yield


app = FastAPI(title="Support Desk", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(comments.router)

# หน้าเว็บ: ต้อง mount ไว้ท้ายสุด ไม่งั้นจะไปทับเส้นทาง API ข้างบน
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
