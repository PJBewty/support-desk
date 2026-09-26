from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..database import SessionDep
from ..models import AuthorRole, Comment, CommentCreate, CommentRead, TicketStatus, utcnow
from ..security import OptionalAgent
from .tickets import get_ticket_or_404

router = APIRouter(tags=["comments"])


@router.post("/tickets/{ticket_id}/comments", response_model=CommentRead, status_code=201)
def add_comment(ticket_id: int, data: CommentCreate, session: SessionDep, agent: OptionalAgent):
    ticket = get_ticket_or_404(session, ticket_id)
    if data.internal and not agent:
        raise HTTPException(status_code=403, detail="Only agents can post internal notes")
    if ticket.status == TicketStatus.closed and not data.internal:
        # 409 Conflict: คำขอถูกต้อง แต่ขัดกับสถานะปัจจุบันของข้อมูล
        raise HTTPException(status_code=409, detail="Ticket is closed")

    if agent:
        author = {"author_role": AuthorRole.agent, "author_name": agent.name}
    else:
        author = {"author_role": AuthorRole.customer, "author_name": ticket.customer_email}
    comment = Comment.model_validate(data, update={"ticket_id": ticket_id, **author})
    # ลูกค้าตอบกลับเรื่องที่แก้ไขแล้ว = ปัญหายังไม่จบ เปิดเรื่องกลับมา
    if not agent and ticket.status == TicketStatus.resolved:
        ticket.status = TicketStatus.in_progress
    ticket.updated_at = utcnow()  # มีความเคลื่อนไหว = ticket ถูกอัปเดต
    session.add(comment)
    session.add(ticket)
    session.commit()
    session.refresh(comment)
    return comment


@router.get("/tickets/{ticket_id}/comments", response_model=list[CommentRead])
def list_comments(ticket_id: int, session: SessionDep, agent: OptionalAgent):
    get_ticket_or_404(session, ticket_id)
    query = select(Comment).where(Comment.ticket_id == ticket_id).order_by(Comment.created_at)
    if not agent:
        query = query.where(Comment.internal == False)  # noqa: E712 (SQL ต้องใช้ ==)
    return session.exec(query).all()
