import os
import sys

print(f"Python {sys.version}", flush=True)
print("Starting FastAPI app...", flush=True)

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

print("FastAPI imported OK", flush=True)

from app.ingest import ingest_documents, list_sources
from app.rag import retrieve_and_stream

print("App modules imported OK", flush=True)

app = FastAPI(title="jalin-rag-lab")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "https://www.jalinbright.com",
        "https://jalinbright.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


_INGEST_SECRET = os.getenv("INGEST_SECRET", "")


@app.post("/api/ingest")
def ingest(authorization: str = Header(default="")):
    if not _INGEST_SECRET or authorization != f"Bearer {_INGEST_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = ingest_documents()
    return result


@app.get("/api/documents")
def documents():
    return {"sources": list_sources()}


@app.post("/api/chat")
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
