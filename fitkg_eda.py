#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FitKG-CN EDA: build searchable knowledge graph + summary tables."""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent / "NYN921-FitKG-CN-41b1142"
DATA = ROOT / "data" / "fitkg-cn"
OUT = Path(__file__).resolve().parent / "outputs" / "fitkg_kg"

ENTITY_EN = {
    "身体部位": "Body part",
    "运动项目": "Sport / activity",
    "健身动作": "Exercise",
    "器械工具": "Equipment",
    "运动目标": "Training goal",
    "解剖结构": "Anatomy",
    "营养物质": "Nutrient",
    "专业名词": "Term",
}

RELATION_EN = {
    "位置": "Location",
    "形状": "Shape",
    "起点": "Origin",
    "止点": "Insertion",
    "包含": "Contains",
    "从属": "Part-of",
    "锻炼": "Trains",
    "功能": "Function",
    "使用": "Uses",
    "实现": "Achieves",
    "需要": "Requires",
}


def _entity_text(tokens: List[str], start: int, end: int) -> str:
    return "".join(tokens[start:end]).replace("\t", "").strip()


def load_splits() -> List[Dict[str, Any]]:
    docs = []
    for name in ("train.json", "dev.json"):
        p = DATA / name
        if not p.is_file():
            continue
        with open(p, encoding="utf-8") as f:
            batch = json.load(f)
        for d in batch:
            d["_split"] = name.replace(".json", "")
        docs.extend(batch)
    return docs


def load_label_translations() -> Dict[str, str]:
    p = OUT / "label_translations_en.json"
    if p.is_file():
        return json.load(open(p, encoding="utf-8"))
    return {}


def apply_english_labels(nodes: List[Dict], edges: List[Dict], tr: Dict[str, str]) -> Dict[str, List[str]]:
    """Set label_en / display_label; rebuild search index with English."""
    index: Dict[str, List[str]] = defaultdict(list)
    for n in nodes:
        zh = n["label"]
        en = tr.get(zh, "")
        n["label_zh"] = zh
        n["label_en"] = en or None
        n["display_label"] = en if en and en != zh else f"{n.get('type_en', 'Entity')}: {zh}"
        for term in (en, zh, n.get("type_en", ""), n.get("type", "")):
            if not term:
                continue
            t = term.lower().strip()
            index[t].append(n["id"])
            if " " in t:
                for w in t.split():
                    if len(w) > 1:
                        index[w].append(n["id"])
            for L in (2, 3, 4, 5):
                for i in range(max(0, len(t) - L + 1)):
                    index[t[i : i + L]].append(n["id"])
    for e in edges:
        for term in (e.get("type_en", ""), e.get("type", "")):
            if term:
                index[term.lower()].append(e["id"])
    for k in index:
        index[k] = sorted(set(index[k]))
    return dict(index)


def build_graph(docs: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], Dict[str, Any]]:
    node_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    edge_agg: Dict[Tuple[str, str, str], int] = defaultdict(int)
    ent_counter = Counter()
    rel_counter = Counter()
    doc_count = len(docs)

    for di, doc in enumerate(docs):
        tokens = doc["tokens"]
        keys: List[str] = []
        for e in doc.get("entities", []):
            text = _entity_text(tokens, e["start"], e["end"])
            if not text:
                continue
            key = (text, e["type"])
            ent_counter[e["type"]] += 1
            if key not in node_map:
                nid = f"n{len(node_map)}"
                node_map[key] = {
                    "id": nid,
                    "label": text,
                    "type": e["type"],
                    "type_en": ENTITY_EN.get(e["type"], e["type"]),
                    "count": 0,
                    "doc_ids": [],
                }
            node_map[key]["count"] += 1
            if len(node_map[key]["doc_ids"]) < 20:
                node_map[key]["doc_ids"].append(di)
            keys.append(node_map[key]["id"])

        for r in doc.get("relations", []):
            h, t = r.get("head"), r.get("tail")
            if h is None or t is None or h >= len(keys) or t >= len(keys):
                continue
            rel_counter[r["type"]] += 1
            edge_agg[(keys[h], keys[t], r["type"])] += 1

    nodes = list(node_map.values())
    edges = [
        {
            "id": f"e{i}",
            "source": s,
            "target": t,
            "type": rt,
            "type_en": RELATION_EN.get(rt, rt),
            "weight": w,
        }
        for i, ((s, t, rt), w) in enumerate(sorted(edge_agg.items(), key=lambda x: -x[1]))
    ]

    tr = load_label_translations()
    if tr:
        search_index = apply_english_labels(nodes, edges, tr)
        translated = sum(1 for n in nodes if n.get("label_en") and n["label_en"] != n["label"])
        print(f"English labels: {translated}/{len(nodes)} from cache")
    else:
        search_index = _legacy_search_index(nodes)
        print("No label_translations_en.json — run: python fitkg_translate_labels.py")

    stats = {
        "documents": doc_count,
        "nodes": len(nodes),
        "edges": len(edges),
        "entity_mentions": sum(ent_counter.values()),
        "relation_mentions": sum(rel_counter.values()),
        "entity_types": dict(ent_counter),
        "relation_types": dict(rel_counter),
        "top_entities_by_freq": sorted(
            [{
                "label": n.get("display_label", n["label"]),
                "label_zh": n.get("label_zh", n["label"]),
                "type": n["type_en"],
                "count": n["count"],
            } for n in nodes],
            key=lambda x: -x["count"],
        )[:30],
        "splits": dict(Counter(d.get("_split", "?") for d in docs)),
        "english_labels": bool(tr),
    }
    return nodes, edges, {"stats": stats, "search_index": search_index}


