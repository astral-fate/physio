#!/usr/bin/env python3
"""Retrieve from FitKG graph + passages; optional LLM answer."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

OUT = Path(__file__).resolve().parent / "outputs" / "fitkg_kg"
_PROJECT_ROOT = OUT.parent.parent

NVIDIA_NIM_BASE = "https://integrate.api.nvidia.com/v1"
DEFAULT_NIM_MODEL = "qwen/qwen3-next-80b-a3b-instruct"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def load_dotenv() -> None:
    """Load project `.env` (does not override variables already set in the shell)."""
    for path in (_PROJECT_ROOT / ".env", Path.cwd() / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
        break


def llm_configured() -> bool:
    load_dotenv()
    return bool(os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def llm_provider() -> Optional[str]:
    load_dotenv()
    if os.environ.get("NVIDIA_API_KEY"):
        return "nvidia-nim"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return None


def get_llm_client() -> Tuple[Any, str, str]:
    """Return (OpenAI client, model id, provider name). Raises if no API key."""
    load_dotenv()
    from openai import OpenAI

    if os.environ.get("NVIDIA_API_KEY"):
        client = OpenAI(
            base_url=os.environ.get("NVIDIA_BASE_URL", NVIDIA_NIM_BASE),
            api_key=os.environ["NVIDIA_API_KEY"],
        )
        model = os.environ.get("FITKG_CHAT_MODEL", DEFAULT_NIM_MODEL)
        return client, model, "nvidia-nim"
    if os.environ.get("OPENAI_API_KEY"):
        base = os.environ.get("OPENAI_BASE_URL")
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=base) if base else OpenAI(
            api_key=os.environ["OPENAI_API_KEY"]
        )
        model = os.environ.get("FITKG_CHAT_MODEL", DEFAULT_OPENAI_MODEL)
        return client, model, "openai"
    raise RuntimeError("Set NVIDIA_API_KEY or OPENAI_API_KEY in .env or environment")


def _llm_completion(client: Any, model: str, messages: List[Dict[str, str]]) -> str:
    temperature = float(os.environ.get("FITKG_LLM_TEMPERATURE", "0.6"))
    top_p = float(os.environ.get("FITKG_LLM_TOP_P", "0.7"))
    max_tokens = int(os.environ.get("FITKG_LLM_MAX_TOKENS", "1024"))
    stream = os.environ.get("FITKG_LLM_STREAM", "").lower() in ("1", "true", "yes")

    if stream:
        parts = []
        for chunk in client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=True,
        ):
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                parts.append(delta)
        return "".join(parts)

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


REL_EN = {
    "包含": "contains", "锻炼": "trains", "从属": "part of", "功能": "function",
    "实现": "achieves", "使用": "uses", "需要": "requires", "位置": "located at",
    "起点": "origin", "止点": "insertion", "形状": "shape",
}

# English body-part words → Chinese KG terms (FitKG labels are mostly Chinese)
BODY_PART_ALIASES: Dict[str, List[str]] = {
    "neck": ["颈", "颈椎", "颈部", "斜方肌", "胸锁乳突肌", "颈项"],
    "butt": ["臀", "臀大肌", "臀部", "髋"],
    "buttocks": ["臀", "臀大肌", "臀部"],
    "glute": ["臀", "臀大肌", "臀部"],
    "glutes": ["臀", "臀大肌", "臀部"],
    "arm": ["肱", "臂", "上臂", "前臂", "肱二头肌", "肱三头肌", "肱二", "肱三"],
    "arms": ["肱", "臂", "上臂", "前臂", "肱二头肌", "肱三头肌"],
    "bicep": ["肱二头肌", "肱二"],
    "biceps": ["肱二头肌", "肱二"],
    "tricep": ["肱三头肌", "肱三"],
    "triceps": ["肱三头肌", "肱三"],
    "forearm": ["前臂", "腕", "肘"],
    "shoulder": ["肩", "三角肌", "肩关节", "肩部"],
    "chest": ["胸", "胸大肌", "胸部", "肋"],
    "back": ["背", "背阔肌", "斜方肌", "竖脊肌", "背阔"],
    "leg": ["腿", "大腿", "股四头肌", "小腿", "股四"],
    "legs": ["腿", "大腿", "股四头肌", "小腿"],
    "thigh": ["大腿", "股四", "腘绳", "股四头肌"],
    "calf": ["小腿", "腓肠", "比目鱼", "腓肠肌"],
    "abs": ["腹", "腹直肌", "核心", "腹部"],
    "core": ["腹", "核心", "腹直肌"],
    "hip": ["髋", "臀", "髋关节", "骨盆"],
    "waist": ["腰", "腹", "核心"],
    "head": ["头", "颅"],
}

# Exercises / equipment → Chinese hints
EN_QUERY_HINTS: Dict[str, List[str]] = {
    **BODY_PART_ALIASES,
    "squat": ["深蹲", "蹲", "squat"],
    "swim": ["游泳", "泳"],
    "swimming": ["游泳", "泳"],
    "dumbbell": ["哑铃"],
    "barbell": ["杠铃"],
    "run": ["跑", "跑步"],
    "running": ["跑", "跑步"],
    "lunge": ["弓步", "跨步"],
    "deadlift": ["硬拉"],
    "press": ["推举", "推"],
    "curl": ["弯举", "曲"],
    "pushup": ["俯卧撑"],
    "push-up": ["俯卧撑"],
}

BODY_NODE_TYPES = frozenset({"身体部位", "解剖结构"})

# Keywords → SVG body region ids (bilateral where noted)
REGION_RULES: List[Tuple[str, List[str]]] = [
    (r"bicep|tricep|肱二|肱三|forearm|前臂|腕|wrist|elbow|肘", ["arm_l", "arm_r"]),
    (r"shoulder|肩|三角肌|deltoid", ["shoulder_l", "shoulder_r"]),
    (r"chest|胸|pectoral|肋", ["chest"]),
    (r"ab|腹|core|腰|腹直", ["abs"]),
    (r"back|背|latissimus|背阔|斜方|trap|spine|脊", ["upper_back", "lower_back"]),
    (r"glute|臀|hip flex", ["glutes"]),
    (r"quad|股四|thigh|大腿|膝|knee", ["thigh_l", "thigh_r"]),
    (r"calf|小腿|踝|ankle|胫", ["calf_l", "calf_r"]),
    (r"neck|颈|头|head", ["neck", "head"]),
    (r"hamstring|腘绳", ["thigh_l", "thigh_r"]),
]


class FitKGRAG:
    def __init__(self):
        self.graph = json.load(open(OUT / "graph.json", encoding="utf-8"))
        self.nodes = {n["id"]: n for n in self.graph["nodes"]}
        self.search = json.load(open(OUT / "search_index.json", encoding="utf-8"))
        self.adj: Dict[str, List[Dict]] = {}
        for e in self.graph["edges"]:
            self.adj.setdefault(e["source"], []).append(e)
            self.adj.setdefault(e["target"], []).append({**e, "_rev": True})

        rag_path = OUT / "rag_index.json"
        self.passages: List[Dict] = []
        self.entity_passages: Dict[str, List[int]] = {}
        self.triples: List[Dict] = []
        if rag_path.is_file():
            rag = json.load(open(rag_path, encoding="utf-8"))
            self.passages = rag.get("passages", [])
            self.entity_passages = rag.get("entity_passages", {})
            self.triples = rag.get("triples", [])

    def _display(self, n: Dict) -> str:
        return n.get("display_label") or n.get("label_en") or n.get("label", "")

    def _query_language(self, query: str) -> str:
        """'en' unless the user wrote mainly Chinese."""
        if not query.strip():
            return "en"
        cjk = sum(1 for c in query if "\u4e00" <= c <= "\u9fff")
        return "zh" if cjk >= max(2, len(query.strip()) // 3) else "en"

    def _format_node_line(self, n: Dict, lang: str) -> str:
        zh = n.get("label_zh") or n.get("label", "")
        en = (n.get("label_en") or "").strip()
        type_en = n.get("type_en") or n.get("type", "")
        if lang == "en":
            primary = en if en else self._display(n)
            if zh and zh != primary and not primary.endswith(zh):
                return f"- **{primary}** (Chinese: {zh}) — {type_en}"
            return f"- **{primary}** — {type_en}"
        return f"- **{self._display(n)}** ({zh}) — {type_en}"

    def entity_to_regions(self, zh: str, en: str = "") -> List[str]:
        try:
            from fitkg_body_map import regions_from_text
            found = regions_from_text(zh, en)
            if found:
                return found
        except ImportError:
            pass
        blob = f"{zh} {en}".lower()
        out = []
        for pat, regs in REGION_RULES:
            if re.search(pat, blob, re.I):
                out.extend(regs)
        return sorted(set(out))

    @staticmethod
    def _is_cjk(s: str) -> bool:
        return bool(re.search(r"[\u4e00-\u9fff]", s))

    def _body_hints(self, query: str) -> List[str]:
        q = query.lower().strip()
        out: List[str] = []
        if q in BODY_PART_ALIASES:
            out.extend(BODY_PART_ALIASES[q])
        for w in re.split(r"\W+", q):
            if w in BODY_PART_ALIASES:
                out.extend(BODY_PART_ALIASES[w])
        return list(dict.fromkeys(out))

    def _query_terms(self, query: str) -> List[str]:
        q = query.lower().strip()
        terms = [t for t in re.split(r"\W+", q) if len(t) > 1]
        extra = list(self._body_hints(query))
        for t in terms:
            extra.extend(EN_QUERY_HINTS.get(t, []))
            for key, hints in EN_QUERY_HINTS.items():
                if len(key) >= 4 and key in t:
                    extra.extend(hints)
        return list(dict.fromkeys(terms + extra))

    def _collect_index_ids(self, query: str, terms: List[str]) -> set:
        """Index lookup without 2-letter substring noise on English queries."""
        ids: set = set()
        for hint in self._body_hints(query):
            ids.update(self.search.get(hint, []))
        for term in terms:
            tl = term.lower()
            if self._is_cjk(term) or len(tl) >= 3:
                ids.update(self.search.get(tl, []))
        q = query.lower().strip()
        if self._is_cjk(q) or any(self._is_cjk(t) for t in terms):
            for i in range(len(q), 1, -1):
                if i < 2:
                    continue
                for j in range(len(q) - i + 1):
                    sub = q[j : j + i]
                    ids.update(self.search.get(sub, []))
        return ids

    def _scan_nodes_by_hints(self, query: str, hints: List[str], limit: int = 12) -> List[Dict]:
        q = query.lower().strip()
        scored: List[Tuple[float, Dict]] = []
        for n in self.graph["nodes"]:
            zh = n.get("label_zh") or n.get("label") or ""
            en = (n.get("label_en") or "").lower()
            disp = self._display(n).lower()
            score = float(n.get("count", 1)) * 0.05
            if n.get("type") in BODY_NODE_TYPES:
                score += 15
            for h in hints:
                if h in zh or (en and h.lower() in en) or h.lower() in disp:
                    score += 120
            if len(q) >= 3 and (q in en or q in disp or en.startswith(q)):
                score += 50
            if score > 20:
                scored.append((score, n))
        scored.sort(key=lambda x: -x[0])
        return [n for _, n in scored[:limit]]

    def match_nodes(self, query: str, k: int = 8) -> List[Dict]:
        q = query.lower().strip()
        terms = self._query_terms(query)
        hints = self._body_hints(query)
        ids = self._collect_index_ids(query, terms)
        for t in self.triples:
            if not any(
                term.lower() in (t.get("head_zh") or "").lower()
                or term.lower() in (t.get("tail_zh") or "").lower()
                or term.lower() in (t.get("head_en") or "").lower()
                or term.lower() in (t.get("tail_en") or "").lower()
                for term in terms
            ):
                continue
            for zh in (t.get("head_zh"), t.get("tail_zh")):
                if not zh:
                    continue
                for n in self.graph["nodes"]:
                    if (n.get("label_zh") or n.get("label")) == zh:
                        ids.add(n["id"])
                        break
        scored = []
        for nid in ids:
            n = self.nodes.get(nid)
            if not n:
                continue
            scored.append((self._score_node(n, q, terms, hints), n))
        if hints or len(scored) < k:
            for n in self._scan_nodes_by_hints(query, hints, limit=k * 2):
                if n["id"] not in ids:
                    scored.append((self._score_node(n, q, terms, hints), n))
        if len(scored) < k:
            for n in self.graph["nodes"]:
                if n["id"] in ids:
                    continue
                s = self._score_node(n, q, terms, hints)
                if s > 40:
                    scored.append((s, n))
        scored.sort(key=lambda x: -x[0])
        seen, out = set(), []
        for _, n in scored:
            if n["id"] in seen:
                continue
            seen.add(n["id"])
            out.append(n)
            if len(out) >= k:
                break
        return out

    def _score_node(self, n: Dict, q: str, terms: List[str], hints: Optional[List[str]] = None) -> float:
        label = self._display(n).lower()
        zh = (n.get("label_zh") or n.get("label", "")).lower()
        en = (n.get("label_en") or "").lower()
        score = float(n.get("count", 1))
        if n.get("type") in BODY_NODE_TYPES and hints:
            score += 25
        for term in terms:
            t = term.lower()
            if len(t) < 3 and not self._is_cjk(t):
                continue
            if t == zh or t in zh:
                score += 80
            if en and (t in en or t == en):
                score += 50
            if t in label and len(t) >= 3:
                score += 35
        for h in hints or []:
            if h in zh or (en and h.lower() in en):
                score += 100
        if q in BODY_PART_ALIASES and n.get("type") not in BODY_NODE_TYPES:
            score -= 30
        return score

    def neighborhood_triples(self, node_ids: List[str], limit: int = 12) -> List[str]:
        lines = []
        for nid in node_ids:
            for e in self.adj.get(nid, [])[:limit]:
                rev = e.get("_rev")
                src, tgt = (e["target"], e["source"]) if rev else (e["source"], e["target"])
                s, t = self.nodes.get(src), self.nodes.get(tgt)
                if not s or not t:
                    continue
                rel = REL_EN.get(e["type"], e.get("type_en", e["type"]))
                lines.append(f"• {self._display(s)} —[{rel}]→ {self._display(t)}")
        return list(dict.fromkeys(lines))[:limit]

    def retrieve_passages(self, query: str, nodes: List[Dict], k: int = 4) -> List[Dict]:
        if not self.passages:
            return []
        pids = set()
        for n in nodes:
            for key in (n.get("label_en", ""), n.get("label_zh", ""), n.get("label", "")):
                if key:
                    pids.update(self.entity_passages.get(key, []))
                    pids.update(self.entity_passages.get(f"{n.get('label_en','')}|{key}", []))
        q = query.lower()
        zh_terms = [t for t in self._query_terms(query) if self._is_cjk(t)]
        if len(pids) < k:
            for i, p in enumerate(self.passages):
                text = p["text_zh"].lower()
                ents = str(p.get("entities", "")).lower()
                if any(t in text or t in ents for t in zh_terms):
                    pids.add(i)
                elif any(w in text for w in q.split() if len(w) > 3):
                    pids.add(i)
        out = []
        for pid in sorted(pids)[:k]:
            if 0 <= pid < len(self.passages):
                out.append(self.passages[pid])
        return out

    def retrieve(self, query: str) -> Dict[str, Any]:
        nodes = self.match_nodes(query)
        try:
            from fitkg_body_map import resolve_query_regions
            regions = resolve_query_regions(query, nodes, graph=self.graph, adj=self.adj)
        except ImportError:
            regions = []
            for n in nodes:
                regions.extend(self.entity_to_regions(
                    n.get("label_zh") or n.get("label", ""),
                    n.get("label_en") or "",
                ))
            regions = sorted(set(regions))
        passages = self.retrieve_passages(query, nodes)
        triple_lines = self.neighborhood_triples([n["id"] for n in nodes])
        muscle_info = []
        try:
            from fitkg_body_map import regions_from_graph_node
            nodes_by_id = self.nodes
            seen = set()
            for n in nodes[:3]:
                if n["id"] in seen:
                    continue
                seen.add(n["id"])
                info = regions_from_graph_node(n["id"], nodes_by_id, self.adj)
                if info.get("muscles"):
                    muscle_info.append(info)
        except ImportError:
            pass
        return {
            "nodes": nodes,
            "regions": regions,
            "triples": triple_lines,
            "passages": passages,
            "muscle_info": muscle_info,
        }

    def _build_context_blocks(self, ctx: Dict[str, Any], lang: str) -> List[str]:
        nodes = ctx["nodes"]
        if lang == "zh":
            blocks = ["### 来自 FitKG 知识图谱\n"]
            concepts, rels, excerpts = "**匹配概念：**", "**关系：**", "**原文摘录：**"
        else:
            blocks = ["### FitKG knowledge graph context\n"]
            concepts, rels, excerpts = "**Matching concepts:**", "**Relationships:**", "**Source excerpts:**"

        if nodes:
            blocks.append(concepts)
            for n in nodes[:6]:
                blocks.append(self._format_node_line(n, lang))
        if ctx["triples"]:
            blocks.append(f"\n{rels}")
            blocks.extend(ctx["triples"][:8])
        if ctx["passages"]:
            blocks.append(f"\n{excerpts}")
            for p in ctx["passages"][:3]:
                en_ents = ", ".join(
                    f"{e.get('en') or e['zh']}" for e in p.get("entities", [])[:5]
                )
                blocks.append(f"> {p['text_zh'][:280]}…\n> _Entities: {en_ents}_")
        return blocks

    def answer(self, query: str, use_llm: bool = True) -> str:
        lang = self._query_language(query)
        ctx = self.retrieve(query)
        nodes = ctx["nodes"]
        if not nodes and not ctx["passages"]:
            if lang == "zh":
                return "在 FitKG 中未找到相关内容。可尝试：**二头肌**、**深蹲**、**游泳**、**哑铃**、**肩部** 等。"
            return (
                "I couldn't find that in FitKG. Try: **biceps**, **squat**, **swimming**, "
                "**dumbbell**, or a body region like **shoulder**."
            )

        blocks = self._build_context_blocks(ctx, lang)
        context_text = "\n".join(blocks)

        if use_llm and llm_configured():
            try:
                client, model, provider = get_llm_client()
                if lang == "zh":
                    system = (
                        "你是运动康复与健身指导助手。仅根据提供的 FitKG 图谱上下文回答。"
                        "用中文作答，简洁、实用、注意安全。"
                        "若上下文中有英文肌肉名，可保留英文并附中文。"
                    )
                    user = f"请用中文回答。\n\n问题：{query}\n\n上下文：\n{context_text}"
                else:
                    system = (
                        "You are a physiotherapy and fitness educator. Answer ONLY from the "
                        "FitKG context. The context may use Chinese labels — translate muscles, "
                        "exercises, and equipment into natural English for the user. "
                        "CRITICAL: Write the entire response in English only — no Chinese "
                        "characters. Translate every exercise name from the context into English "
                        "(e.g. 屈腿硬拉 → Romanian deadlift). "
                        "Structure: brief intro, key muscles, recommended exercises from "
                        "relationships (with English names), 2–3 practical tips. Be concise and safe."
                    )
                    user = (
                        f"Reply language: English only.\n\n"
                        f"User question: {query}\n\nContext:\n{context_text}"
                    )
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
                text = _llm_completion(client, model, messages)
                return text or context_text
            except Exception as ex:
                blocks.append(f"\n_(LLM unavailable: {ex})_")

        if lang == "zh":
            blocks.append("\n---\n**提示：** 在 `.env` 中配置 `NVIDIA_API_KEY` 并勾选 LLM 可获得更自然的回答。")
        else:
            blocks.append(
                "\n---\n**Tip:** Enable LLM in chat with `NVIDIA_API_KEY` in `.env` for a full English summary."
            )
        return "\n".join(blocks)


def get_rag() -> FitKGRAG:
    return FitKGRAG()
