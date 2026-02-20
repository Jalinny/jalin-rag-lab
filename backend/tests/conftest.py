"""
Shared pytest configuration and fixtures for the backend test suite.

Sets up:
  - ANTHROPIC_API_KEY env var before any app module is imported
    (app.config reads it at import time via os.environ["ANTHROPIC_API_KEY"])
  - A session-scoped FastAPI app instance
  - A function-scoped TestClient for endpoint tests
  - Patch fixtures for the three callables exposed through app.main
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Must be set before any app module is imported.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-unit-tests")

# Patch targets — functions imported into app.main's namespace.
_PATCH_RETRIEVE = "app.main.retrieve_and_stream"
_PATCH_INGEST = "app.main.ingest_documents"
_PATCH_SOURCES = "app.main.list_sources"


# ── App / client ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def fastapi_app():
    """Return the FastAPI application object (created once per test session)."""
    from app.main import app
    return app


@pytest.fixture()
def client(fastapi_app):
    """Return a fresh TestClient for each test function."""
    return TestClient(fastapi_app)


# ── RAG / ingest patch fixtures ───────────────────────────────────────────────

@pytest.fixture()
def mock_retrieve():
    """Patch retrieve_and_stream to yield two text chunks without real I/O."""
    with patch(_PATCH_RETRIEVE, return_value=iter(["Hello ", "world."])) as mock:
        yield mock


@pytest.fixture()
def mock_ingest_docs():
    """Patch ingest_documents to return a successful ingest result."""
    with patch(
        _PATCH_INGEST,
        return_value={"status": "ok", "chunks": 5, "sources": ["data/test.txt"]},
    ) as mock:
        yield mock


@pytest.fixture()
def mock_list_sources():
    """Patch list_sources to return a predictable list of source paths."""
    with patch(
        _PATCH_SOURCES,
        return_value=["data/doc1.txt", "data/doc2.md"],
    ) as mock:
        yield mock
