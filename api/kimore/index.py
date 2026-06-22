from http.server import BaseHTTPRequestHandler

from api._common import handle_options, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        handle_options(self)

    def do_GET(self) -> None:
        try:
            from fitkg_kimore_bridge import list_kimore_catalog

            send_json(self, 200, {"classes": list_kimore_catalog()})
        except Exception as ex:
            send_json(self, 500, {"error": str(ex)})
