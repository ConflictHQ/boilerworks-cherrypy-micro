from datetime import datetime, timezone

import cherrypy


class HealthApi:
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
