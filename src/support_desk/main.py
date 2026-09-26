from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import (
    Comment,
    CommentCreate,
    CommentRead,
    Ticket,
    TicketCreate,
    TicketRead,
    TicketStatus,
    TicketUpdate,
    utcnow,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # สร้างตารางตอนเปิดเซิร์ฟเวอร์
    yield


app = FastAPI(title="Support Desk", lifespan=lifespan)

SessionDep = Annotated[Session, Depends(get_session)]


def get_ticket_or_404(session: Session, ticket_id: int) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/tickets", response_model=TicketRead, status_code=201)
def create_ticket(data: TicketCreate, session: SessionDep):
    ticket = Ticket.model_validate(data)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)  # ดึง id ที่ DB สร้างให้กลับมา
    return ticket


@app.get("/tickets", response_model=list[TicketRead])
def list_tickets(
    session: SessionDep,
    status: TicketStatus | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 20,
):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    return session.exec(query.offset(offset).limit(limit)).all()


@app.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, session: SessionDep):
    return get_ticket_or_404(session, ticket_id)


@app.patch("/tickets/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, data: TicketUpdate, session: SessionDep):
    ticket = get_ticket_or_404(session, ticket_id)
    # exclude_unset: อัปเดตเฉพาะ field ที่ client ส่งมาจริง ๆ
    ticket.sqlmodel_update(data.model_dump(exclude_unset=True))
    ticket.updated_at = utcnow()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/comments", response_model=CommentRead, status_code=201)
def add_comment(ticket_id: int, data: CommentCreate, session: SessionDep):
    ticket = get_ticket_or_404(session, ticket_id)
    if ticket.status == TicketStatus.closed:
        # 409 Conflict: คำขอถูกต้อง แต่ขัดกับสถานะปัจจุบันของข้อมูล
        raise HTTPException(status_code=409, detail="Ticket is closed")

    comment = Comment.model_validate(data, update={"ticket_id": ticket_id})
    ticket.updated_at = utcnow()  # มีความเคลื่อนไหว = ticket ถูกอัปเดต
    session.add(comment)
    session.add(ticket)
    session.commit()
    session.refresh(comment)
    return comment


@app.get("/tickets/{ticket_id}/comments", response_model=list[CommentRead])
def list_comments(ticket_id: int, session: SessionDep):
    get_ticket_or_404(session, ticket_id)
    query = select(Comment).where(Comment.ticket_id == ticket_id).order_by(Comment.created_at)
    return session.exec(query).all()


# หน้าเว็บลูกค้า: ต้อง mount ไว้ท้ายสุด ไม่งั้นจะไปทับเส้นทาง API ข้างบน
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
