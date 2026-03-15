from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from lens_server.database import SessionLocal, init_db
from lens_server.main import app
from lens_server.models import Trace


@pytest.fixture(autouse=True)
def reset_db() -> None:
    init_db()
    with SessionLocal() as session:
        session.execute(delete(Trace))
        session.commit()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
