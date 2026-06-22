from http.server import BaseHTTPRequestHandler

from api._common import get_rag, handle_options, node_payload, read_json_body, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        handle_options(self)

    def do_POST(self) -> None:
        try:
            body = read_json_body(self)
            query = (body.get("query") or "").strip()
            if not query:
                send_json(self, 400, {"error": "query required"})
                return
            use_llm = bool(body.get("use_llm"))
            rag = get_rag()
            ctx = rag.retrieve(query)
            reply = rag.answer(query, use_llm=use_llm)
            send_json(
                self,
                200,
                {
                    "reply": reply,
                    "nodes": [node_payload(n) for n in ctx.get("nodes", [])],
                    "regions": ctx.get("regions", []),
                    "muscle_info": ctx.get("muscle_info", []),
                    "passage_count": len(ctx.get("passages", [])),
                },
            )
        except Exception as ex:
            send_json(self, 500, {"error": str(ex)})
