"""Create or reset an admin user. Password comes from ADMIN_PASSWORD or an interactive prompt.

    ADMIN_PASSWORD=... python -m app.scripts.create_admin --username admin
"""
import argparse
import getpass
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password

MIN_LENGTH = 12


def upsert_admin(db: Session, username: str, password: str) -> bool:
    """Returns True if created, False if the password of an existing admin was reset."""
    from app.models import AdminUser

    if len(password) < MIN_LENGTH:
        raise ValueError(f"password must be at least {MIN_LENGTH} characters")
    user = db.scalar(select(AdminUser).where(AdminUser.username == username))
    created = user is None
    if created:
        user = AdminUser(username=username, password_hash="")
        db.add(user)
    user.password_hash = hash_password(password)
    user.is_active = True
    db.commit()
    return created


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", default="admin")
    args = ap.parse_args()
    pw = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("New admin password: ")
    from app.core.database import Base, SessionLocal, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        print("created" if upsert_admin(db, args.username, pw) else "password reset")
    finally:
        db.close()


if __name__ == "__main__":
    main()
