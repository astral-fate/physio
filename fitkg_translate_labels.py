#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translate FitKG entity labels zh → en (cached). Run once, then: python fitkg_eda.py"""
from __future__ import annotations

import json
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent / "outputs" / "fitkg_kg"
CACHE = OUT / "label_translations_en.json"
GRAPH = OUT / "graph.json"
BATCH = 40
SEP = " ⟨|⟩ "


def load_unique_labels() -> list[str]:
    if not GRAPH.is_file():
        raise SystemExit(f"Run fitkg_eda.py first — missing {GRAPH}")
    with open(GRAPH, encoding="utf-8") as f:
        g = json.load(f)
    labels = sorted({n["label"] for n in g["nodes"] if n.get("label")})
    return labels


def translate_batch(texts: list[str], translator) -> list[str]:
    if not texts:
        return []
    if len(texts) == 1:
        return [translator.translate(texts[0])]
    blob = SEP.join(texts)
    out = translator.translate(blob)
    parts = [p.strip() for p in out.split(SEP)]
    if len(parts) != len(texts):
        return [translator.translate(t) for t in texts]
    return parts


def main() -> None:
    from deep_translator import GoogleTranslator

    labels = load_unique_labels()
    cache: dict[str, str] = {}
    if CACHE.is_file():
        cache = json.load(open(CACHE, encoding="utf-8"))
    todo = [t for t in labels if t not in cache]
    print(f"Labels: {len(labels)} | cached: {len(cache)} | to translate: {len(todo)}")

    tr = GoogleTranslator(source="zh-CN", target="en")
    for i in range(0, len(todo), BATCH):
        batch = todo[i : i + BATCH]
        try:
            en = translate_batch(batch, tr)
            for zh, e in zip(batch, en):
                cache[zh] = e or zh
        except Exception as ex:
            print(f"  batch {i} failed ({ex}), one-by-one…")
            for t in batch:
                try:
                    cache[t] = tr.translate(t) or t
                except Exception:
                    cache[t] = t
                time.sleep(0.15)
        if (i // BATCH) % 5 == 0:
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            print(f"  progress {min(i + BATCH, len(todo))}/{len(todo)}")
        time.sleep(0.25)

    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Saved {CACHE} ({len(cache)} entries)")


if __name__ == "__main__":
    main()
