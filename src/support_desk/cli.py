"""สร้างบัญชีเจ้าหน้าที่: uv run create-agent EMAIL "ชื่อ" """
import argparse
import getpass
import sys

from sqlmodel import Session, select

from .models import Agent
from .security import create_agent

MIN_PASSWORD_LENGTH = 8


def run(argv, session: Session, read_password=getpass.getpass) -> Agent:
    parser = argparse.ArgumentParser(prog="create-agent", description="สร้างบัญชีเจ้าหน้าที่")
    parser.add_argument("email")
    parser.add_argument("name")
    args = parser.parse_args(argv)

    if session.exec(select(Agent).where(Agent.email == args.email.lower())).first():
        sys.exit(f"มีบัญชี {args.email} อยู่แล้ว")

    password = read_password("รหัสผ่าน: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"รหัสผ่านต้องยาวอย่างน้อย {MIN_PASSWORD_LENGTH} ตัวอักษร")
    if read_password("ยืนยันรหัสผ่าน: ") != password:
        sys.exit("รหัสผ่านสองครั้งไม่ตรงกัน")

    agent = create_agent(session, email=args.email, name=args.name, password=password)
    print(f"สร้างบัญชี {agent.name} <{agent.email}> เรียบร้อย")
    return agent


def main() -> None:
    from .database import create_db_and_tables, engine

    create_db_and_tables()
    with Session(engine) as session:
        run(sys.argv[1:], session)
