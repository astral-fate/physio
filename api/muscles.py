from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._common import get_rag, handle_options, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        handle_options(self)

    def do_GET(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        nid = (qs.get("node_id") or [None])[0]
        if not nid:
            send_json(self, 400, {"error": "node_id required"})
            return
        try:
            from fitkg_body_map import regions_from_graph_node

            rag = get_rag()
            info = regions_from_graph_node(nid, rag.nodes, rag.adj)
            send_json(self, 200, info)
        except Exception as ex:
            send_json(self, 500, {"error": str(ex)})
