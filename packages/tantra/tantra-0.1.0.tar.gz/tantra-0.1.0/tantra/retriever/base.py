"""Base classes for retrieval in Tantra.

Provides the Retriever interface for RAG (Retrieval-Augmented Generation).
Implement this to create custom retrieval backends (Pinecone, Milvus, pgvector, etc.).

Memory vs Retriever:
- Memory: Stores conversation history (messages). No query parameter needed.
- Retriever: Stores knowledge/documents. Requires a query for semantic search.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A document in the retriever.

    Represents a piece of knowledge that can be retrieved based on
    semantic similarity to a query.

    Attributes:
        id: Unique identifier for the document.
        text: The document content.
        metadata: Optional metadata (source, date, category, etc.).
        score: Relevance score (set during retrieval). Higher is more relevant.
    """

    id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None  # Set during retrieval

    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Document(id={self.id!r}, text={text_preview!r}, score={self.score})"


class Retriever(ABC):
    """Abstract base class for document retrieval.

    Retriever is separate from Memory by design:
    - Memory: Conversation history (no query parameter)
    - Retriever: Knowledge base with semantic search (requires query)

    Implement this class to create custom retrieval backends
    (Pinecone, Milvus, Weaviate, pgvector, etc.).

    Examples:
        ```python
        class PineconeRetriever(Retriever):
            def __init__(self, index_name: str):
                self._index = pinecone.Index(index_name)
                self._embedder = OpenAIEmbeddings()

            async def add(self, text: str, metadata: dict | None = None) -> str:
                doc_id = str(uuid4())
                embedding = await self._embedder.embed(text)
                self._index.upsert([(doc_id, embedding, {**metadata, "text": text})])
                return doc_id

            async def retrieve(self, query: str, top_k: int = 5) -> list[Document]:
                embedding = await self._embedder.embed(query)
                results = self._index.query(embedding, top_k=top_k, include_metadata=True)
                return [
                    Document(
                        id=r.id,
                        text=r.metadata["text"],
                        metadata=r.metadata,
                        score=r.score,
                    )
                    for r in results.matches
                ]
        ```
    """

    @abstractmethod
    async def add(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a document to the retriever.

        Args:
            text: The document text content.
            metadata: Optional metadata (source, category, date, etc.).

        Returns:
            The document ID.
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[Document]:
        """Retrieve documents relevant to a query.

        Args:
            query: The search query.
            top_k: Maximum number of documents to return.

        Returns:
            List of Documents ordered by relevance (highest first).
        """
        pass

    @abstractmethod
    async def delete(self, doc_id: str) -> bool:
        """Delete a document by ID.

        Args:
            doc_id: The document ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the retriever."""
        pass

    async def add_many(
        self,
        documents: list[tuple[str, dict[str, Any] | None]],
    ) -> list[str]:
        """Add multiple documents.

        Default implementation calls add() for each document.
        Override for batch optimization.

        Args:
            documents: List of (text, metadata) tuples.

        Returns:
            List of document IDs.
        """
        ids = []
        for text, metadata in documents:
            doc_id = await self.add(text, metadata)
            ids.append(doc_id)
        return ids

    async def get(self, doc_id: str) -> Document | None:
        """Get a document by ID.

        Default implementation returns None (not supported).
        Override to enable direct document lookup.

        Args:
            doc_id: The document ID.

        Returns:
            The Document if found, None otherwise.
        """
        return None
