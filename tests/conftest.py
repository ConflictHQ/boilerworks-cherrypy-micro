import hashlib
import os
import time

import cherrypy
import pytest

from app import create_app
from app.database import init_db, run_migrations
from app.models import ApiKey, Event

TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5440/boilerworks")

# Fixed test keys
ADMIN_KEY = "bw_test_admin_key_12345"
READ_ONLY_KEY = "bw_test_readonly_key_12345"
NO_SCOPE_KEY = "bw_test_noscope_key_12345"
KEYS_MANAGE_KEY = "bw_test_keysmanage_key_12345"


def _hash(k):
    return hashlib.sha256(k.encode()).hexdigest()


@pytest.fixture(scope="session")
def db_session_factory():
    factory = init_db(TEST_DATABASE_URL)
    run_migrations(TEST_DATABASE_URL)
    return factory


@pytest.fixture(scope="session")
def server(db_session_factory):
    """Start a CherryPy server in a background thread."""
    # Seed test API keys
    session = db_session_factory()
    try:
        # Clean slate
        session.query(Event).delete()
        session.query(ApiKey).delete()
        session.commit()

        for name, raw_key, scopes in [
            ("admin", ADMIN_KEY, ["*"]),
            ("read-only", READ_ONLY_KEY, ["events.read"]),
            ("no-scope", NO_SCOPE_KEY, []),
            ("keys-manage", KEYS_MANAGE_KEY, ["keys.manage"]),
        ]:
            session.add(ApiKey(name=name, key_hash=_hash(raw_key), scopes=scopes))
        session.commit()
    finally:
        session.close()

    root, app_config = create_app(db_session_factory=db_session_factory)

    cherrypy.tree.mount(root, "/", app_config)
    cherrypy.config.update(
        {
            "server.socket_host": "127.0.0.1",
            "server.socket_port": 0,  # random port
            "engine.autoreload.on": False,
            "log.screen": False,
        }
    )

    cherrypy.engine.start()
    # Wait for server to start
    time.sleep(0.5)

    # Get the actual port
    port = cherrypy.server.bound_addr[1]

    yield port

    cherrypy.engine.exit()


@pytest.fixture(scope="session")
def base_url(server):
    return f"http://127.0.0.1:{server}"


@pytest.fixture(scope="session")
def admin_key():
    return ADMIN_KEY


@pytest.fixture(scope="session")
def read_only_key():
    return READ_ONLY_KEY


@pytest.fixture(scope="session")
def no_scope_key():
    return NO_SCOPE_KEY


@pytest.fixture(scope="session")
def keys_manage_key():
    return KEYS_MANAGE_KEY


@pytest.fixture(autouse=True)
def clean_events(db_session_factory):
    """Clean events before each test."""
    session = db_session_factory()
    try:
        session.query(Event).delete()
        session.commit()
    finally:
        session.close()
