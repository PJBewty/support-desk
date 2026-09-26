from datetime import datetime, timezone
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# --- Schemas: แยกตามหน้าที่ ว่าข้อมูลไหน "รับเข้า" / "ส่งออก" / "แก้ไขได้" ---

class TicketBase(SQLModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1)
    customer_email: EmailStr
    priority: TicketPriority = TicketPriority.medium


class Ticket(TicketBase, table=True):
    """ตารางจริงในฐานข้อมูล"""
    id: int | None = Field(default=None, primary_key=True)
    customer_email: str = Field(index=True)
    status: TicketStatus = Field(default=TicketStatus.open, index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class TicketCreate(TicketBase):
    """ข้อมูลที่ลูกค้าส่งมาตอนเปิด ticket (ลูกค้ากำหนด status/id เองไม่ได้)"""


class TicketRead(TicketBase):
    """ข้อมูลที่ API ส่งกลับ"""
    id: int
    status: TicketStatus
    created_at: datetime
    updated_at: datetime


class TicketUpdate(SQLModel):
    """ทุก field เป็น optional เพราะ PATCH แก้แค่บางส่วนได้"""
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None


# --- Comment: ข้อความตอบกลับใน ticket ---

class AuthorRole(str, Enum):
    customer = "customer"
    agent = "agent"


class CommentBase(SQLModel):
    author_role: AuthorRole
    author_name: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1)


class Comment(CommentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # foreign key: ผูก comment เข้ากับ ticket ที่มันอยู่
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class CommentCreate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int
    ticket_id: int
    created_at: datetime
