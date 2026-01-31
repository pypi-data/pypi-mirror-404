"""Tests for storage backends."""

from datetime import datetime, timedelta

import pytest

from rotalabs_comply.audit.storage import AuditEntry, FileStorage, MemoryStorage


@pytest.fixture
def sample_entry():
    """Create a sample audit entry for testing."""
    return AuditEntry(
        id="test-entry-001",
        timestamp=datetime.utcnow().isoformat(),
        input_hash="abc123",
        output_hash="def456",
        provider="openai",
        model="gpt-4",
        safety_passed=True,
        latency_ms=150.0,
        metadata={"test": "value"},
    )


@pytest.fixture
def sample_entries():
    """Create multiple sample entries with different timestamps."""
    now = datetime.utcnow()
    entries = []
    for i in range(5):
        entry = AuditEntry(
            id=f"test-entry-{i:03d}",
            timestamp=(now - timedelta(days=i)).isoformat(),
            input_hash=f"input-{i}",
            output_hash=f"output-{i}",
            provider="openai",
            model="gpt-4",
            safety_passed=True,
            latency_ms=100.0 + i * 10,
        )
        entries.append(entry)
    return entries


class TestMemoryStorage:
    """Tests for MemoryStorage backend."""

    @pytest.mark.asyncio
    async def test_memory_storage_write_read(self, sample_entry):
        """Write and read back an entry."""
        storage = MemoryStorage()

        # Write
        entry_id = await storage.write(sample_entry)
        assert entry_id == sample_entry.id

        # Read back
        retrieved = await storage.read(entry_id)
        assert retrieved is not None
        assert retrieved.id == sample_entry.id
        assert retrieved.input_hash == sample_entry.input_hash
        assert retrieved.output_hash == sample_entry.output_hash
        assert retrieved.provider == sample_entry.provider

    @pytest.mark.asyncio
    async def test_memory_storage_list_entries(self, sample_entries):
        """List entries by date range."""
        storage = MemoryStorage()

        # Write all entries
        for entry in sample_entries:
            await storage.write(entry)

        # Query with date range that includes all entries
        now = datetime.utcnow()
        start = now - timedelta(days=10)
        end = now + timedelta(days=1)

        entries = await storage.list_entries(start, end)
        assert len(entries) == len(sample_entries)

        # Query with narrower range (last 2 days)
        start_narrow = now - timedelta(days=2)
        entries_narrow = await storage.list_entries(start_narrow, end)
        assert len(entries_narrow) >= 2  # At least entries from day 0, 1, and 2

    @pytest.mark.asyncio
    async def test_memory_storage_delete(self, sample_entry):
        """Delete an entry."""
        storage = MemoryStorage()

        # Write
        await storage.write(sample_entry)

        # Verify exists
        assert await storage.read(sample_entry.id) is not None

        # Delete
        deleted = await storage.delete(sample_entry.id)
        assert deleted is True

        # Verify deleted
        assert await storage.read(sample_entry.id) is None

        # Try to delete again
        deleted_again = await storage.delete(sample_entry.id)
        assert deleted_again is False

    @pytest.mark.asyncio
    async def test_memory_storage_count(self, sample_entries):
        """Count entries in storage."""
        storage = MemoryStorage()

        # Initial count
        assert await storage.count() == 0

        # Add entries
        for i, entry in enumerate(sample_entries):
            await storage.write(entry)
            assert await storage.count() == i + 1

    @pytest.mark.asyncio
    async def test_memory_storage_max_entries(self):
        """Test max entries limit."""
        max_entries = 3
        storage = MemoryStorage(max_entries=max_entries)

        # Create entries
        entries = []
        for i in range(5):
            entry = AuditEntry(
                id=f"entry-{i}",
                timestamp=datetime.utcnow().isoformat(),
                input_hash=f"hash-{i}",
                output_hash=f"hash-{i}",
                safety_passed=True,
                latency_ms=100.0,
            )
            entries.append(entry)
            await storage.write(entry)

        # Should only have max_entries
        count = await storage.count()
        assert count == max_entries

        # Oldest entries should be removed (FIFO)
        assert await storage.read("entry-0") is None
        assert await storage.read("entry-1") is None
        assert await storage.read("entry-2") is not None
        assert await storage.read("entry-3") is not None
        assert await storage.read("entry-4") is not None

    @pytest.mark.asyncio
    async def test_memory_storage_read_nonexistent(self):
        """Reading nonexistent entry returns None."""
        storage = MemoryStorage()
        result = await storage.read("nonexistent-id")
        assert result is None


class TestFileStorage:
    """Tests for FileStorage backend."""

    @pytest.mark.asyncio
    async def test_file_storage_write_read(self, tmp_path, sample_entry):
        """Write and read back an entry using file storage."""
        storage = FileStorage(str(tmp_path))

        # Write
        entry_id = await storage.write(sample_entry)
        assert entry_id == sample_entry.id

        # Read back
        retrieved = await storage.read(entry_id)
        assert retrieved is not None
        assert retrieved.id == sample_entry.id
        assert retrieved.input_hash == sample_entry.input_hash
        assert retrieved.output_hash == sample_entry.output_hash
        assert retrieved.provider == sample_entry.provider
        assert retrieved.model == sample_entry.model

    @pytest.mark.asyncio
    async def test_file_storage_creates_directory(self, tmp_path):
        """File storage creates directory if it doesn't exist."""
        new_dir = tmp_path / "audit_logs"
        storage = FileStorage(str(new_dir))

        entry = AuditEntry(
            id="test-001",
            timestamp=datetime.utcnow().isoformat(),
            input_hash="abc",
            output_hash="def",
            safety_passed=True,
            latency_ms=100.0,
        )

        await storage.write(entry)

        assert new_dir.exists()

    @pytest.mark.asyncio
    async def test_file_storage_list_entries(self, tmp_path, sample_entries):
        """List entries from file storage."""
        storage = FileStorage(str(tmp_path))

        for entry in sample_entries:
            await storage.write(entry)

        now = datetime.utcnow()
        start = now - timedelta(days=10)
        end = now + timedelta(days=1)

        entries = await storage.list_entries(start, end)
        assert len(entries) == len(sample_entries)

    @pytest.mark.asyncio
    async def test_file_storage_count(self, tmp_path, sample_entries):
        """Count entries in file storage."""
        storage = FileStorage(str(tmp_path))

        for entry in sample_entries:
            await storage.write(entry)

        count = await storage.count()
        assert count == len(sample_entries)

    @pytest.mark.asyncio
    async def test_file_storage_delete(self, tmp_path, sample_entry):
        """Delete entry from file storage."""
        storage = FileStorage(str(tmp_path))

        await storage.write(sample_entry)
        assert await storage.read(sample_entry.id) is not None

        deleted = await storage.delete(sample_entry.id)
        assert deleted is True

        assert await storage.read(sample_entry.id) is None

    @pytest.mark.asyncio
    async def test_file_storage_read_nonexistent(self, tmp_path):
        """Reading nonexistent entry returns None."""
        storage = FileStorage(str(tmp_path))
        result = await storage.read("nonexistent-id")
        assert result is None
