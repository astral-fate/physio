"""Vercel entrypoint — single FastAPI app for all /api/* routes."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fitkg_api_common import ROOT, get_rag, node_payload

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


@app.get("/api/health")
def health() -> Dict[str, Any]:
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


@app.post("/api/chat")
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
def muscles(node_id: str = Query(..., description="FitKG node id")) -> Dict[str, Any]:
    try:
        from fitkg_body_map import regions_from_graph_node

        rag = get_rag()
        return regions_from_graph_node(node_id, rag.nodes, rag.adj)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.get("/api/kimore")
def kimore_catalog() -> Dict[str, Any]:
    try:
        from fitkg_kimore_bridge import list_kimore_catalog

        return {"classes": list_kimore_catalog()}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.get("/api/kimore/demo")
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
