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


# สถานะปัจจุบัน -> สถานะที่เปลี่ยนไปได้
ALLOWED_TRANSITIONS = {
    TicketStatus.open: {TicketStatus.in_progress},
    TicketStatus.in_progress: {TicketStatus.resolved, TicketStatus.open},
    TicketStatus.resolved: {TicketStatus.closed, TicketStatus.in_progress},
    TicketStatus.closed: {TicketStatus.in_progress},  # เปิดเรื่องใหม่
}


def can_change_status(current: TicketStatus, target: TicketStatus) -> bool:
    return target == current or target in ALLOWED_TRANSITIONS[current]


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
    assignee_id: int | None = Field(default=None, foreign_key="agent.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class TicketCreate(TicketBase):
    """ข้อมูลที่ลูกค้าส่งมาตอนเปิด ticket (ลูกค้ากำหนด status/id เองไม่ได้)"""


class TicketRead(TicketBase):
    """ข้อมูลที่ API ส่งกลับ"""
    id: int
    status: TicketStatus
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime


class TicketUpdate(SQLModel):
    """ทุก field เป็น optional เพราะ PATCH แก้แค่บางส่วนได้"""
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    assignee_id: int | None = None  # ส่ง null = เลิก assign


# --- Comment: ข้อความตอบกลับใน ticket ---

class AuthorRole(str, Enum):
    customer = "customer"
    agent = "agent"


class CommentBase(SQLModel):
    body: str = Field(min_length=1)
    internal: bool = False  # True = โน้ตภายในทีม ลูกค้ามองไม่เห็น


class Comment(CommentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # foreign key: ผูก comment เข้ากับ ticket ที่มันอยู่
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    author_role: AuthorRole
    author_name: str
    created_at: datetime = Field(default_factory=utcnow)


class CommentCreate(CommentBase):
    """client ส่งมาแค่ข้อความ ส่วนผู้ส่งเซิร์ฟเวอร์ดูจาก token เอง (กันปลอมตัว)"""


class CommentRead(CommentBase):
    id: int
    ticket_id: int
    author_role: AuthorRole
    author_name: str
    created_at: datetime


# --- Agent: บัญชีเจ้าหน้าที่ ---

class Agent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    password_hash: str  # เก็บแค่ hash ไม่เก็บรหัสผ่านจริง
    created_at: datetime = Field(default_factory=utcnow)


class AgentRead(SQLModel):
    """ข้อมูลเจ้าหน้าที่ที่ส่งออกได้ (ไม่มี password_hash)"""
    id: int
    email: str
    name: str


class LoginRequest(SQLModel):
    email: str
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
