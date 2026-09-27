import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.dependencies import get_db
from app.main import app

# StaticPool ensures a single shared SQLite connection in memory across threads/tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _fresh_database():
    """Ensures each test gets a clean, isolated database state."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def register(client):
    def _register(username="admin", password="secretpassword123", full_name="Admin User"):
        return client.post(
            "/auth/register",
            json={"username": username, "password": password, "full_name": full_name},
        )

    return _register


@pytest.fixture
def login(client):
    def _login(username="admin", password="secretpassword123"):
        resp = client.post(
            "/auth/login",
            data={"username": username, "password": password},
        )
        return resp.json()["access_token"]

    return _login


@pytest.fixture
def auth_header():
    def _header(token):
        return {"Authorization": f"Bearer {token}"}

    return _header


@pytest.fixture
def admin_token(register, login):
    register("sysadmin", "AdminPass123!")
    return login("sysadmin", "AdminPass123!")


@pytest.fixture
def user_token(register, login):
    # First user is admin
    register("sysadmin", "AdminPass123!")
    # Second user is standard 'user'
    register("standarduser", "UserPass123!", "Standard User")
    return login("standarduser", "UserPass123!")
