import hashlib
import json as json_lib
import secrets
import uuid

import cherrypy

from app.models import ApiKey


def _read_json_body():
    """Read and parse JSON from the request body."""
    ct = cherrypy.request.headers.get("Content-Type", "")
    if "application/json" not in ct:
        raise cherrypy.HTTPError(400, "Content-Type must be application/json")
    try:
        raw = cherrypy.request.body.read()
        return json_lib.loads(raw)
    except (ValueError, json_lib.JSONDecodeError):
        raise cherrypy.HTTPError(400, "Invalid JSON body")


class ApiKeysApi:
    def __init__(self, db_session_factory):
        self._db = db_session_factory

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.api_key()
    @cherrypy.tools.require_scope(scope="keys.manage")
    def index(self, **kwargs):
        method = cherrypy.request.method
        if method == "GET":
            return self._list()
        elif method == "POST":
            return self._create()
        raise cherrypy.HTTPError(405, "Method not allowed")

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.api_key()
    @cherrypy.tools.require_scope(scope="keys.manage")
    def default(self, key_id, *args, **kwargs):
        method = cherrypy.request.method
        if method == "DELETE":
            return self._revoke(key_id)
        raise cherrypy.HTTPError(405, "Method not allowed")

    def _create(self):
        body = _read_json_body()

        name = body.get("name")
        if not name:
            raise cherrypy.HTTPError(400, "Field 'name' is required")

        scopes = body.get("scopes", [])
        if not isinstance(scopes, list):
            raise cherrypy.HTTPError(400, "Field 'scopes' must be a list")

        raw_key = f"bw_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        session = self._db()
        try:
            api_key = ApiKey(name=name, key_hash=key_hash, scopes=scopes)
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            result = api_key.to_dict()
            result["key"] = raw_key  # Return plaintext key once
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        cherrypy.response.status = 201
        return {"ok": True, "data": result, "message": "API key created", "errors": []}

    def _list(self):
        session = self._db()
        try:
            keys = session.query(ApiKey).filter(ApiKey.is_active.is_(True)).order_by(ApiKey.created_at.desc()).all()
            result = [k.to_dict() for k in keys]
        finally:
            session.close()

        return {"ok": True, "data": result, "message": None, "errors": []}

    def _revoke(self, key_id):
        try:
            uid = uuid.UUID(key_id)
        except ValueError:
            raise cherrypy.HTTPError(400, "Invalid key ID")

        session = self._db()
        try:
            api_key = session.query(ApiKey).filter(ApiKey.id == uid, ApiKey.is_active.is_(True)).first()
            if not api_key:
                raise cherrypy.HTTPError(404, "API key not found")
            api_key.is_active = False
            session.commit()
        except cherrypy.HTTPError:
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return {"ok": True, "data": None, "message": "API key revoked", "errors": []}
