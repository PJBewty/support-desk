import pytest

from support_desk.cli import run
from support_desk.security import authenticate


def test_create_agent_command_creates_account(session):
    run(["nun@example.com", "Nun"], session, read_password=lambda prompt: "s3cret-pass")

    assert authenticate(session, "nun@example.com", "s3cret-pass") is not None


def test_create_agent_command_rejects_short_password(session):
    with pytest.raises(SystemExit):
        run(["nun@example.com", "Nun"], session, read_password=lambda prompt: "short")


def test_create_agent_command_rejects_mismatched_passwords(session):
    answers = iter(["first-password", "second-password"])
    with pytest.raises(SystemExit):
        run(["nun@example.com", "Nun"], session, read_password=lambda prompt: next(answers))


def test_create_agent_command_rejects_duplicate_email(session):
    run(["nun@example.com", "Nun"], session, read_password=lambda prompt: "s3cret-pass")
    with pytest.raises(SystemExit):
        run(["NUN@example.com", "Nun 2"], session, read_password=lambda prompt: "s3cret-pass")
