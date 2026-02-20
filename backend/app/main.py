from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ingest import ingest_documents, list_sources
from app.rag import retrieve_and_stream

app = FastAPI(title="jalin-rag-lab")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest():
    result = ingest_documents()
    return result


@app.get("/documents")
def documents():
    return {"sources": list_sources()}


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    def event_stream():
        for chunk in retrieve_and_stream(req.query):
            # Escape newlines so SSE framing is never broken by content
            safe = chunk.replace("\n", "\\n")
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
