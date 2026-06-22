# PG-XFormer & FitKG Explorer: Home Physiotherapy Monitoring with Knowledge-Grounded AI

<p align="center">
  <img src="assets/banner.svg" alt="PG-XFormer and FitKG Explorer banner" width="100%"/>
</p>

This repository contains the **physio** research stack: **PG-XFormer** (pose-guided cross-modal exercise classification) and **FitKG Explorer** (interactive fitness knowledge graph with RAG + LLM chat, body map, and KIMORE clinical demos).

#### By: [Fatimah Mohamed Emad Elden](https://scholar.google.com/citations?user=CfX6eA8AAAAJ&hl=ar)

#### *Cairo University · MIUA Physiotherapy Monitoring*

[![Live Demo](https://img.shields.io/badge/Live_Demo-Vercel-000000?style=flat&logo=vercel&logoColor=white)](https://physio-x2pm.vercel.app/)
[![GitHub](https://img.shields.io/badge/GitHub-physio-blue)](https://github.com/astral-fate/physio)
[![Colab](https://img.shields.io/badge/Colab-Model_Training-F9AB00?style=flat&logo=googlecolab&logoColor=white)](https://colab.research.google.com/drive/1E64eBfdd6kSDk4Rt4GPmH4todzeCrJcg?usp=sharing)
[![FitKG-CN](https://img.shields.io/badge/FitKG--CN-Knowledge_Graph-3d8bfd)](https://github.com/NYN921/FitKG-CN)

---

## Platform links

| Platform | Description | Link |
|----------|-------------|------|
| **Knowledge graph** | FitKG Explorer — graph search, RAG chat, body map, KIMORE demos | [physio-tau-eight.vercel.app](https://physio-tau-eight.vercel.app/) |
| **Model training** | PG-XFormer Colab pipeline (InfiniteRep → KIMORE → UI-PRMD) | [Google Colab](https://colab.research.google.com/drive/1E64eBfdd6kSDk4Rt4GPmH4todzeCrJcg?usp=sharing) |
| **B2B landing page** | Clinical / product landing (Faqarati) | [faqarati.run.app](https://faqarati-403347311270.europe-west2.run.app/) |

> **Note:** Latest deploy with graph fixes: [physio-x2pm.vercel.app](https://physio-x2pm.vercel.app/) · API health: [/api/health](https://physio-x2pm.vercel.app/api/health)

---

## Platform interface previews & gallery

Explore the live **FitKG Explorer** workspace and related platform surfaces. *Replace placeholder SVGs in `assets/` with your screenshots (`kg-graph.png`, `rag-chat.png`, etc.) and update the `src` paths below.*

<table width="100%">
  <tr>
    <td width="50%" valign="top" align="center">
      <h4>FitKG Knowledge Graph (8k+ nodes)</h4>
      <a href="https://physio-tau-eight.vercel.app/"><img src="assets/kg-graph.svg" width="100%" alt="Knowledge graph explorer" style="border-radius: 6px; border: 1px solid #2d3a4d;"/></a>
      <p align="left"><small>Interactive vis.js subgraph — English search over FitKG-CN entities, relations, and 2-hop neighborhoods.</small></p>
    </td>
    <td width="50%" valign="top" align="center">
      <h4>RAG + LLM Assistant</h4>
      <a href="https://physio-tau-eight.vercel.app/"><img src="assets/rag-chat.svg" width="100%" alt="RAG chat panel" style="border-radius: 6px; border: 1px solid #2d3a4d;"/></a>
      <p align="left"><small>Grounded chat over 11k+ passages — optional NVIDIA NIM / OpenAI synthesis with graph + body-map highlights.</small></p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top" align="center">
      <h4>Anatomical Body Map</h4>
      <a href="https://physio-tau-eight.vercel.app/"><img src="assets/body-map.svg" width="100%" alt="SVG body map" style="border-radius: 6px; border: 1px solid #2d3a4d;"/></a>
      <p align="left"><small>22-region anterior/posterior SVG — muscles highlight from RAG retrieval and graph node selection.</small></p>
    </td>
    <td width="50%" valign="top" align="center">
      <h4>KIMORE Clinical Pose Demo</h4>
      <a href="https://physio-tau-eight.vercel.app/"><img src="assets/kimore-pose.svg" width="100%" alt="KIMORE pose player" style="border-radius: 6px; border: 1px solid #2d3a4d;"/></a>
      <p align="left"><small>COCO-17 synthetic animations for 5 rehab classes with FitKG muscle context and therapist-style cues.</small></p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top" align="center">
      <h4>PG-XFormer Model Training</h4>
      <a href="https://colab.research.google.com/drive/1E64eBfdd6kSDk4Rt4GPmH4todzeCrJcg?usp=sharing"><img src="assets/model-training.svg" width="100%" alt="Colab training pipeline" style="border-radius: 6px; border: 1px solid #2d3a4d;"/></a>
      <p align="left"><small>Sim-to-real pipeline: pretrain on InfiniteRep synthetic data, fine-tune on KIMORE, evaluate on UI-PRMD.</small></p>
    </td>
    <td width="50%" valign="top" align="center">
      <h4>B2B Clinical Landing Page</h4>
      <a href="https://faqarati-403347311270.europe-west2.run.app/"><img src="assets/b2b-landing.svg" width="100%" alt="B2B landing page" style="border-radius: 6px; border: 1px solid #2d3a4d;"/></a>
      <p align="left"><small>Product-facing clinical landing for physiotherapy / rehab deployment scenarios.</small></p>
    </td>
  </tr>
</table>

---

## Table of contents

1. [Problem & solution](#problem--solution)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Technology stack](#technology-stack)
5. [Knowledge graph results](#knowledge-graph-results)
6. [RAG pipeline](#rag-pipeline)
7. [LLM prompts & safety](#llm-prompts--safety)
8. [KIMORE rehab bridge](#kimore-rehab-bridge)
9. [Body map & muscle highlighting](#body-map--muscle-highlighting)
10. [API reference](#api-reference)
11. [Deployment](#deployment)
12. [Environment variables](#environment-variables)
13. [Local development](#local-development)
14. [Project structure](#project-structure)
15. [Research context (PG-XFormer)](#research-context-pg-xformer)
16. [License & attribution](#license--attribution)

---

## Problem & solution

### Problem

Patients often perform **home physiotherapy exercises without supervision**. Clinicians and researchers need tools that can:

- Explain **which muscles** an exercise trains
- Ground answers in **structured medical/fitness knowledge**, not hallucinated anatomy
- Connect **clinical movement datasets** (e.g. KIMORE) to readable, interactive education
- Be **demoable** to collaborators via a public URL

### Solution

**physio** delivers a web application with four integrated layers:

| Layer | What it does |
|-------|----------------|
| **Knowledge graph** | Search & explore 8k+ FitKG entities (muscles, exercises, equipment) in English |
| **RAG retrieval** | Pull relevant passages + triples from 11k+ annotated fitness documents |
| **LLM synthesis** | Optional NVIDIA NIM / OpenAI chat that answers **only** from retrieved context |
| **Clinical bridge** | KIMORE rehab classes → pose animation, muscle highlights, therapist-style cues |

The system is **grounded by design**: the LLM receives FitKG subgraph context and is instructed not to invent facts beyond it.

---

## Architecture

```mermaid
flowchart TB
    subgraph UI["Browser — fitkg_graph_ui"]
        Graph["Graph explorer vis.js"]
        Chat["RAG chat panel"]
        Body["SVG body map"]
        Kimore["KIMORE pose player"]
    end

    subgraph API["API — api/index.py"]
        Health["GET /api/health"]
        ChatAPI["POST /api/chat"]
        Muscles["GET /api/muscles"]
        KimoreAPI["GET /api/kimore"]
    end

    subgraph Core["Python core"]
        RAG["fitkg_rag.py"]
        BodyMap["fitkg_body_map.py"]
        Bridge["fitkg_kimore_bridge.py"]
        LLM["NVIDIA NIM / OpenAI"]
    end

    subgraph Data["outputs/fitkg_kg"]
        G["graph.json"]
        S["search_index.json"]
        R["rag_index.json"]
        M["muscle_region_map.json"]
        K["kimore_pose_demos.json"]
    end

    UI --> API
    ChatAPI --> RAG
    Muscles --> BodyMap
    KimoreAPI --> Bridge
    RAG --> G
    RAG --> S
    RAG --> R
    RAG --> LLM
    BodyMap --> M
    Bridge --> RAG
    Bridge --> K
    Graph --> G
    Graph --> S
```

### Request flow (chat example)

1. User asks *"What muscles does squat train?"* in the chat panel.
2. `POST /api/chat` → `FitKGRAG.retrieve()`:
   - English query hints → Chinese KG terms (`squat` → 深蹲)
   - Search index → matching nodes
   - 2-hop neighborhood → relation triples
   - Passage index → top fitness text excerpts
   - Body map → `regions: [thigh_l, thigh_r, glutes, abs, lower_back]`
3. If LLM enabled → context blocks sent with **grounded system prompt** → natural English answer.
4. UI highlights body regions and selects matching graph nodes.

---

## Components

### Web UI (`fitkg_graph_ui/`)

| Feature | Description |
|---------|-------------|
| **Graph explorer** | English search, entity/relation filters, 2-hop vis.js subgraph |
| **Detail panel** | Node metadata (ZH + EN labels, types) |
| **RAG chat** | Bottom-right FAB; optional LLM checkbox |
| **Body viewer** | Anterior/posterior SVG; regions highlight from chat or KIMORE |
| **KIMORE panel** | 5 clinical exercises; play COCO-17 pose sequence + cue text |

### Backend services

| Module | Role |
|--------|------|
| `fitkg_serve.py` | Local dev server (port 8766): static files + REST API |
| `api/*.py` | Vercel serverless equivalents of the same endpoints |
| `fitkg_rag.py` | Graph search, passage retrieval, LLM answer generation |
| `fitkg_body_map.py` | Graph node → anatomical region resolution |
| `fitkg_body_svg.py` | SVG body renderer + region queries |
| `fitkg_kimore_bridge.py` | KIMORE classes ↔ FitKG muscles + synthetic pose demos |
| `fitkg_assistant.py` | Alternative Streamlit UI (local) |

### Data pipeline (build once)

| Script | Output |
|--------|--------|
| `fitkg_eda.py` | `graph.json`, `search_index.json`, EDA tables |
| `fitkg_translate_labels.py` | `label_translations_en.json` (cached EN labels) |
| `fitkg_build_rag_index.py` | `rag_index.json` (passages + triples + entity links) |

> **Note:** Pre-built artifacts are committed under `outputs/fitkg_kg/` so Vercel deploys work without rebuilding from raw FitKG source.

---

## Technology stack

| Category | Technology |
|----------|------------|
| **Knowledge base** | FitKG-CN (Chinese fitness KG, SpERT extraction) |
| **Graph UI** | HTML/CSS/JS, [vis-network](https://visjs.github.io/vis-network/) |
| **Body map** | Custom SVG (`fitkg_body_svg.py`, `body_viewer.js`) |
| **RAG** | Keyword + graph traversal (no vector DB); JSON indexes |
| **LLM** | [NVIDIA NIM](https://build.nvidia.com/) (default: `qwen/qwen3-next-80b-a3b-instruct`) or OpenAI-compatible API |
| **Pose demos** | Synthetic COCO-17 keypoints (NumPy); KIMORE clinical presets |
| **Local server** | Python `http.server` threading (`fitkg_serve.py`) |
| **Cloud** | [Vercel](https://vercel.com) Python serverless + static hosting |
| **Tunnel demo** | ngrok (`run_fitkg_ngrok.ps1`) |

### Python dependencies

```
openai>=1.0      # LLM client (NIM + OpenAI)
numpy>=1.24      # KIMORE pose generation
streamlit>=1.28  # optional: fitkg_assistant.py
deep-translator  # optional: label translation
```

---

## Knowledge graph results

Built from FitKG-CN `train.json` + `dev.json` (see `outputs/fitkg_kg/eda_summary.md`).

### Scale

| Metric | Value |
|--------|------:|
| Documents | **11,544** |
| Unique entities (nodes) | **8,043** |
| Unique relations (edges) | **13,510** |
| Entity mentions | **26,494** |
| Relation mentions | **15,455** |
| RAG passages indexed | **11,544** |
| Deployed data size | ~18 MB (`graph.json` + `search_index.json` + `rag_index.json`) |

### Entity types

| Chinese | English | Count |
|---------|---------|------:|
| 身体部位 | Body part | 6,954 |
| 运动项目 | Sport / activity | 4,940 |
| 专业名词 | Term | 4,408 |
| 运动目标 | Training goal | 3,032 |
| 健身动作 | Exercise | 2,892 |
| 器械工具 | Equipment | 1,733 |
| 解剖结构 | Anatomy | 1,716 |
| 营养物质 | Nutrient | 819 |

### Top relation types

| Relation | English | Count |
|----------|---------|------:|
| 包含 | Contains | 4,196 |
| 锻炼 | **Trains** | 2,619 |
| 从属 | Part-of | 2,284 |
| 实现 | Achieves | 1,660 |
| 功能 | Function | 1,630 |
| 使用 | Uses | 948 |

### Frequently referenced entities (by document frequency)

Go, Legs, aerobics, triceps brachii, pectoralis major, biceps brachii, dumbbell, deltoid, barbell, latissimus dorsi, rectus abdominis, gluteus maximus.

---

## RAG pipeline

### Retrieval (`FitKGRAG.retrieve`)

1. **Query expansion** — English body-part aliases and exercise hints mapped to Chinese KG terms (`BODY_PART_ALIASES`, `EN_QUERY_HINTS` in `fitkg_rag.py`).
2. **Node matching** — `search_index.json` inverted index (substring + CJK n-grams).
3. **Graph neighborhood** — Up to 2-hop edges from matched nodes; triples formatted as `head —[trains]→ tail`.
4. **Passage retrieval** — Documents linked to matched entities via `entity_passages` in `rag_index.json`.
5. **Region resolution** — `fitkg_body_map.resolve_query_regions()` → SVG region IDs for highlighting.

### Index build (`fitkg_build_rag_index.py`)

- Reads annotated FitKG JSON (entities + relations per document)
- Stores passage text (≤800 chars), entity links, deduplicated triples
- Links English translations when `label_translations_en.json` exists

### Retrieval-only vs LLM mode

| Mode | Behavior |
|------|----------|
| `use_llm: false` | Returns formatted markdown: matched concepts, relationships, source excerpts |
| `use_llm: true` | Same context → LLM produces concise, structured natural language |

---

## LLM prompts & safety

Configuration via `.env` (see [Environment variables](#environment-variables)). Default provider: **NVIDIA NIM**.

### English system prompt (grounded)

```
You are a physiotherapy and fitness educator. Answer ONLY from the FitKG context.
The context may use Chinese labels — translate muscles, exercises, and equipment
into natural English for the user.
CRITICAL: Write the entire response in English only — no Chinese characters.
Translate every exercise name from the context into English
(e.g. 屈腿硬拉 → Romanian deadlift).
Structure: brief intro, key muscles, recommended exercises from relationships
(with English names), 2–3 practical tips. Be concise and safe.
```

### Chinese system prompt

```
你是运动康复与健身指导助手。仅根据提供的 FitKG 图谱上下文回答。
用中文作答，简洁、实用、注意安全。
若上下文中有英文肌肉名，可保留英文并附中文。
```

### Safety principles

- **Context-only answers** — no free-form medical diagnosis
- **Fallback** — if LLM fails, user still sees retrieved KG context
- **Temperature** — default `0.6` (configurable); retrieval is deterministic
- **No diagnosis** — KIMORE cues are educational (*"focus on quadriceps, glutes…"*), not clinical verdicts

### LLM parameters (`.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `FITKG_CHAT_MODEL` | `qwen/qwen3-next-80b-a3b-instruct` | NIM model ID |
| `FITKG_LLM_TEMPERATURE` | `0.6` | Response creativity |
| `FITKG_LLM_TOP_P` | `0.7` | Nucleus sampling |
| `FITKG_LLM_MAX_TOKENS` | `1024` | Max response length (use `512` on Vercel Hobby) |

---

## KIMORE rehab bridge

Connects **clinical rehabilitation exercise classes** from the KIMORE dataset to FitKG knowledge and UI visualization.

### Supported classes

| Class ID | English | Primary muscles |
|----------|---------|-----------------|
| `squat` | Squat | Quadriceps, gluteus maximus, erector spinae, core |
| `sit_to_stand` | Sit-to-stand | Quadriceps, gluteus maximus, rectus abdominis |
| `unilateral_stance` | Unilateral stance | Gluteus medius, quadriceps, gastrocnemius, core |
| `pelvis_tilt` | Pelvis tilt | Rectus abdominis, gluteus maximus, erector spinae, hip flexors |
| `trunk_flexion` | Trunk flexion | Rectus abdominis, hip flexors, erector spinae |

### What `/api/kimore/demo` returns

- 16-frame **COCO-17** keypoint sequence (synthetic, clinically styled)
- Skeleton edges for canvas rendering
- FitKG retrieval for exercise-specific Chinese query (e.g. 深蹲)
- Matching graph nodes + triples
- **Cue text** — short English coaching line grounded in preset muscles

Example cue:

> *Squat: focus on quadriceps, gluteus maximus, erector spinae, core. Keep controlled tempo and stable alignment.*

---

## Body map & muscle highlighting

### Regions (`muscle_region_map.json`)

**22 anatomical regions** with bilateral arms/legs, anterior + posterior views:

`head`, `neck`, `chest`, `shoulder_l/r`, `biceps_l/r`, `triceps_l/r`, `forearm_l/r`, `abs`, `obliques`, `upper_back`, `mid_back`, `lower_back`, `glutes`, `hip_flexor`, `thigh_l/r`, `calf_l/r`

Each region maps to **FitKG keywords** (Chinese + English) for automatic highlighting when RAG retrieves matching anatomy.

### Highlight triggers

1. **Chat response** — `regions` array in `/api/chat` JSON
2. **Graph node click** — `/api/muscles?node_id=…`
3. **KIMORE demo** — preset regions per exercise class

---

## API reference

Base URL: **https://physio-x2pm.vercel.app** (local: `http://127.0.0.1:8766`)

| Endpoint | Method | Parameters / body | Response |
|----------|--------|-------------------|----------|
| `/api/health` | GET | — | `{ server, ok, rag_index, graph, llm, llm_provider }` |
| `/api/chat` | POST | `{ "query": "squat muscles", "use_llm": true }` | `{ reply, nodes, regions, muscle_info, passage_count }` |
| `/api/muscles` | GET | `?node_id=<id>` | `{ regions, muscles, … }` |
| `/api/kimore` | GET | — | `{ classes: [...] }` |
| `/api/kimore/demo` | GET | `?class=squat` | Pose sequence, edges, FitKG context, cue |
| `/api/kimore/feedback` | POST | `{ "exercise_class": "squat", "confidence": 0.9 }` | Highlighted regions, muscles, cue |

### Example: chat request

```bash
curl -X POST https://physio-x2pm.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"what does squat train?","use_llm":true}'
```

### Static assets

| Path | Content |
|------|---------|
| `/fitkg_graph_ui/index.html` | Main application |
| `/outputs/fitkg_kg/graph.json` | Full knowledge graph |
| `/outputs/fitkg_kg/search_index.json` | Search inverted index |

---

## Deployment

### Vercel (recommended for public demos)

1. Import [astral-fate/physio](https://github.com/astral-fate/physio) at [vercel.com/new](https://vercel.com/new)
2. Add `NVIDIA_API_KEY` in Project → Settings → Environment Variables → **Redeploy**
3. Open **https://physio-x2pm.vercel.app/** (or your Vercel URL)

`api/index.py` (FastAPI) serves the UI, KG JSON files, and all `/api/*` routes on Vercel.

```powershell
.\run_vercel.ps1 --prod   # requires Vercel CLI + Node.js
```

### ngrok (local tunnel)

```powershell
ngrok config add-authtoken YOUR_TOKEN   # once
.\run_fitkg_ngrok.ps1
```

Shares a temporary public URL while your machine runs `fitkg_serve.py`.

### Local

```powershell
pip install -r requirements.txt
copy .env.example .env    # add NVIDIA_API_KEY
.\run_fitkg.ps1
```

Open: http://127.0.0.1:8766/fitkg_graph_ui/index.html

> **Important:** Do not use `python -m http.server` — the chat API requires `fitkg_serve.py`.

---

## Environment variables

Copy `.env.example` → `.env` for local dev. On Vercel, set the same keys in **Project → Settings → Environment Variables** (then **Redeploy**).

| Variable | Required | Notes |
|----------|----------|-------|
| `NVIDIA_API_KEY` | For LLM chat | From [build.nvidia.com](https://build.nvidia.com/) |
| `FITKG_CHAT_MODEL` | Optional | Default `qwen/qwen3-next-80b-a3b-instruct` |

Verify LLM after deploy: `GET /api/health` should show `"llm": true`. If still `false`, check the variable name is exact (not `NIM_API_KEY`) and redeploy.

```env
# NVIDIA NIM (recommended)
NVIDIA_API_KEY=your_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
FITKG_CHAT_MODEL=qwen/qwen3-next-80b-a3b-instruct
FITKG_LLM_TEMPERATURE=0.6
FITKG_LLM_TOP_P=0.7
FITKG_LLM_MAX_TOKENS=1024

# Or OpenAI-compatible (alternative)
# OPENAI_API_KEY=sk-...
# FITKG_CHAT_MODEL=gpt-4o-mini
```

---

## Local development

### Full rebuild (from FitKG source)

Requires `NYN921-FitKG-CN-41b1142/data/fitkg-cn/` (not in this repo — download FitKG-CN separately).

```powershell
python fitkg_eda.py
python fitkg_translate_labels.py   # ~10–20 min, caches translations
python fitkg_eda.py                # rebuild graph with English labels
python fitkg_build_rag_index.py
.\run_fitkg.ps1
```

### Streamlit assistant (alternative UI)

```powershell
pip install streamlit
streamlit run fitkg_assistant.py
```

### Push updates to GitHub

```powershell
.\push_github.ps1   # pushes to astral-fate/physio
```

---

## Project structure

```
physio/
├── api/index.py              # Vercel FastAPI entrypoint (all /api/* routes)
├── scripts/vercel_build.py   # Copies UI + KG JSON → public/ at deploy
├── fitkg_api_common.py       # Shared API helpers
├── fitkg_graph_ui/           # Web application (HTML/JS)
│   ├── index.html
│   └── body_viewer.js
├── outputs/fitkg_kg/         # Built KG + RAG artifacts (deployed to Vercel)
│   ├── graph.json
│   ├── search_index.json
│   ├── rag_index.json
│   ├── muscle_region_map.json
│   └── kimore_pose_demos.json
├── fitkg_rag.py              # RAG + LLM core
├── fitkg_serve.py            # Local HTTP server
├── fitkg_kimore_bridge.py    # KIMORE ↔ FitKG bridge
├── fitkg_body_map.py         # Anatomy region mapping
├── fitkg_body_svg.py         # SVG body renderer
├── fitkg_build_rag_index.py  # RAG index builder
├── fitkg_eda.py              # Graph EDA + export
├── fitkg_assistant.py        # Streamlit UI
├── vercel.json               # Vercel config
├── requirements.txt
├── run_fitkg.ps1             # Local server launcher
├── run_fitkg_ngrok.ps1       # ngrok tunnel launcher
├── run_vercel.ps1            # Vercel deploy helper
├── push_github.ps1           # GitHub push helper
└── PROJECT_OVERVIEW.md       # PG-XFormer research pipeline (separate track)
```

---

## Research context (PG-XFormer)

This repository's **deployed demo** focuses on **FitKG Explorer** (knowledge + RAG + body map + KIMORE education).

The broader **physiotherapy monitoring research** — video + skeleton classification with PG-XFormer across InfiniteRep → KIMORE → UI-PRMD — is documented in [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md). That pipeline includes:

- **PG-XFormer** — pose-guided cross-modal transformer (CTR-GCN + VideoMAE)
- **Sim-to-real training** — pretrain on synthetic InfiniteRep, fine-tune on clinical KIMORE
- **Planned agentic layer** — VAE anomaly detection → kinematic error report → guarded LLM cues

The KIMORE bridge in this repo provides the **educational / explainability** layer that complements exercise classification research.

---

## License & attribution

- **FitKG-CN** knowledge graph: see [NYN921/FitKG-CN](https://github.com/NYN921/FitKG-CN) and original dataset license.
- **KIMORE** exercise classes: clinical rehabilitation benchmark (referenced for demo presets).
- **Application code** in this repository: developed for the physio / MIUA research project.

---

## Quick links

| Resource | URL |
|----------|-----|
| **Knowledge graph (live)** | https://physio-tau-eight.vercel.app/ |
| **Latest Vercel deploy** | https://physio-x2pm.vercel.app/ |
| **Model training (Colab)** | https://colab.research.google.com/drive/1E64eBfdd6kSDk4Rt4GPmH4todzeCrJcg?usp=sharing |
| **B2B landing page** | https://faqarati-403347311270.europe-west2.run.app/ |
| GitHub | https://github.com/astral-fate/physio |
| API health | https://physio-x2pm.vercel.app/api/health |
| NVIDIA NIM API keys | https://build.nvidia.com/ |
