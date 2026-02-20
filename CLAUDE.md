# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Python / FastAPI)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run dev server (from backend/)
uvicorn app.main:app --reload

# Ingest documents
curl -X POST http://localhost:8000/ingest

# Query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here"}'
```

### Frontend (Vite + React + TypeScript)
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # production build → frontend/dist/
```

## Architecture

```
backend/
  app/
    config.py    # All env-based settings (ANTHROPIC_API_KEY, paths, model names)
    ingest.py    # Load PDF/TXT/MD from data/ → split → embed → persist to Chroma
    rag.py       # Retrieve top-k chunks from Chroma → stream Claude response
    main.py      # FastAPI app: /health, /ingest, /chat (SSE), /documents
  data/          # Drop source documents here before ingesting
  chroma_db/     # Auto-created; Chroma persists embeddings here

frontend/
  src/
    App.tsx      # Single-page chat UI; streams SSE from /api/chat
    types.ts     # Message type (role + content)
  vite.config.ts # Proxies /api → http://localhost:8000
```

**Data flow:**
1. Drop files into `backend/data/` (PDF, TXT, or MD)
2. POST `/ingest` — documents are chunked, embedded with `all-MiniLM-L6-v2` (local, no API key), and stored in Chroma
3. POST `/chat` — query is embedded, top-5 chunks retrieved, passed as context to `claude-sonnet-4-6`, response is streamed back as SSE
4. Frontend reads the SSE stream and renders tokens incrementally

**Key configuration** (`backend/.env`):
- `ANTHROPIC_API_KEY` — required
- `CHROMA_PATH` — defaults to `chroma_db`
- `DATA_PATH` — defaults to `data`
- Model/chunk settings are constants in `config.py`

## First-time setup

```bash
cp backend/.env.example backend/.env
# edit backend/.env and add your ANTHROPIC_API_KEY
```
