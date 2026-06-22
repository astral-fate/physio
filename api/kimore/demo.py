from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._common import get_rag, handle_options, node_payload, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        handle_options(self)

    def do_GET(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        class_id = (qs.get("class") or qs.get("class_id") or [None])[0]
        if not class_id:
            send_json(self, 400, {"error": "class query param required"})
            return
        try:
            from fitkg_kimore_bridge import ensure_pose_demos, kimore_fitkg_context, live_rep_feedback

            demos = ensure_pose_demos()
            key = class_id.strip().lower().replace("-", "_")
            block = demos.get("classes", {}).get(key)
            if not block:
                send_json(self, 404, {"error": f"unknown class: {class_id}"})
                return
            rag = get_rag()
            fitkg = kimore_fitkg_context(rag, key)
            fb = live_rep_feedback(rag, key)
            send_json(
                self,
                200,
                {
                    "class_id": key,
                    "label_en": block.get("label_en"),
                    "label_zh": block.get("label_zh"),
                    "regions": block.get("regions", []),
                    "sequence": block.get("sequence", []),
                    "edges": demos.get("edges", []),
                    "fitkg_query": fitkg.get("fitkg_query"),
                    "triples": fitkg.get("triples", []),
                    "nodes": [node_payload(n) for n in fitkg.get("nodes", [])],
                    "primary_muscles_en": fitkg.get("primary_muscles_en", []),
                    "primary_muscles_zh": fitkg.get("primary_muscles_zh", []),
                    "cue_text": fb.get("cue_text"),
                },
            )
        except Exception as ex:
            send_json(self, 500, {"error": str(ex)})
