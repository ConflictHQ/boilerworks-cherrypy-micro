import hashlib
import json
from datetime import datetime, timezone

import cherrypy

from app.models import ApiKey

# Module-level storage for the DB session factory.
# Set by register_tools() before the server starts handling requests.
_db_session_factory = None


def _hash_key(raw_key):
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _json_escape(s):
    """Simple JSON string escaping."""
    return json.dumps(str(s))


def json_error_page(status, message, traceback, version):
    """Custom error page handler that returns JSON instead of HTML."""
    cherrypy.response.headers["Content-Type"] = "application/json"
    return json.dumps({"ok": False, "data": None, "message": message, "errors": [message]})


def api_key_tool():
    """Read X-API-Key header, hash it, look up in DB, store on request."""
    raw_key = cherrypy.request.headers.get("X-API-Key")
    if not raw_key:
        raise cherrypy.HTTPError(401, "Missing X-API-Key header")

    if _db_session_factory is None:
        raise cherrypy.HTTPError(500, "Database not configured")

    key_hash = _hash_key(raw_key)
    session = _db_session_factory()
    try:
        api_key = session.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True)).first()
        if not api_key:
            raise cherrypy.HTTPError(401, "Invalid API key")
        api_key.last_used_at = datetime.now(timezone.utc)
        session.commit()
        # Eagerly load attributes before detaching from session
        key_data = {
            "id": api_key.id,
            "name": api_key.name,
            "scopes": list(api_key.scopes),
            "is_active": api_key.is_active,
        }
    except cherrypy.HTTPError:
        session.close()
        raise
    except Exception:
        session.rollback()
        session.close()
        raise cherrypy.HTTPError(500, "Auth error")
    finally:
        session.close()

    # Store a simple namespace object so downstream code can access .scopes etc.
    cherrypy.request.api_key = type("ApiKeyInfo", (), key_data)()


def require_scope_tool(scope=None):
    """Check that the authenticated api_key has the required scope or '*'."""
    api_key = getattr(cherrypy.request, "api_key", None)
    if not api_key:
        raise cherrypy.HTTPError(401, "Not authenticated")
    if "*" not in api_key.scopes and scope not in api_key.scopes:
        raise cherrypy.HTTPError(403, f"Missing required scope: {scope}")


# Register tools at module level so decorators work at class definition time.
cherrypy.tools.api_key = cherrypy.Tool("before_handler", api_key_tool, priority=10)
cherrypy.tools.require_scope = cherrypy.Tool("before_handler", require_scope_tool, priority=11)


def register_tools(db_session_factory):
    """Store db_session_factory so the api_key tool can find it at request time."""
    global _db_session_factory
    _db_session_factory = db_session_factory
