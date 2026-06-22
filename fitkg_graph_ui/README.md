# FitKG Explorer

Interactive search UI for the **FitKG-CN** fitness knowledge graph.

## 1. Build the graph + English labels

```bash
python fitkg_eda.py
python fitkg_translate_labels.py   # ~10–20 min once; caches translations
python fitkg_eda.py                # rebuild graph with label_en fields
```

Outputs: `outputs/fitkg_kg/graph.json`, `search_index.json`, `label_translations_en.json`

## 2. Start the UI (graph + chat)

From the **physui** project root:

```bash
python fitkg_build_rag_index.py   # once
```

**Windows (recommended):**

```powershell
cd D:\physui
.\run_fitkg.ps1
```

Or: `python fitkg_serve.py` → open **http://127.0.0.1:8766/fitkg_graph_ui/index.html** (port **8766** on purpose).

Click the **blue chat button** (bottom-right) for RAG + NVIDIA NIM.

**Do not** use `python -m http.server 8765` for chat — it causes `Got HTML instead of JSON` if your browser hits port 8765 instead of 8766.

## Interactive assistant (recommended)

RAG chat + body map + muscle highlighting:

```bash
pip install streamlit openai
python fitkg_build_rag_index.py
streamlit run fitkg_assistant.py
```

**LLM (optional):** copy `.env.example` → `.env` and set `NVIDIA_API_KEY` for [NVIDIA NIM](https://build.nvidia.com/) (default model `qwen/qwen3-next-80b-a3b-instruct`), or `OPENAI_API_KEY` for OpenAI. Enable the checkbox in chat.

## Static graph explorer

- Search in **English** (after `fitkg_translate_labels.py`)
- Filter by entity/relation type
- 2-hop graph (vis.js)
