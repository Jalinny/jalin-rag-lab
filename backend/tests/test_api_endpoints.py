"""
Tests for the FastAPI endpoints defined in app/main.py.

All tests patch the three callables that app.main imports — retrieve_and_stream,
ingest_documents, and list_sources — so no real Chroma, HuggingFace, or
Anthropic I/O occurs.

Endpoints under test:
  GET  /health
  POST /ingest
  GET  /documents
  POST /chat
"""

from unittest.mock import patch

import pytest

# Patch targets match the names imported into app.main's namespace.
_PATCH_RETRIEVE = "app.main.retrieve_and_stream"
_PATCH_INGEST = "app.main.ingest_documents"
_PATCH_SOURCES = "app.main.list_sources"


# ── GET /health ────────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_body(client):
    resp = client.get("/health")
    assert resp.json() == {"status": "ok"}


# ── POST /ingest ───────────────────────────────────────────────────────────────

def test_ingest_returns_200(client, mock_ingest_docs):
    resp = client.post("/ingest")
    assert resp.status_code == 200


def test_ingest_calls_ingest_documents_once(client, mock_ingest_docs):
    client.post("/ingest")
    mock_ingest_docs.assert_called_once()


def test_ingest_forwards_result(client, mock_ingest_docs):
    resp = client.post("/ingest")
    body = resp.json()
    assert body["status"] == "ok"
    assert body["chunks"] == 5
    assert "data/test.txt" in body["sources"]


def test_ingest_no_documents(client):
    with patch(_PATCH_INGEST, return_value={"status": "no_documents", "chunks": 0}):
        resp = client.post("/ingest")
    assert resp.status_code == 200
    assert resp.json() == {"status": "no_documents", "chunks": 0}


# ── GET /documents ─────────────────────────────────────────────────────────────

def test_documents_returns_200(client, mock_list_sources):
    resp = client.get("/documents")
    assert resp.status_code == 200


def test_documents_calls_list_sources_once(client, mock_list_sources):
    client.get("/documents")
    mock_list_sources.assert_called_once()


def test_documents_wraps_sources_in_key(client, mock_list_sources):
    resp = client.get("/documents")
    assert resp.json() == {"sources": ["data/doc1.txt", "data/doc2.md"]}


def test_documents_empty_store(client):
    with patch(_PATCH_SOURCES, return_value=[]):
        resp = client.get("/documents")
    assert resp.status_code == 200
    assert resp.json() == {"sources": []}


# ── POST /chat ─────────────────────────────────────────────────────────────────

def test_chat_empty_query_returns_400(client):
    resp = client.post("/chat", json={"query": ""})
    assert resp.status_code == 400


def test_chat_empty_query_detail_mentions_empty(client):
    resp = client.post("/chat", json={"query": ""})
    assert "empty" in resp.json()["detail"].lower()


def test_chat_whitespace_query_returns_400(client):
    resp = client.post("/chat", json={"query": "   "})
    assert resp.status_code == 400


def test_chat_missing_body_returns_422(client):
    resp = client.post("/chat")
    assert resp.status_code == 422


def test_chat_returns_200_and_event_stream(client):
    with patch(_PATCH_RETRIEVE, return_value=iter(["Hello ", "world."])):
        resp = client.post("/chat", json={"query": "Who is Jalin?"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_chat_sse_contains_chunk_data(client):
    with patch(_PATCH_RETRIEVE, return_value=iter(["Hello ", "world."])):
        resp = client.post("/chat", json={"query": "Who is Jalin?"})
    assert "data: Hello " in resp.text
    assert "data: world." in resp.text


def test_chat_sse_ends_with_done(client):
    with patch(_PATCH_RETRIEVE, return_value=iter(["Hello ", "world."])):
        resp = client.post("/chat", json={"query": "Who is Jalin?"})
    assert resp.text.strip().endswith("data: [DONE]")


def test_chat_always_sends_done_even_with_empty_stream(client):
    """[DONE] sentinel must be sent even when retrieve_and_stream yields nothing."""
    with patch(_PATCH_RETRIEVE, return_value=iter([])):
        resp = client.post("/chat", json={"query": "Empty answer?"})
    assert "data: [DONE]" in resp.text


def test_chat_newlines_escaped_in_sse(client):
    """Newlines inside a chunk must be escaped so SSE framing is never broken."""
    with patch(_PATCH_RETRIEVE, return_value=iter(["line1\nline2"])):
        resp = client.post("/chat", json={"query": "Multi-line?"})
    # The escaped form uses a literal backslash-n, not a real newline.
    assert "data: line1\\nline2" in resp.text


def test_chat_calls_retrieve_with_query(client):
    """retrieve_and_stream must receive the exact query string from the request."""
    with patch(_PATCH_RETRIEVE, return_value=iter(["answer"])) as mock_retrieve:
        client.post("/chat", json={"query": "Tell me about Jalin's projects."})
    mock_retrieve.assert_called_once_with("Tell me about Jalin's projects.")
