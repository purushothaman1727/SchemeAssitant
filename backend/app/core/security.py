import time

import bcrypt
import jwt

from app.core.config import Settings

# A valid bcrypt hash used to keep login timing similar when the username does not exist.
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), (hashed or _DUMMY_HASH).encode()) and hashed is not None
    except ValueError:
        return False


def create_access_token(subject: str, settings: Settings) -> str:
    now = int(time.time())
    payload = {"sub": subject, "iat": now, "exp": now + settings.jwt_expire_minutes * 60, "scope": "admin"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> str | None:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if data.get("scope") != "admin":
        return None
    sub = data.get("sub")
    return sub if isinstance(sub, str) else None
