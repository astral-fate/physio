#!/usr/bin/env python3
"""Build RAG index: passages + entity links + triples for FitKG assistant."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "NYN921-FitKG-CN-41b1142" / "data" / "fitkg-cn"
OUT = Path(__file__).resolve().parent / "outputs" / "fitkg_kg"


def _text(tokens):
    return re.sub(r"\s+", " ", "".join(tokens).replace("\t", " ")).strip()


def main():
    tr = {}
    tp = OUT / "label_translations_en.json"
    if tp.is_file():
        tr = json.load(open(tp, encoding="utf-8"))

    node_by_key = {}
    gp = OUT / "graph.json"
    if gp.is_file():
        for n in json.load(open(gp, encoding="utf-8"))["nodes"]:
            node_by_key[(n.get("label_zh") or n["label"], n["type"])] = n

    passages = []
    entity_passages: dict[str, list[int]] = defaultdict(list)
    triples = []

    pid = 0
    for split in ("train.json", "dev.json"):
        p = ROOT / split
        if not p.is_file():
            continue
        data = json.load(open(p, encoding="utf-8"))
        for doc in data:
            tokens = doc["tokens"]
            text = _text(tokens)
            if len(text) < 8:
                continue
            ents = []
            elist = []
            for e in doc.get("entities", []):
                zh = "".join(tokens[e["start"] : e["end"]]).replace("\t", "").strip()
                if not zh:
                    continue
                en = tr.get(zh, "")
                nid = node_by_key.get((zh, e["type"]), {}).get("id", "")
                ents.append({"zh": zh, "en": en, "type": e["type"], "node_id": nid})
                elist.append((zh, e["type"]))
                key = zh if not en else f"{en}|{zh}"
                if len(entity_passages[key]) < 12:
                    entity_passages[key].append(pid)

            for r in doc.get("relations", []):
                h, t = r.get("head"), r.get("tail")
                if h is None or t is None or h >= len(elist) or t >= len(elist):
                    continue
                hz, ht = elist[h][0], elist[t][0]
                triples.append({
                    "head_zh": hz, "head_en": tr.get(hz, ""),
                    "tail_zh": ht, "tail_en": tr.get(ht, ""),
                    "rel": r["type"],
                    "passage_id": pid,
                })

            passages.append({
                "id": pid,
                "text_zh": text[:800],
                "entities": ents[:20],
            })
            pid += 1

    # dedupe triples
    seen = set()
    uniq_triples = []
    for t in triples:
        k = (t["head_zh"], t["rel"], t["tail_zh"])
        if k in seen:
            continue
        seen.add(k)
        uniq_triples.append(t)

    out = {
        "n_passages": len(passages),
        "n_triples": len(uniq_triples),
        "passages": passages,
        "entity_passages": dict(entity_passages),
        "triples": uniq_triples[:50000],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "rag_index.json"
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Wrote {path} — {len(passages)} passages, {len(uniq_triples)} triples")


if __name__ == "__main__":
    main()
