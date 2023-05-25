from fastapi.testclient import TestClient
import pytest
from knotty import make_app, model

from knotty.config import Config, DefaultNamesConfig, get_config
from knotty.db import make_db
from knotty.tests import make_user


@pytest.fixture
def client() -> TestClient:
    config = Config(
        secret_key="hello world",  # type: ignore
        db_url="sqlite://",
        connect_args={"check_same_thread": False},
        default_names=DefaultNamesConfig(),
        use_static_pool=True,
        logging={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "loggers": {
                "sqlalchemy.engine": {
                    "level": "INFO",
                },
            },
            "root": {
                "level": "DEBUG",
            },
        },
    )

    def get_test_config() -> Config:
        return config

    app = make_app(config)
    app.dependency_overrides[get_config] = get_test_config

    DbSession = make_db(config=config)

    with DbSession() as session:
        model.Base.metadata.create_all(bind=session.get_bind())
        session.commit()

    return TestClient(app)


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    token = make_user(client)
    client.headers["Authorization"] = f"Bearer {token}"

    return client
