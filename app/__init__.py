import cherrypy

from app.config import Config
from app.database import init_db, run_migrations
from app.seed import seed_api_key
from app.tools import json_error_page, register_tools


class Root:
    pass


def create_app(config=None, db_session_factory=None):
    """Create and configure the CherryPy application. Returns (root, app_config)."""
    # Import API modules here (not at top level) because they use
    # @cherrypy.tools.api_key() decorators that require tools to be registered first.
    from app.api.api_keys import ApiKeysApi
    from app.api.events import EventsApi
    from app.api.health import HealthApi

    if config is None:
        config = Config()

    if db_session_factory is None:
        db_session_factory = init_db(config.database_url)
        run_migrations(config.database_url)

    register_tools(db_session_factory)

    root = Root()
    root.health = HealthApi()
    root.events = EventsApi(db_session_factory)
    root.api_keys = ApiKeysApi(db_session_factory)

    app_config = {
        "/": {
            "request.dispatch": cherrypy.dispatch.Dispatcher(),
            "error_page.default": json_error_page,
            "request.show_tracebacks": False,
        },
    }

    return root, app_config


def main():
    config = Config()
    db_session_factory = init_db(config.database_url)
    run_migrations(config.database_url)

    if config.api_key_seed:
        seed_api_key(db_session_factory, config.api_key_seed)

    root, app_config = create_app(config, db_session_factory)

    cherrypy.tree.mount(root, "/", app_config)
    cherrypy.config.update(
        {
            "server.socket_host": "0.0.0.0",
            "server.socket_port": config.port,
            "engine.autoreload.on": False,
        }
    )
    cherrypy.engine.start()
    cherrypy.engine.block()
