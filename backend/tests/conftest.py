"""
Shared pytest fixtures.

Tests run against a REAL PostgreSQL + PostGIS database (see
TEST_DATABASE_URL below) because the application relies on PostGIS
geography types/functions (ST_DWithin, ST_Distance, geography casts) that
have no SQLite equivalent. This mirrors how the app actually runs in
Docker Compose.

Set TEST_DATABASE_URL to point at a scratch database before running the
suite, e.g.:

    createdb mausamnetra_test
    psql -d mausamnetra_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"
    export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/mausamnetra_test
    pytest

Each test runs inside its own transaction which is rolled back afterwards,
so tests do not leak state into one another.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/mausamnetra_test",
    ),
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use-only")

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.dependencies.database import get_db_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models.source import Source, SourceType  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all tables once for the test session, drop them afterwards."""
    with engine.connect() as conn:
        conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS postgis")
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """
    Provide a session bound to an outer transaction + SAVEPOINT, so that even
    if application code calls session.commit() (as our services/repositories
    do), the outer transaction is still rolled back at the end of the test,
    keeping tests isolated from one another.
    """
    from sqlalchemy import event

    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session):
    """FastAPI TestClient with the DB dependency overridden to use db_session."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def source(db_session: Session) -> Source:
    src = Source(id=uuid.uuid4(), name=f"Citizen App {uuid.uuid4().hex[:6]}", type=SourceType.CITIZEN,
                 reliability_score=55.0, is_active=True)
    db_session.add(src)
    db_session.commit()
    db_session.refresh(src)
    return src


@pytest.fixture()
def inactive_source(db_session: Session) -> Source:
    src = Source(id=uuid.uuid4(), name=f"Inactive Source {uuid.uuid4().hex[:6]}", type=SourceType.NEWS,
                 reliability_score=40.0, is_active=False)
    db_session.add(src)
    db_session.commit()
    db_session.refresh(src)
    return src


def _make_user(db_session: Session, *, role: UserRole, is_active: bool = True, password: str = "TestPass123!") -> tuple[User, str]:
    user = User(
        id=uuid.uuid4(),
        name="Test User" if role == UserRole.USER else "Test Admin",
        email=f"{uuid.uuid4().hex[:10]}@mausamnetra.dev",
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, password


@pytest.fixture()
def normal_user(db_session: Session):
    return _make_user(db_session, role=UserRole.USER)


@pytest.fixture()
def inactive_user(db_session: Session):
    return _make_user(db_session, role=UserRole.USER, is_active=False)


@pytest.fixture()
def admin_user(db_session: Session):
    return _make_user(db_session, role=UserRole.ADMIN)


@pytest.fixture()
def user_token(normal_user) -> str:
    user, _ = normal_user
    return create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})


@pytest.fixture()
def admin_token(admin_user) -> str:
    user, _ = admin_user
    return create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
