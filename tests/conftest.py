from typing import Dict, Generator

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import Base, get_engine, get_sessionmaker, get_db
from app.core.config import settings

fake = Faker()

test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables once before the test session, drop them after."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """A DB session for a single test. Commits on success, rolls back on error."""
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """A FastAPI TestClient whose get_db dependency is overridden to use db_session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _strong_password() -> str:
    """A password satisfying UserCreate's strength rules."""
    return "TestPass123!"


@pytest.fixture
def fake_user_payload() -> Dict[str, str]:
    """A registration payload with a unique username/email each time."""
    password = _strong_password()
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name()[:20],
        "password": password,
        "confirm_password": password,
    }


@pytest.fixture
def registered_user(client: TestClient, fake_user_payload: Dict[str, str]) -> Dict[str, str]:
    """Registers a user through the real API and returns the payload (incl. password)."""
    response = client.post("/users/register", json=fake_user_payload)
    assert response.status_code == 201, response.text
    return fake_user_payload


@pytest.fixture
def auth_headers(client: TestClient, registered_user: Dict[str, str]) -> Dict[str, str]:
    """Logs in as registered_user and returns an Authorization header dict."""
    response = client.post(
        "/users/login",
        json={"username": registered_user["username"], "password": registered_user["password"]},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
    