def _legacy_search_index(nodes: List[Dict]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = defaultdict(list)
    for n in nodes:
        label = n["label"].lower()
        index[label].append(n["id"])
        for ch in range(len(label)):
            for L in (2, 3, 4):
                if ch + L <= len(label):
                    index[label[ch : ch + L]].append(n["id"])
        index[n["type"]].append(n["id"])
        if n.get("type_en"):
            index[n["type_en"].lower()].append(n["id"])
    for k in index:
        index[k] = sorted(set(index[k]))
    return dict(index)


def write_outputs(nodes: List[Dict], edges: List[Dict], meta: Dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    graph = {"nodes": nodes, "edges": edges, "meta": meta["stats"]}
    with open(OUT / "graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=None)

    with open(OUT / "search_index.json", "w", encoding="utf-8") as f:
        json.dump(meta["search_index"], f, ensure_ascii=False)

    with open(OUT / "entity_types.json", "w", encoding="utf-8") as f:
        json.dump({"zh": list(ENTITY_EN.keys()), "en": ENTITY_EN, "relations": RELATION_EN}, f, ensure_ascii=False, indent=2)

    # CSV tables for paper / reports
    import csv
    with open(OUT / "entity_type_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type_zh", "type_en", "count"])
        for k, v in meta["stats"]["entity_types"].items():
            w.writerow([k, ENTITY_EN.get(k, k), v])
    with open(OUT / "relation_type_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type_zh", "type_en", "count"])
        for k, v in meta["stats"]["relation_types"].items():
            w.writerow([k, RELATION_EN.get(k, k), v])

    with open(OUT / "eda_summary.md", "w", encoding="utf-8") as f:
        s = meta["stats"]
        f.write("# FitKG-CN EDA Summary\n\n")
        f.write(f"- Documents: **{s['documents']}** (train + dev)\n")
        f.write(f"- Unique entities (nodes): **{s['nodes']}**\n")
        f.write(f"- Unique relations (edges): **{s['edges']}**\n")
        f.write(f"- Entity mentions: **{s['entity_mentions']}**\n")
        f.write(f"- Relation mentions: **{s['relation_mentions']}**\n\n")
        f.write("## Entity types\n")
        for k, v in sorted(s["entity_types"].items(), key=lambda x: -x[1]):
            f.write(f"- {k} ({ENTITY_EN.get(k, k)}): {v}\n")
        f.write("\n## Relation types\n")
        for k, v in sorted(s["relation_types"].items(), key=lambda x: -x[1]):
            f.write(f"- {k} ({RELATION_EN.get(k, k)}): {v}\n")
        f.write("\n## Top entities by document frequency\n")
        for row in s["top_entities_by_freq"][:15]:
            f.write(f"- {row['label']} [{row['type']}]: {row['count']}\n")

    print(f"Wrote {OUT}")


def main() -> None:
    docs = load_splits()
    if not docs:
        raise SystemExit(f"No data under {DATA}")
    nodes, edges, meta = build_graph(docs)
    write_outputs(nodes, edges, meta)
    print(f"Nodes: {len(nodes)}, edges: {len(edges)}, docs: {len(docs)}")


if __name__ == "__main__":
    main()
