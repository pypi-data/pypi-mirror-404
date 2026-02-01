"""Retriever components for Tantra.

Provides retrieval interfaces for RAG (Retrieval-Augmented Generation).

Example:
    from tantra import Retriever, Document, InMemoryRetriever

    # Create a retriever
    retriever = InMemoryRetriever()
    await retriever.add("Python is a programming language", {"source": "wiki"})

    # Retrieve relevant documents
    docs = await retriever.retrieve("What is Python?", top_k=3)
"""

from .base import Document, Retriever
from .inmemory import InMemoryRetriever

__all__ = [
    "Document",
    "Retriever",
    "InMemoryRetriever",
]
