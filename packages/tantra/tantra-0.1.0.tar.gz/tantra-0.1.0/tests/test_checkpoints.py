"""Tests for checkpoint infrastructure."""

from uuid import uuid4

import pytest
from conftest import MemoryCheckpointStore

from tantra.checkpoints import Checkpoint
from tantra.types import Message


class TestCheckpointModel:
    """Tests for the Checkpoint model with new fields."""

    def test_session_id_defaults_to_none(self):
        """session_id defaults to None."""
        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[],
        )
        assert checkpoint.session_id is None

    def test_checkpoint_type_defaults_to_interrupt(self):
        """checkpoint_type defaults to 'interrupt'."""
        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[],
        )
        assert checkpoint.checkpoint_type == "interrupt"

    def test_create_with_session_id(self):
        """Can create a checkpoint with session_id."""
        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[],
            session_id="sess-abc",
        )
        assert checkpoint.session_id == "sess-abc"

    def test_create_with_checkpoint_type_progress(self):
        """Can create a checkpoint with checkpoint_type='progress'."""
        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[],
            checkpoint_type="progress",
        )
        assert checkpoint.checkpoint_type == "progress"

    def test_create_with_all_new_fields(self):
        """Can create a checkpoint with both new fields set."""
        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[Message(role="user", content="Hello")],
            session_id="sess-xyz",
            checkpoint_type="progress",
            pending_tool="my_tool",
            pending_args={"key": "value"},
            prompt="Approve?",
        )
        assert checkpoint.session_id == "sess-xyz"
        assert checkpoint.checkpoint_type == "progress"
        assert checkpoint.pending_tool == "my_tool"
        assert len(checkpoint.messages) == 1


class TestMemoryCheckpointStore:
    """Tests for MemoryCheckpointStore (test helper)."""

    @pytest.mark.asyncio
    async def test_save_and_load(self):
        """Can save and load checkpoints."""
        store = MemoryCheckpointStore()

        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test-agent",
            messages=[Message(role="user", content="Hello")],
            pending_tool="my_tool",
            prompt="Approve?",
        )

        checkpoint_id = await store.save(checkpoint)
        assert checkpoint_id == checkpoint.id

        loaded = await store.load(checkpoint_id)
        assert loaded is not None
        assert loaded.id == checkpoint.id
        assert loaded.pending_tool == "my_tool"

    @pytest.mark.asyncio
    async def test_update(self):
        """Can update checkpoint status."""
        store = MemoryCheckpointStore()

        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test-agent",
            messages=[],
            prompt="Test",
        )

        await store.save(checkpoint)
        updated = await store.update(checkpoint.id, status="completed")
        assert updated is True

        loaded = await store.load(checkpoint.id)
        assert loaded.status == "completed"

    @pytest.mark.asyncio
    async def test_delete(self):
        """Can delete checkpoint."""
        store = MemoryCheckpointStore()

        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test-agent",
            messages=[],
            prompt="Test",
        )

        await store.save(checkpoint)
        deleted = await store.delete(checkpoint.id)
        assert deleted is True

        loaded = await store.load(checkpoint.id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_list_pending(self):
        """Can list pending checkpoints."""
        store = MemoryCheckpointStore()

        for i in range(3):
            checkpoint = Checkpoint(
                run_id=uuid4(),
                name=f"agent-{i}",
                messages=[],
                prompt=f"Prompt {i}",
            )
            await store.save(checkpoint)

        checkpoints = await store.list_pending()
        await store.update(checkpoints[0].id, status="completed")

        pending = await store.list_pending()
        assert len(pending) == 2

        filtered = await store.list_pending(name="agent-1")
        assert len(filtered) == 1

    @pytest.mark.asyncio
    async def test_save_with_new_fields(self):
        """Can save and load checkpoints with session_id and checkpoint_type."""
        store = MemoryCheckpointStore()

        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test-agent",
            messages=[],
            session_id="sess-123",
            checkpoint_type="progress",
            prompt="Test",
        )

        await store.save(checkpoint)
        loaded = await store.load(checkpoint.id)
        assert loaded.session_id == "sess-123"
        assert loaded.checkpoint_type == "progress"
