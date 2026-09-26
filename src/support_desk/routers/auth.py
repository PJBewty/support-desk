from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..database import SessionDep
from ..models import Agent, AgentRead, LoginRequest, Token
from ..security import CurrentAgent, authenticate, create_access_token

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=Token)
def login(data: LoginRequest, session: SessionDep):
    agent = authenticate(session, data.email, data.password)
    if not agent:
        # ไม่บอกว่าผิดที่อีเมลหรือรหัสผ่าน กันคนเดาว่าอีเมลไหนมีในระบบ
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return Token(access_token=create_access_token(agent))


@router.get("/auth/me", response_model=AgentRead)
def me(agent: CurrentAgent):
    return agent


@router.get("/agents", response_model=list[AgentRead])
def list_agents(session: SessionDep, agent: CurrentAgent):
    return session.exec(select(Agent).order_by(Agent.name)).all()
