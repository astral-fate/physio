from http.server import BaseHTTPRequestHandler

from fitkg_api_common import get_rag, handle_options, read_json_body, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        handle_options(self)

    def do_POST(self) -> None:
        try:
            body = read_json_body(self)
            exercise = (body.get("exercise_class") or body.get("exercise") or "").strip()
            if not exercise:
                send_json(self, 400, {"error": "exercise_class required"})
                return
            from fitkg_kimore_bridge import live_rep_feedback

            rag = get_rag()
            fb = live_rep_feedback(
                rag,
                exercise,
                confidence=float(body.get("confidence", 1.0)),
                keypoints=body.get("keypoints"),
            )
            if fb.get("error"):
                send_json(self, 404, fb)
                return
            send_json(self, 200, fb)
        except Exception as ex:
            send_json(self, 500, {"error": str(ex)})
