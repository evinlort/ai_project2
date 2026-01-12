import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from intentbid.app.main import app
from intentbid.app.db.session import get_session


class CompatTestClient(TestClient):
    def get(self, url, **kwargs):
        if "allow_redirects" in kwargs and "follow_redirects" not in kwargs:
            kwargs["follow_redirects"] = kwargs.pop("allow_redirects")
        return super().get(url, **kwargs)

    def request(self, method, url, **kwargs):
        if "allow_redirects" in kwargs and "follow_redirects" not in kwargs:
            kwargs["follow_redirects"] = kwargs.pop("allow_redirects")
        return super().request(method, url, **kwargs)


@pytest.fixture(name="test_engine")
def fixture_test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def fixture_session(test_engine):
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def fixture_client(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    client = CompatTestClient(app)
    yield client
    app.dependency_overrides.clear()
