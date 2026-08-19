"""Test fixtures.

ADR-001: PostgreSQL-specific behavior must be tested against PostgreSQL
rather than inferred from SQLite, so these tests require a real PostgreSQL
instance (see docker-compose.yml) reachable at ATLAS_DATABASE_URL, or the
default `postgresql+psycopg://atlas:atlas@localhost:5432/atlas_test`. Every
fixture here descends from `engine`, which skips the whole run fast (~2s)
if that database is unreachable, instead of hanging on a slow TCP timeout.
"""
import socket
import threading
import time
import uuid
from collections.abc import Iterator

import os

os.environ.setdefault("ATLAS_ENVIRONMENT", "test")
os.environ.setdefault(
    "ATLAS_DATABASE_URL", "postgresql+psycopg://atlas:atlas@localhost:5432/atlas_test"
)
os.environ.setdefault("ATLAS_ENABLE_DEVELOPMENT_IDENTITY", "true")
os.environ.setdefault("ATLAS_HEALTH_CHECK_INTERVAL_SECONDS", "0")  # tests drive checks explicitly

import pytest
import uvicorn
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import create_app
from app.models import Permission, Role, RolePermission
from app.rbac.permissions import ALL_PERMISSIONS, SEED_ROLES
from app.simulators.sanfabric.app import app as sanfabric_simulator_app


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    db_url = get_settings().database_url
    test_engine = create_engine(db_url, future=True, connect_args={"connect_timeout": 2})
    try:
        with test_engine.connect():
            pass
    except Exception:
        test_engine.dispose()
        pytest.skip(f"PostgreSQL is not reachable at {db_url}; start it with `docker compose up -d`.")

    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _seed_rbac(engine: Engine) -> None:
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as session:
        if session.query(Role).count() > 0:
            return
        permission_ids = {}
        for key, description in ALL_PERMISSIONS.items():
            permission = Permission(key=key, description=description)
            session.add(permission)
            session.flush()
            permission_ids[key] = permission.id
        for role_name, permission_keys in SEED_ROLES.items():
            role = Role(name=role_name)
            session.add(role)
            session.flush()
            for key in permission_keys:
                session.add(RolePermission(role_id=role.id, permission_id=permission_ids[key]))
        session.commit()


@pytest.fixture()
def db_session(engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=engine, future=True)
    session = session_factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def correlation_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def sanfabric_simulator_url() -> Iterator[str]:
    """Runs the real SAN fabric simulator ASGI app on a live loopback port
    for the duration of the test session, so connector tests exercise a real
    HTTP round trip rather than mocking the transport layer.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    config = uvicorn.Config(sanfabric_simulator_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("SAN fabric simulator did not start within 5 seconds.")
        time.sleep(0.02)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)
