import json as json_lib
import uuid
from datetime import datetime, timezone

import cherrypy

from app.models import Event


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


class EventsApi:
    def __init__(self, db_session_factory):
        self._db = db_session_factory

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.api_key()
    def index(self, **kwargs):
        method = cherrypy.request.method
        if method == "GET":
            require_scope_tool_check("events.read")
            return self._list(**kwargs)
        elif method == "POST":
            require_scope_tool_check("events.write")
            return self._create()
        raise cherrypy.HTTPError(405, "Method not allowed")

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.api_key()
    def default(self, event_id, *args, **kwargs):
        method = cherrypy.request.method
        if method == "GET":
            require_scope_tool_check("events.read")
            return self._get(event_id)
        elif method == "DELETE":
            require_scope_tool_check("events.write")
            return self._delete(event_id)
        raise cherrypy.HTTPError(405, "Method not allowed")

    def _create(self):
        body = _read_json_body()

        event_type = body.get("type")
        if not event_type:
            raise cherrypy.HTTPError(400, "Field 'type' is required")

        payload = body.get("payload", {})
        status = body.get("status", "pending")

        session = self._db()
        try:
            event = Event(type=event_type, payload=payload, status=status)
            session.add(event)
            session.commit()
            session.refresh(event)
            result = event.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        cherrypy.response.status = 201
        return {"ok": True, "data": result, "message": "Event created", "errors": []}

    def _list(self, **kwargs):
        session = self._db()
        try:
            query = session.query(Event).filter(Event.deleted_at.is_(None))
            event_type = kwargs.get("type")
            if event_type:
                query = query.filter(Event.type == event_type)
            query = query.order_by(Event.created_at.desc())
            events = query.all()
            result = [e.to_dict() for e in events]
        finally:
            session.close()

        return {"ok": True, "data": result, "message": None, "errors": []}

    def _get(self, event_id):
        try:
            uid = uuid.UUID(event_id)
        except ValueError:
            raise cherrypy.HTTPError(400, "Invalid event ID")

        session = self._db()
        try:
            event = session.query(Event).filter(Event.id == uid, Event.deleted_at.is_(None)).first()
            if not event:
                raise cherrypy.HTTPError(404, "Event not found")
            result = event.to_dict()
        finally:
            session.close()

        return {"ok": True, "data": result, "message": None, "errors": []}

    def _delete(self, event_id):
        try:
            uid = uuid.UUID(event_id)
        except ValueError:
            raise cherrypy.HTTPError(400, "Invalid event ID")

        session = self._db()
        try:
            event = session.query(Event).filter(Event.id == uid, Event.deleted_at.is_(None)).first()
            if not event:
                raise cherrypy.HTTPError(404, "Event not found")
            event.deleted_at = datetime.now(timezone.utc)
            session.commit()
        except cherrypy.HTTPError:
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return {"ok": True, "data": None, "message": "Event deleted", "errors": []}


def require_scope_tool_check(scope):
    """Inline scope check (since we need method-specific scopes)."""
    api_key = getattr(cherrypy.request, "api_key", None)
    if not api_key:
        raise cherrypy.HTTPError(401, "Not authenticated")
    if "*" not in api_key.scopes and scope not in api_key.scopes:
        raise cherrypy.HTTPError(403, f"Missing required scope: {scope}")
