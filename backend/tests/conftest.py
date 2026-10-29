import os
import sys
import uuid
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_kb.db"


@pytest.fixture(scope="session")
def engine():
    if os.path.exists("./test_kb.db"):
        os.remove("./test_kb.db")
    eng = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()
    if os.path.exists("./test_kb.db"):
        try:
            os.remove("./test_kb.db")
        except Exception:
            pass


@pytest.fixture(scope="function")
def db_session(engine) -> Generator:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user_a(db_session) -> User:
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"user_a_{uid}@antigravity.ai",
        hashed_password=hash_password("PasswordA123!"),
        full_name=f"User Alpha {uid}"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def token_a(user_a) -> str:
    return create_access_token(user_a.id)


@pytest.fixture(scope="function")
def user_b(db_session) -> User:
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"user_b_{uid}@antigravity.ai",
        hashed_password=hash_password("PasswordB123!"),
        full_name=f"User Beta {uid}"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def token_b(user_b) -> str:
    return create_access_token(user_b.id)
