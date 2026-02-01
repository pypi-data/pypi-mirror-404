"""In-memory retriever for Tantra.

Simple keyword-based retriever for testing and development.
"""

from __future__ import annotations

from typing import Any

from .base import Document, Retriever


class InMemoryRetriever(Retriever):
    """Simple in-memory retriever using keyword matching.

    Uses basic TF-IDF-style keyword matching for retrieval.
    Suitable for testing, development, and small datasets.

    For production with semantic search, use a vector database
    implementation (Pinecone, Milvus, pgvector, etc.).

    Examples:
        ```python
        retriever = InMemoryRetriever()
        await retriever.add("Python is a programming language")
        await retriever.add("JavaScript runs in browsers")

        docs = await retriever.retrieve("What is Python?")
        print(docs[0].text)  # "Python is a programming language"
        ```
    """

    def __init__(self) -> None:
        """Initialize the in-memory retriever."""
        self._documents: dict[str, Document] = {}
        self._counter = 0

    async def add(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a document to memory.

        Args:
            text: The document text content.
            metadata: Optional metadata dict (source, category, etc.).

        Returns:
            The generated document ID (e.g. ``"doc_1"``).
        """
        self._counter += 1
        doc_id = f"doc_{self._counter}"
        self._documents[doc_id] = Document(
            id=doc_id,
            text=text,
            metadata=metadata or {},
        )
        return doc_id

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[Document]:
        """Retrieve documents using keyword matching.

        Scores documents based on how many query words appear in the text.
        Case-insensitive matching.

        Args:
            query: The search query string.
            top_k: Maximum number of documents to return.

        Returns:
            List of Documents ordered by relevance score (highest first).
            Only documents with at least one matching word are included.
        """
        query_words = set(query.lower().split())

        scored_docs = []
        for doc in self._documents.values():
            doc_words = set(doc.text.lower().split())
            # Simple overlap score
            overlap = len(query_words & doc_words)
            if overlap > 0:
                # Normalize by query length
                score = overlap / len(query_words)
                scored_docs.append(
                    Document(
                        id=doc.id,
                        text=doc.text,
                        metadata=doc.metadata,
                        score=score,
                    )
                )

        # Sort by score descending
        scored_docs.sort(key=lambda d: d.score or 0, reverse=True)
        return scored_docs[:top_k]

    async def delete(self, doc_id: str) -> bool:
        """Delete a document by ID.

        Args:
            doc_id: The document ID to delete.

        Returns:
            True if the document was deleted, False if not found.
        """
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False

    async def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        self._counter = 0

    async def get(self, doc_id: str) -> Document | None:
        """Get a document by ID.

        Args:
            doc_id: The document ID to look up.

        Returns:
            The Document if found, None otherwise.
        """
        return self._documents.get(doc_id)

    @property
    def count(self) -> int:
        """Number of documents in the retriever."""
        return len(self._documents)

    def __len__(self) -> int:
        """Support len() for document count."""
        return len(self._documents)
