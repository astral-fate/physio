# physio — FitKG Explorer

Interactive fitness knowledge graph with RAG chat, body map, and KIMORE rehab pose demos.

**Live demo:** deploy to [Vercel](https://vercel.com) from this repo.

## Features

- Knowledge graph search (FitKG-CN, English labels)
- RAG retrieval over 11k+ passages
- LLM chat (NVIDIA NIM or OpenAI)
- Anatomical body map + muscle highlighting
- KIMORE exercise pose animations + cues

## Deploy on Vercel

1. Import this repo at [vercel.com/new](https://vercel.com/new)
2. Add environment variables: `NVIDIA_API_KEY` (and optional `FITKG_CHAT_MODEL`)
3. Deploy — open `/fitkg_graph_ui/index.html`

## Local dev

```powershell
pip install -r requirements.txt
python fitkg_build_rag_index.py   # if outputs/fitkg_kg/rag_index.json missing
.\run_fitkg.ps1
```

Open http://127.0.0.1:8766/fitkg_graph_ui/index.html

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | RAG + LLM status |
| `/api/chat` | POST | RAG chat (`query`, `use_llm`) |
| `/api/muscles` | GET | Muscle regions (`node_id`) |
| `/api/kimore` | GET | Exercise catalog |
| `/api/kimore/demo` | GET | Pose demo (`class=squat`) |
| `/api/kimore/feedback` | POST | Live rep feedback |
