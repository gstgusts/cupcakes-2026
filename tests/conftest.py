import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# Tests use their own database, so the dev data in "cupcakes" is never touched.
# Config reads DATABASE_URL on import, so it must be set before the app is imported.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://cupcakes:cupcakes@localhost:5432/cupcakes_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from flask_migrate import Migrate, upgrade  # noqa: E402

from app import create_app, db  # noqa: E402


def _create_database_if_missing(url):
    url = make_url(url)
    # CREATE DATABASE cannot run inside a transaction, so connect to the default database in autocommit mode
    engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"),
                              {"name": url.database}).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    engine.dispose()


@pytest.fixture(scope="session")
def app():
    _create_database_if_missing(TEST_DATABASE_URL)

    app = create_app()
    app.config["TESTING"] = True
    Migrate(app, db)

    with app.app_context():
        # Start from an empty schema and build it with the real migrations
        # (this also seeds the profiles of user1 and user2)
        with db.engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
        upgrade(directory="migrations")

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    """Logs in without Keycloak by putting the identity into the session, like /auth/callback does."""
    def do_login(email="user1@example.com", roles=("user",), first_name="", last_name=""):
        with client.session_transaction() as session:
            session["user"] = {
                "sub": "test-sub",
                "username": email.split("@")[0],
                "name": f"{first_name} {last_name}".strip(),
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "roles": list(roles),
            }

    return do_login
