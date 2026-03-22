"""
Lightweight embedding function using chromadb's built-in ONNX runtime.

Downloads a ~23MB ONNX model on first use (no PyTorch, no API key).
Memory footprint: ~120MB vs ~400MB for sentence-transformers.
"""

from typing import List
from langchain_core.embeddings import Embeddings


class OnnxEmbeddings(Embeddings):
    def __init__(self):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        self._fn = ONNXMiniLM_L6_V2()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[float(x) for x in v] for v in self._fn(texts)]

    def embed_query(self, text: str) -> List[float]:
        return [float(x) for x in self._fn([text])[0]]
