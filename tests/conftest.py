import os
import tempfile

# Must be set before app modules import settings.
_tmp = tempfile.mkdtemp(prefix="schemes_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["APP_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "none"
os.environ["CHROMA_PATH"] = f"{_tmp}/chroma"
os.environ["RATE_LIMIT_DEFAULT"] = "100000/minute"
os.environ["RATE_LIMIT_CHAT"] = "100000/minute"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-0123456789"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    from app.core.limiter import limiter

    limiter.reset()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)
