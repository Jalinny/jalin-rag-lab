"""
Ingest documents from DATA_PATH into the Chroma vector store.

Supported file types: .pdf, .txt, .md
"""

import os
from pathlib import Path

from app.config import CHROMA_PATH, DATA_PATH, EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, VOYAGE_API_KEY


def _load_documents(data_path: str) -> list:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    docs = []
    for fpath in Path(data_path).rglob("*"):
        if fpath.suffix == ".pdf":
            loader = PyPDFLoader(str(fpath))
        elif fpath.suffix in {".txt", ".md"}:
            loader = TextLoader(str(fpath), encoding="utf-8")
        else:
            continue
        docs.extend(loader.load())
    return docs


def ingest_documents() -> dict:
    from langchain_voyageai import VoyageAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    docs = _load_documents(DATA_PATH)
    if not docs:
        return {"status": "no_documents", "chunks": 0}

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(docs)

    embeddings = VoyageAIEmbeddings(model=EMBED_MODEL, api_key=VOYAGE_API_KEY)

    # Clear existing collection before re-ingesting to avoid duplicates
    existing = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    existing.delete_collection()

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )

    sources = list({doc.metadata.get("source", "unknown") for doc in docs})
    return {"status": "ok", "chunks": len(chunks), "sources": sources}


def list_sources() -> list[str]:
    from langchain_voyageai import VoyageAIEmbeddings
    from langchain_community.vectorstores import Chroma
    embeddings = VoyageAIEmbeddings(model=EMBED_MODEL, api_key=VOYAGE_API_KEY)
    try:
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        items = db.get(include=["metadatas"])
        sources = list({m.get("source", "unknown") for m in items["metadatas"]})
        return sorted(sources)
    except Exception:
        return []
