from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select

from ..database import SessionDep
from ..models import Agent, Ticket, TicketCreate, TicketRead, TicketStatus, TicketUpdate, can_change_status, utcnow
from ..security import CurrentAgent

router = APIRouter(tags=["tickets"])


def get_ticket_or_404(session: Session, ticket_id: int) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/tickets", response_model=TicketRead, status_code=201)
def create_ticket(data: TicketCreate, session: SessionDep):
    ticket = Ticket.model_validate(data)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)  # ดึง id ที่ DB สร้างให้กลับมา
    return ticket


@router.get("/tickets", response_model=list[TicketRead])
def list_tickets(
    session: SessionDep,
    agent: CurrentAgent,
    status: TicketStatus | None = None,
    mine: bool = False,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 20,
):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    if mine:
        query = query.where(Ticket.assignee_id == agent.id)
    return session.exec(query.offset(offset).limit(limit)).all()


@router.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, session: SessionDep):
    return get_ticket_or_404(session, ticket_id)


@router.patch("/tickets/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, data: TicketUpdate, session: SessionDep, agent: CurrentAgent):
    ticket = get_ticket_or_404(session, ticket_id)
    if data.status and not can_change_status(ticket.status, data.status):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot change status from {ticket.status.value} to {data.status.value}",
        )
    if data.assignee_id is not None and not session.get(Agent, data.assignee_id):
        raise HTTPException(status_code=422, detail="Agent not found")
    # exclude_unset: อัปเดตเฉพาะ field ที่ client ส่งมาจริง ๆ
    ticket.sqlmodel_update(data.model_dump(exclude_unset=True))
    ticket.updated_at = utcnow()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
