import os
from datetime import timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlmodel import Session, select

from .database import get_session
from .models import Agent, utcnow

# ของจริงต้องตั้ง SECRET_KEY ผ่าน environment variable เสมอ
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-before-deploying")
ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=8)

password_hasher = PasswordHash.recommended()  # Argon2
bearer_scheme = HTTPBearer(auto_error=False)

UNAUTHORIZED = HTTPException(
    status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"}
)


def create_agent(session: Session, *, email: str, name: str, password: str) -> Agent:
    agent = Agent(email=email.lower(), name=name, password_hash=password_hasher.hash(password))
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


def authenticate(session: Session, email: str, password: str) -> Agent | None:
    agent = session.exec(select(Agent).where(Agent.email == email.lower())).first()
    if agent and password_hasher.verify(password, agent.password_hash):
        return agent
    return None


def create_access_token(agent: Agent) -> str:
    payload = {"sub": str(agent.id), "exp": utcnow() + TOKEN_TTL}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_optional_agent(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> Agent | None:
    """ไม่มี token = ลูกค้า (None) / token ถูกต้อง = เจ้าหน้าที่ / token ปลอมหรือหมดอายุ = 401"""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        agent = session.get(Agent, int(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise UNAUTHORIZED
    if agent is None:
        raise UNAUTHORIZED
    return agent


def get_current_agent(agent: Annotated[Agent | None, Depends(get_optional_agent)]) -> Agent:
    """ใช้กับ endpoint ที่เจ้าหน้าที่เท่านั้นเข้าได้"""
    if agent is None:
        raise UNAUTHORIZED
    return agent


CurrentAgent = Annotated[Agent, Depends(get_current_agent)]
OptionalAgent = Annotated[Agent | None, Depends(get_optional_agent)]
