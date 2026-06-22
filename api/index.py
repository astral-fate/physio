"""Vercel FastAPI entrypoint — API + static UI/KG files (api/index.py)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from fitkg_api_common import ROOT, get_rag, node_payload

UI_DIR = ROOT / "fitkg_graph_ui"
KG_DIR = ROOT / "outputs" / "fitkg_kg"

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def _safe_file(base: Path, rel: str) -> Path:
    path = (base / rel).resolve()
    if not str(path).startswith(str(base.resolve())):
        raise HTTPException(status_code=404, detail="Not Found")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not Found")
    return path


def _file_response(path: Path) -> FileResponse:
    media = _MIME.get(path.suffix.lower())
    return FileResponse(path, media_type=media) if media else FileResponse(path)

app = FastAPI(title="FitKG API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str = ""
    use_llm: bool = False


class FeedbackRequest(BaseModel):
    exercise_class: str = ""
    exercise: str = ""
    confidence: float = 1.0
    keypoints: Optional[List[List[List[float]]]] = None


def _health_payload() -> Dict[str, Any]:
    from fitkg_rag import llm_configured, llm_provider, load_dotenv

    load_dotenv()
    kg = ROOT / "outputs" / "fitkg_kg"
    return {
        "server": "fitkg-vercel",
        "ok": True,
        "rag_index": (kg / "rag_index.json").is_file(),
        "graph": (kg / "graph.json").is_file(),
        "llm": llm_configured(),
        "llm_provider": llm_provider(),
    }


@app.get("/api/health")
@app.get("/health")
def health() -> Dict[str, Any]:
    return _health_payload()


@app.post("/api/chat")
@app.post("/chat")
def chat(body: ChatRequest) -> Dict[str, Any]:
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query required")
    try:
        rag = get_rag()
        ctx = rag.retrieve(query)
        reply = rag.answer(query, use_llm=body.use_llm)
        return {
            "reply": reply,
            "nodes": [node_payload(n) for n in ctx.get("nodes", [])],
            "regions": ctx.get("regions", []),
            "muscle_info": ctx.get("muscle_info", []),
            "passage_count": len(ctx.get("passages", [])),
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.get("/api/muscles")
@app.get("/muscles")
def muscles(node_id: str = Query(..., description="FitKG node id")) -> Dict[str, Any]:
    try:
        from fitkg_body_map import regions_from_graph_node

        rag = get_rag()
        return regions_from_graph_node(node_id, rag.nodes, rag.adj)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.get("/api/kimore")
@app.get("/kimore")
def kimore_catalog() -> Dict[str, Any]:
    try:
        from fitkg_kimore_bridge import list_kimore_catalog

        return {"classes": list_kimore_catalog()}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.get("/api/kimore/demo")
@app.get("/kimore/demo")
def kimore_demo(
    class_id: Optional[str] = Query(None, alias="class"),
    class_id_alt: Optional[str] = Query(None, alias="class_id"),
) -> Dict[str, Any]:
    cid = (class_id or class_id_alt or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="class query param required")
    try:
        from fitkg_kimore_bridge import ensure_pose_demos, kimore_fitkg_context, live_rep_feedback

        demos = ensure_pose_demos()
        key = cid.lower().replace("-", "_")
        block = demos.get("classes", {}).get(key)
        if not block:
            raise HTTPException(status_code=404, detail=f"unknown class: {cid}")
        rag = get_rag()
        fitkg = kimore_fitkg_context(rag, key)
        fb = live_rep_feedback(rag, key)
        return {
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
        }
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.post("/api/kimore/feedback")
@app.post("/kimore/feedback")
def kimore_feedback(body: FeedbackRequest) -> Dict[str, Any]:
    exercise = (body.exercise_class or body.exercise or "").strip()
    if not exercise:
        raise HTTPException(status_code=400, detail="exercise_class required")
    try:
        from fitkg_kimore_bridge import live_rep_feedback

        rag = get_rag()
        fb = live_rep_feedback(
            rag,
            exercise,
            confidence=body.confidence,
            keypoints=body.keypoints,
        )
        if fb.get("error"):
            raise HTTPException(status_code=404, detail=fb)
        return fb
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


# --- Static UI + KG data (Vercel FastAPI serves the whole site) ---

@app.get("/")
@app.get("/fitkg_graph_ui")
@app.get("/fitkg_graph_ui/")
def ui_home() -> FileResponse:
    index = UI_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="UI not found")
    return _file_response(index)


@app.get("/fitkg_graph_ui/{rest:path}")
def ui_asset(rest: str) -> FileResponse:
    return _file_response(_safe_file(UI_DIR, rest))


@app.get("/outputs/fitkg_kg/{rest:path}")
def kg_asset(rest: str) -> FileResponse:
    return _file_response(_safe_file(KG_DIR, rest))
