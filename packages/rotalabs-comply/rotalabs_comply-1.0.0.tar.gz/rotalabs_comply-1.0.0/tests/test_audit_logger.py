"""Tests for AuditLogger."""

import pytest

from rotalabs_comply.audit.encryption import EncryptionManager, hash_content
from rotalabs_comply.audit.logger import AuditLogger
from rotalabs_comply.audit.storage import MemoryStorage


@pytest.fixture
def memory_storage():
    """Create a memory storage backend for testing."""
    return MemoryStorage()


@pytest.fixture
def audit_logger(memory_storage):
    """Create an AuditLogger with memory storage."""
    return AuditLogger(memory_storage)


class TestAuditLogger:
    """Tests for AuditLogger class."""

    @pytest.mark.asyncio
    async def test_audit_logger_basic_log(self, audit_logger, memory_storage):
        """Log and retrieve a basic entry."""
        entry_id = await audit_logger.log(
            input="What is 2+2?",
            output="4",
            provider="openai",
            model="gpt-4",
        )

        assert entry_id is not None
        assert len(entry_id) > 0

        # Retrieve the entry
        entry = await audit_logger.get_entry(entry_id)
        assert entry is not None
        assert entry.id == entry_id
        assert entry.provider == "openai"
        assert entry.model == "gpt-4"

        # By default, content is not stored (hash only)
        assert entry.input_content is None
        assert entry.output_content is None

        # But hashes should be populated
        assert entry.input_hash == hash_content("What is 2+2?")
        assert entry.output_hash == hash_content("4")

    @pytest.mark.asyncio
    async def test_audit_logger_with_encryption(self, memory_storage):
        """Log with encryption enabled."""
        encryption = EncryptionManager()
        logger = AuditLogger(
            memory_storage,
            encryption=encryption,
            store_content=True,
        )

        entry_id = await logger.log(
            input="Sensitive question",
            output="Sensitive answer",
            provider="anthropic",
            model="claude-3-opus",
        )

        # Retrieve the entry
        entry = await logger.get_entry(entry_id)
        assert entry is not None

        # Content should be stored but encrypted
        assert entry.input_content is not None
        assert entry.output_content is not None

        # Encrypted content should not equal original
        assert entry.input_content != "Sensitive question"
        assert entry.output_content != "Sensitive answer"

        # Decrypt using the logger's method
        decrypted_input = logger.decrypt_content(entry.input_content)
        decrypted_output = logger.decrypt_content(entry.output_content)

        assert decrypted_input == "Sensitive question"
        assert decrypted_output == "Sensitive answer"

    @pytest.mark.asyncio
    async def test_audit_logger_hash_only(self, memory_storage):
        """Log with store_content=False (hash only mode)."""
        logger = AuditLogger(
            memory_storage,
            store_content=False,
        )

        entry_id = await logger.log(
            input="Private data",
            output="Private response",
        )

        entry = await logger.get_entry(entry_id)
        assert entry is not None

        # Content should not be stored
        assert entry.input_content is None
        assert entry.output_content is None

        # Hashes should be present
        assert entry.input_hash is not None
        assert entry.output_hash is not None
        assert entry.input_hash == hash_content("Private data")
        assert entry.output_hash == hash_content("Private response")

    @pytest.mark.asyncio
    async def test_audit_logger_metadata(self, audit_logger):
        """Log with custom metadata."""
        entry_id = await audit_logger.log(
            input="Hello",
            output="Hi there!",
            provider="openai",
            model="gpt-3.5-turbo",
            safety_passed=True,
            detectors_triggered=["greeting_detector"],
            latency_ms=50.5,
            input_tokens=2,
            output_tokens=3,
            metadata={
                "session_id": "sess-123",
                "user_id": "user-456",
                "request_id": "req-789",
            },
        )

        entry = await audit_logger.get_entry(entry_id)
        assert entry is not None

        # Check all metadata
        assert entry.safety_passed is True
        assert entry.detectors_triggered == ["greeting_detector"]
        assert entry.latency_ms == 50.5
        assert entry.input_tokens == 2
        assert entry.output_tokens == 3
        assert entry.metadata == {
            "session_id": "sess-123",
            "user_id": "user-456",
            "request_id": "req-789",
        }

    @pytest.mark.asyncio
    async def test_audit_logger_with_alerts(self, audit_logger):
        """Log entry with alerts."""
        entry_id = await audit_logger.log(
            input="Test input",
            output="Test output",
            safety_passed=False,
            block_reason="Content policy violation",
            alerts=["High risk content detected", "PII found"],
        )

        entry = await audit_logger.get_entry(entry_id)
        assert entry is not None
        assert entry.safety_passed is False
        assert entry.block_reason == "Content policy violation"
        assert len(entry.alerts) == 2
        assert "High risk content detected" in entry.alerts
        assert "PII found" in entry.alerts

    @pytest.mark.asyncio
    async def test_audit_logger_conversation_tracking(self, audit_logger):
        """Log multiple entries in a conversation."""
        conv_id = "conversation-001"

        entry1_id = await audit_logger.log(
            input="Hello",
            output="Hi! How can I help?",
            conversation_id=conv_id,
        )

        entry2_id = await audit_logger.log(
            input="What's the weather?",
            output="I don't have access to weather data.",
            conversation_id=conv_id,
        )

        entry1 = await audit_logger.get_entry(entry1_id)
        entry2 = await audit_logger.get_entry(entry2_id)

        assert entry1.conversation_id == conv_id
        assert entry2.conversation_id == conv_id

    @pytest.mark.asyncio
    async def test_audit_logger_file_path_storage(self, tmp_path):
        """Test AuditLogger with file path string creates FileStorage."""
        logger = AuditLogger(str(tmp_path))

        entry_id = await logger.log(
            input="Test",
            output="Response",
        )

        entry = await logger.get_entry(entry_id)
        assert entry is not None
        assert entry.id == entry_id

    @pytest.mark.asyncio
    async def test_audit_logger_decrypt_without_encryption(self, audit_logger):
        """Decrypting without encryption manager raises error."""
        with pytest.raises(ValueError) as exc_info:
            audit_logger.decrypt_content("some-encrypted-data")

        assert "No encryption manager configured" in str(exc_info.value)
