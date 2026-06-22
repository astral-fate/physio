#!/usr/bin/env python3
"""Anatomical region mapping for FitKG muscle ↔ exercise graph."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

OUT = Path(__file__).resolve().parent / "outputs" / "fitkg_kg"
MAP_PATH = OUT / "muscle_region_map.json"

BODY_NODE_TYPES = frozenset({"身体部位", "解剖结构"})
EXERCISE_NODE_TYPES = frozenset({"健身动作", "运动项目"})
TRAINS_REL = "锻炼"

_map_cache: Optional[Dict[str, Any]] = None


def load_region_map() -> Dict[str, Any]:
    global _map_cache
    if _map_cache is None:
        if not MAP_PATH.is_file():
            _map_cache = {"regions": [], "exercise_presets": {}, "legacy_aliases": {}}
        else:
            _map_cache = json.load(open(MAP_PATH, encoding="utf-8"))
    return _map_cache


def region_catalog() -> List[Dict[str, Any]]:
    return load_region_map().get("regions", [])


def _expand_legacy(region_ids: Iterable[str]) -> Set[str]:
    m = load_region_map()
    aliases = m.get("legacy_aliases") or {}
    out: Set[str] = set()
    for rid in region_ids:
        out.add(rid)
        for extra in aliases.get(rid, []):
            out.add(extra)
    return out


def _keyword_index() -> List[tuple]:
    """(keyword_lower, region_id) sorted longest-first for greedy match."""
    pairs = []
    for r in region_catalog():
        rid = r["id"]
        for kw in r.get("fitkg_keywords", []):
            if kw:
                pairs.append((kw.lower(), rid))
    pairs.sort(key=lambda x: -len(x[0]))
    return pairs


def regions_from_text(zh: str = "", en: str = "") -> List[str]:
    blob = f"{zh} {en}".lower()
    if not blob.strip():
        return []
    found: Set[str] = set()
    for kw, rid in _keyword_index():
        kw_l = kw.lower()
        # Avoid single CJK chars matching inside compound terms (e.g. 头 in 股四头肌)
        if len(kw_l) == 1 and "\u4e00" <= kw_l <= "\u9fff":
            continue
        if kw_l in blob:
            found.add(rid)
    return sorted(found)


def regions_from_nodes(nodes: List[Dict[str, Any]]) -> List[str]:
    found: Set[str] = set()
    for n in nodes:
        found.update(
            regions_from_text(
                n.get("label_zh") or n.get("label") or "",
                n.get("label_en") or n.get("display_label") or "",
            )
        )
    return sorted(found)


def regions_from_exercise_preset(name: str) -> List[str]:
    presets = load_region_map().get("exercise_presets") or {}
    kimore = load_region_map().get("kimore_classes") or {}
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    if key in kimore:
        return list(kimore[key].get("regions", []))
    for k, regs in presets.items():
        if k.lower().replace(" ", "_").replace("-", "_") == key:
            return list(regs)
    return []


def regions_from_graph_node(
    node_id: str,
    nodes_by_id: Dict[str, Dict],
    adj: Dict[str, List[Dict]],
    *,
    include_presets: bool = True,
) -> Dict[str, Any]:
    """Resolve muscle regions from a FitKG node (exercise, muscle, or sport)."""
    node = nodes_by_id.get(node_id)
    if not node:
        return {"regions": [], "muscles": [], "exercises": []}

    regions: Set[str] = set()
    muscles: List[Dict[str, str]] = []
    exercises: List[Dict[str, str]] = []
    ntype = node.get("type", "")

    def _node_line(n: Dict) -> Dict[str, str]:
        return {
            "id": n.get("id", ""),
            "label_en": n.get("display_label") or n.get("label_en") or n.get("label", ""),
            "label_zh": n.get("label_zh") or n.get("label", ""),
            "type_en": n.get("type_en") or n.get("type", ""),
        }

    if ntype in BODY_NODE_TYPES:
        regions.update(regions_from_text(node.get("label_zh") or node.get("label", ""), node.get("label_en") or ""))
        muscles.append(_node_line(node))
        for edge in adj.get(node_id, []):
            if edge.get("_rev"):
                src_id = edge["source"]
                src = nodes_by_id.get(src_id)
                if src and src.get("type") in EXERCISE_NODE_TYPES and edge.get("type") == TRAINS_REL:
                    exercises.append(_node_line(src))
            else:
                tgt = nodes_by_id.get(edge["target"])
                if tgt and tgt.get("type") in EXERCISE_NODE_TYPES and edge.get("type") == TRAINS_REL:
                    exercises.append(_node_line(tgt))

    elif ntype in EXERCISE_NODE_TYPES:
        exercises.append(_node_line(node))
        label_keys = [
            node.get("label_en") or "",
            node.get("label_zh") or node.get("label") or "",
            node.get("display_label") or "",
        ]
        kimore_hit = False
        if include_presets:
            for lk in label_keys:
                k = lk.strip().lower().replace(" ", "_").replace("-", "_")
                if k in (load_region_map().get("kimore_classes") or {}):
                    regions.update(regions_from_exercise_preset(k))
                    kimore_hit = True
                    break
            if not kimore_hit:
                for lk in label_keys:
                    regions.update(regions_from_exercise_preset(lk))
        for edge in adj.get(node_id, []):
            if edge.get("_rev"):
                continue
            if edge.get("type") != TRAINS_REL:
                continue
            tgt = nodes_by_id.get(edge["target"])
            if not tgt or tgt.get("type") not in BODY_NODE_TYPES:
                continue
            muscles.append(_node_line(tgt))
            if not kimore_hit:
                regions.update(regions_from_text(tgt.get("label_zh") or tgt.get("label", ""), tgt.get("label_en") or ""))

    else:
        regions.update(regions_from_text(node.get("label_zh") or node.get("label", ""), node.get("label_en") or ""))

    expanded = _expand_legacy(regions)
    return {
        "regions": sorted(expanded),
        "muscles": muscles[:20],
        "exercises": exercises[:20],
        "node": _node_line(node),
    }


def build_adjacency(graph: Dict[str, Any]) -> Dict[str, List[Dict]]:
    adj: Dict[str, List[Dict]] = {}
    for e in graph.get("edges", []):
        adj.setdefault(e["source"], []).append(e)
        adj.setdefault(e["target"], []).append({**e, "_rev": True})
    return adj


def resolve_query_regions(
    query: str,
    matched_nodes: List[Dict],
    *,
    graph: Optional[Dict] = None,
    adj: Optional[Dict[str, List[Dict]]] = None,
) -> List[str]:
    """Combine RAG node matches, presets, and graph 锻炼 edges."""
    regions: Set[str] = set(regions_from_nodes(matched_nodes))
    regions.update(regions_from_exercise_preset(query))
    for term in re.split(r"\W+", query.lower()):
        if len(term) > 2:
            regions.update(regions_from_exercise_preset(term))

    if graph is not None:
        nodes_by_id = {n["id"]: n for n in graph.get("nodes", [])}
        if adj is None:
            adj = build_adjacency(graph)
        for n in matched_nodes:
            if n.get("type") in EXERCISE_NODE_TYPES:
                info = regions_from_graph_node(n["id"], nodes_by_id, adj)
                regions.update(info["regions"])
    return sorted(regions)
