"""Tests for the Retriever interface."""

import pytest

from tantra import Document, InMemoryRetriever, Retriever


class TestDocument:
    """Tests for the Document model."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(id="doc1", text="Hello world")
        assert doc.id == "doc1"
        assert doc.text == "Hello world"
        assert doc.metadata == {}
        assert doc.score is None

    def test_document_with_metadata(self):
        """Test document with metadata."""
        doc = Document(
            id="doc1",
            text="Hello",
            metadata={"source": "wiki", "date": "2024-01-01"},
        )
        assert doc.metadata["source"] == "wiki"
        assert doc.metadata["date"] == "2024-01-01"

    def test_document_with_score(self):
        """Test document with relevance score."""
        doc = Document(id="doc1", text="Hello", score=0.95)
        assert doc.score == 0.95

    def test_document_repr(self):
        """Test document string representation."""
        doc = Document(id="doc1", text="Hello world", score=0.5)
        repr_str = repr(doc)
        assert "doc1" in repr_str
        assert "Hello world" in repr_str
        assert "0.5" in repr_str

    def test_document_repr_truncates_long_text(self):
        """Test that repr truncates long text."""
        long_text = "A" * 100
        doc = Document(id="doc1", text=long_text)
        repr_str = repr(doc)
        assert "..." in repr_str


class TestInMemoryRetriever:
    """Tests for the InMemoryRetriever."""

    @pytest.fixture
    def retriever(self):
        """Create a fresh retriever for each test."""
        return InMemoryRetriever()

    @pytest.mark.asyncio
    async def test_add_document(self, retriever):
        """Test adding a document."""
        doc_id = await retriever.add("Hello world")
        assert doc_id == "doc_1"
        assert retriever.count == 1

    @pytest.mark.asyncio
    async def test_add_document_with_metadata(self, retriever):
        """Test adding a document with metadata."""
        doc_id = await retriever.add("Hello", {"source": "test"})
        doc = await retriever.get(doc_id)
        assert doc is not None
        assert doc.metadata["source"] == "test"

    @pytest.mark.asyncio
    async def test_add_multiple_documents(self, retriever):
        """Test adding multiple documents."""
        await retriever.add("Document one")
        await retriever.add("Document two")
        await retriever.add("Document three")
        assert retriever.count == 3

    @pytest.mark.asyncio
    async def test_retrieve_matching_documents(self, retriever):
        """Test retrieving documents that match a query."""
        await retriever.add("Python is a programming language")
        await retriever.add("JavaScript runs in browsers")
        await retriever.add("Python is great for data science")

        docs = await retriever.retrieve("Python programming")
        assert len(docs) >= 1
        # Python documents should rank higher
        assert "Python" in docs[0].text

    @pytest.mark.asyncio
    async def test_retrieve_top_k(self, retriever):
        """Test that retrieve respects top_k limit."""
        for i in range(10):
            await retriever.add(f"Document about Python number {i}")

        docs = await retriever.retrieve("Python", top_k=3)
        assert len(docs) == 3

    @pytest.mark.asyncio
    async def test_retrieve_empty(self, retriever):
        """Test retrieving from empty retriever."""
        docs = await retriever.retrieve("anything")
        assert docs == []

    @pytest.mark.asyncio
    async def test_retrieve_no_match(self, retriever):
        """Test retrieving with no matching documents."""
        await retriever.add("Hello world")
        docs = await retriever.retrieve("xyz123")
        assert docs == []

    @pytest.mark.asyncio
    async def test_retrieve_scores(self, retriever):
        """Test that retrieved documents have scores."""
        await retriever.add("Python is great")
        docs = await retriever.retrieve("Python")
        assert len(docs) == 1
        assert docs[0].score is not None
        assert docs[0].score > 0

    @pytest.mark.asyncio
    async def test_delete_document(self, retriever):
        """Test deleting a document."""
        doc_id = await retriever.add("To be deleted")
        assert retriever.count == 1

        deleted = await retriever.delete(doc_id)
        assert deleted is True
        assert retriever.count == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, retriever):
        """Test deleting a document that doesn't exist."""
        deleted = await retriever.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_clear(self, retriever):
        """Test clearing all documents."""
        await retriever.add("Doc 1")
        await retriever.add("Doc 2")
        assert retriever.count == 2

        await retriever.clear()
        assert retriever.count == 0

    @pytest.mark.asyncio
    async def test_get_document(self, retriever):
        """Test getting a document by ID."""
        doc_id = await retriever.add("Hello", {"key": "value"})
        doc = await retriever.get(doc_id)

        assert doc is not None
        assert doc.id == doc_id
        assert doc.text == "Hello"
        assert doc.metadata["key"] == "value"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, retriever):
        """Test getting a document that doesn't exist."""
        doc = await retriever.get("nonexistent")
        assert doc is None

    @pytest.mark.asyncio
    async def test_add_many(self, retriever):
        """Test batch adding documents."""
        documents = [
            ("Document 1", {"idx": 1}),
            ("Document 2", {"idx": 2}),
            ("Document 3", None),
        ]
        ids = await retriever.add_many(documents)

        assert len(ids) == 3
        assert retriever.count == 3

    @pytest.mark.asyncio
    async def test_len(self, retriever):
        """Test __len__ support."""
        assert len(retriever) == 0
        await retriever.add("Doc")
        assert len(retriever) == 1


class TestRetrieverABC:
    """Tests for the Retriever abstract base class."""

    def test_cannot_instantiate_abc(self):
        """Test that Retriever ABC cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Retriever()

    def test_subclass_must_implement_methods(self):
        """Test that subclasses must implement abstract methods."""

        class IncompleteRetriever(Retriever):
            pass

        with pytest.raises(TypeError):
            IncompleteRetriever()
