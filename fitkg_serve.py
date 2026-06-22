#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serve FitKG graph UI + RAG chat API (use this instead of plain http.server).

  python fitkg_serve.py
  → http://localhost:8766/fitkg_graph_ui/   (port 8766 avoids conflict with http.server on 8765)

Optional: NVIDIA NIM or OpenAI — put keys in `.env`, enable LLM in chat UI.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
# 8766 default — Windows often has `python -m http.server 8765` on [::] at the same time
DEFAULT_PORTS = (8766, 8767, 8768, 8770)

_rag = None


def get_rag():
    global _rag
    if _rag is None:
        from fitkg_rag import FitKGRAG, load_dotenv
        load_dotenv()
        _rag = FitKGRAG()
    return _rag


def _node_payload(n: dict) -> dict:
    return {
        "id": n.get("id"),
        "label": n.get("display_label") or n.get("label_en") or n.get("label"),
        "label_zh": n.get("label_zh") or n.get("label"),
        "type_en": n.get("type_en") or n.get("type"),
    }


class FitKGHandler(BaseHTTPRequestHandler):
    server_version = "FitKGServe/1.0"

    def log_message(self, fmt, *args):
        if os.environ.get("FITKG_QUIET"):
            return
        super().log_message(fmt, *args)

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/muscles":
            qs = parse_qs(urlparse(self.path).query)
            nid = (qs.get("node_id") or [None])[0]
            if not nid:
                self._send_json(400, {"error": "node_id required"})
                return
            try:
                from fitkg_body_map import build_adjacency, regions_from_graph_node
                rag = get_rag()
                info = regions_from_graph_node(nid, rag.nodes, rag.adj)
                self._send_json(200, info)
            except Exception as ex:
                self._send_json(500, {"error": str(ex)})
            return
        if path == "/api/kimore":
            try:
                from fitkg_kimore_bridge import list_kimore_catalog
                self._send_json(200, {"classes": list_kimore_catalog()})
            except Exception as ex:
                self._send_json(500, {"error": str(ex)})
            return
        if path == "/api/kimore/demo":
            qs = parse_qs(urlparse(self.path).query)
            class_id = (qs.get("class") or qs.get("class_id") or [None])[0]
            if not class_id:
                self._send_json(400, {"error": "class query param required"})
                return
            try:
                from fitkg_kimore_bridge import ensure_pose_demos, kimore_fitkg_context
                demos = ensure_pose_demos()
                key = class_id.strip().lower().replace("-", "_")
                block = demos.get("classes", {}).get(key)
                if not block:
                    self._send_json(404, {"error": f"unknown class: {class_id}"})
                    return
                rag = get_rag()
                fitkg = kimore_fitkg_context(rag, key)
                from fitkg_kimore_bridge import live_rep_feedback
                fb = live_rep_feedback(rag, key)
                self._send_json(200, {
                    "class_id": key,
                    "label_en": block.get("label_en"),
                    "label_zh": block.get("label_zh"),
                    "regions": block.get("regions", []),
                    "sequence": block.get("sequence", []),
                    "edges": demos.get("edges", []),
                    "fitkg_query": fitkg.get("fitkg_query"),
                    "triples": fitkg.get("triples", []),
                    "nodes": [_node_payload(n) for n in fitkg.get("nodes", [])],
                    "primary_muscles_en": fitkg.get("primary_muscles_en", []),
                    "primary_muscles_zh": fitkg.get("primary_muscles_zh", []),
                    "cue_text": fb.get("cue_text"),
                })
            except Exception as ex:
                self._send_json(500, {"error": str(ex)})
            return
        if path == "/api/health":
            from fitkg_rag import llm_configured, llm_provider, load_dotenv
            load_dotenv()
            rag_path = ROOT / "outputs" / "fitkg_kg" / "rag_index.json"
            self._send_json(200, {
                "server": "fitkg-serve",
                "ok": True,
                "rag_index": rag_path.is_file(),
                "graph": (ROOT / "outputs" / "fitkg_kg" / "graph.json").is_file(),
                "llm": llm_configured(),
                "llm_provider": llm_provider(),
            })
            return
        if path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/fitkg_graph_ui/")
            self.end_headers()
            return
        if path in ("/fitkg_graph_ui", "/fitkg_graph_ui/"):
            self.send_response(302)
            self.send_header("Location", "/fitkg_graph_ui/index.html")
            self.end_headers()
            return
        rel = path.lstrip("/").split("?", 1)[0]
        file_path = (ROOT / rel).resolve()
        root_resolved = str(ROOT.resolve())
        if not str(file_path).startswith(root_resolved):
            self.send_error(404, "Not found")
            return
        if file_path.is_dir():
            index = file_path / "index.html"
            if index.is_file():
                file_path = index
            else:
                self.send_error(404, "Not found")
                return
        elif not file_path.is_file():
            self.send_error(404, "Not found")
            return
        ext = file_path.suffix.lower()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
        }.get(ext, "application/octet-stream")
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/kimore/feedback":
            try:
                body = self._read_json_body()
                exercise = (body.get("exercise_class") or body.get("exercise") or "").strip()
                if not exercise:
                    self._send_json(400, {"error": "exercise_class required"})
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
                    self._send_json(404, fb)
                    return
                self._send_json(200, fb)
            except Exception as ex:
                self._send_json(500, {"error": str(ex)})
            return
        if path != "/api/chat":
            self.send_error(404)
            return
        try:
            body = self._read_json_body()
            query = (body.get("query") or "").strip()
            if not query:
                self._send_json(400, {"error": "query required"})
                return
            use_llm = bool(body.get("use_llm"))
            rag = get_rag()
            ctx = rag.retrieve(query)
            reply = rag.answer(query, use_llm=use_llm)
            self._send_json(200, {
                "reply": reply,
                "nodes": [_node_payload(n) for n in ctx.get("nodes", [])],
                "regions": ctx.get("regions", []),
                "muscle_info": ctx.get("muscle_info", []),
                "passage_count": len(ctx.get("passages", [])),
            })
        except Exception as ex:
            self._send_json(500, {"error": str(ex)})


def _bind_httpd() -> tuple[ThreadingHTTPServer, int]:
    if os.environ.get("FITKG_PORT"):
        ports = (int(os.environ["FITKG_PORT"]),)
    else:
        ports = DEFAULT_PORTS
    last_err = None
    for port in ports:
        try:
            return ThreadingHTTPServer(("0.0.0.0", port), FitKGHandler), port
        except OSError as ex:
            last_err = ex
    raise OSError(last_err or "no free port")


def main() -> int:
    os.chdir(ROOT)
    try:
        httpd, port = _bind_httpd()
    except OSError as ex:
        print(f"ERROR: cannot bind ports {DEFAULT_PORTS}: {ex}")
        print("Run: .\\run_fitkg.ps1   (stops stray servers, then starts FitKG)")
        return 1
    url = f"http://127.0.0.1:{port}/fitkg_graph_ui/index.html"
    print(f"FitKG server: {url}")
    print("Chat API: POST /api/chat  (click the chat icon in the UI)")
    print("KIMORE: GET /api/kimore/demo?class=squat  ·  POST /api/kimore/feedback")
    print("Use this URL only — NOT http://localhost:8765 if http.server is still running there.")
    if port != 8766:
        print(f"(Port {port} — 8766 was busy)")
    rag = ROOT / "outputs" / "fitkg_kg" / "rag_index.json"
    if not rag.is_file():
        print("WARNING: run `python fitkg_build_rag_index.py` for full RAG passages")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
