"""Shared helpers for Vercel Python serverless API routes."""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_rag = None


def get_rag():
    global _rag
    if _rag is None:
        from fitkg_rag import FitKGRAG, load_dotenv

        load_dotenv()
        _rag = FitKGRAG()
    return _rag


def node_payload(n: dict) -> dict:
    return {
        "id": n.get("id"),
        "label": n.get("display_label") or n.get("label_en") or n.get("label"),
        "label_zh": n.get("label_zh") or n.get("label"),
        "type_en": n.get("type_en") or n.get("type"),
    }


def cors_headers() -> Dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def send_json(handler: BaseHTTPRequestHandler, code: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    for key, val in cors_headers().items():
        handler.send_header(key, val)
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    n = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(n) if n else b"{}"
    return json.loads(raw.decode("utf-8") or "{}")


def handle_options(handler: BaseHTTPRequestHandler) -> None:
    handler.send_response(204)
    for key, val in cors_headers().items():
        handler.send_header(key, val)
    handler.end_headers()
