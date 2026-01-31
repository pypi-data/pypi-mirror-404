"""
Main audit logging interface for AI compliance.

This module provides the AuditLogger class, which is the primary interface
for logging AI interactions for compliance and auditing purposes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Union

from .encryption import EncryptionManager, hash_content
from .storage import (
    AuditEntry,
    FileStorage,
    MemoryStorage,
    StorageBackend,
    create_entry_id,
)


class AuditLogger:
    """
    Main audit logging interface for AI compliance.

    The AuditLogger provides a high-level interface for recording AI interactions,
    including inputs, outputs, safety evaluations, and performance metrics. It
    supports optional encryption of content and configurable retention policies.

    Args:
        storage: Either a StorageBackend instance or a file path string.
            If a string is provided, FileStorage is automatically created.
        encryption: Optional EncryptionManager for encrypting stored content.
        store_content: If True, stores actual content. If False, only stores
            content hashes for privacy (default: False).
        retention_days: Number of days to retain entries before cleanup
            (default: 365).

    Attributes:
        storage: The underlying storage backend.
        encryption: The encryption manager (if provided).
        store_content: Whether to store actual content.
        retention_days: Retention period in days.

    Example:
        Basic usage with file storage:

        >>> logger = AuditLogger("/var/log/audit")
        >>> entry_id = await logger.log(
        ...     input="What is 2+2?",
        ...     output="4",
        ...     provider="openai",
        ...     model="gpt-4",
        ... )

        With encryption and content storage:

        >>> from rotalabs_comply.audit import EncryptionManager
        >>> encryption = EncryptionManager()
        >>> logger = AuditLogger(
        ...     "/var/log/audit",
        ...     encryption=encryption,
        ...     store_content=True,
        ... )
        >>> entry_id = await logger.log(
        ...     input="Sensitive question",
        ...     output="Sensitive answer",
        ...     safety_passed=True,
        ... )

        With custom storage backend:

        >>> from rotalabs_comply.audit import MemoryStorage
        >>> storage = MemoryStorage(max_entries=10000)
        >>> logger = AuditLogger(storage)
    """

    def __init__(
        self,
        storage: Union[StorageBackend, str],
        encryption: EncryptionManager | None = None,
        store_content: bool = False,
        retention_days: int = 365,
    ) -> None:
        """
        Initialize the audit logger.

        Args:
            storage: StorageBackend instance or file path string.
            encryption: Optional encryption manager for content encryption.
            store_content: Whether to store actual content (default: False).
            retention_days: Days to retain entries (default: 365).
        """
        if isinstance(storage, str):
            self.storage: StorageBackend = FileStorage(storage)
        else:
            self.storage = storage

        self.encryption = encryption
        self.store_content = store_content
        self.retention_days = retention_days

    def _prepare_content(
        self, content: str
    ) -> tuple[str | None, str]:
        """
        Prepare content for storage.

        Returns tuple of (stored_content, content_hash).
        If store_content is False, stored_content will be None.
        If encryption is enabled, stored_content will be encrypted.
        """
        content_hash = hash_content(content)

        if not self.store_content:
            return None, content_hash

        if self.encryption:
            stored_content = self.encryption.encrypt(content)
        else:
            stored_content = content

        return stored_content, content_hash

    async def log(
        self,
        input: str,
        output: str,
        provider: str | None = None,
        model: str | None = None,
        conversation_id: str | None = None,
        safety_passed: bool = True,
        detectors_triggered: List[str] | None = None,
        block_reason: str | None = None,
        alerts: List[str] | None = None,
        latency_ms: float = 0.0,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        """
        Log an AI interaction.

        Creates an audit entry for the interaction and stores it in the
        configured storage backend.

        Args:
            input: The user input or prompt.
            output: The AI-generated output or response.
            provider: The AI provider (e.g., "openai", "anthropic").
            model: The model identifier (e.g., "gpt-4", "claude-3-opus").
            conversation_id: Optional ID to link related interactions.
            safety_passed: Whether the interaction passed safety checks
                (default: True).
            detectors_triggered: List of safety detector names that triggered.
            block_reason: Reason for blocking, if the request was blocked.
            alerts: List of alert messages generated.
            latency_ms: Time taken to process the request in milliseconds
                (default: 0.0).
            input_tokens: Number of tokens in the input.
            output_tokens: Number of tokens in the output.
            metadata: Additional custom metadata dictionary.

        Returns:
            str: The unique entry ID for this audit log entry.

        Example:
            >>> entry_id = await logger.log(
            ...     input="Tell me a joke",
            ...     output="Why did the chicken...",
            ...     provider="anthropic",
            ...     model="claude-3-opus",
            ...     safety_passed=True,
            ...     latency_ms=250.5,
            ...     input_tokens=5,
            ...     output_tokens=20,
            ...     metadata={"session_id": "abc123"},
            ... )
        """
        entry_id = create_entry_id()
        timestamp = datetime.utcnow().isoformat()

        input_content, input_hash = self._prepare_content(input)
        output_content, output_hash = self._prepare_content(output)

        entry = AuditEntry(
            id=entry_id,
            timestamp=timestamp,
            input_hash=input_hash,
            output_hash=output_hash,
            input_content=input_content,
            output_content=output_content,
            provider=provider,
            model=model,
            conversation_id=conversation_id,
            safety_passed=safety_passed,
            detectors_triggered=detectors_triggered or [],
            block_reason=block_reason,
            alerts=alerts or [],
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            metadata=metadata or {},
        )

        await self.storage.write(entry)
        return entry_id

    async def get_entry(self, entry_id: str) -> AuditEntry | None:
        """
        Retrieve an audit entry by ID.

        If encryption is enabled and store_content is True, the content
        will still be encrypted in the returned entry. Use the encryption
        manager to decrypt if needed.

        Args:
            entry_id: The unique identifier of the entry.

        Returns:
            AuditEntry | None: The entry if found, None otherwise.

        Example:
            >>> entry = await logger.get_entry("abc-123-def")
            >>> if entry:
            ...     print(f"Safety passed: {entry.safety_passed}")
        """
        return await self.storage.read(entry_id)

    async def get_entries(
        self, start: datetime, end: datetime
    ) -> List[AuditEntry]:
        """
        Retrieve all audit entries within a time range.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).

        Returns:
            List[AuditEntry]: All entries within the specified time range.

        Example:
            >>> from datetime import datetime, timedelta
            >>> end = datetime.utcnow()
            >>> start = end - timedelta(days=7)
            >>> entries = await logger.get_entries(start, end)
            >>> print(f"Found {len(entries)} entries in the last week")
        """
        return await self.storage.list_entries(start, end)

    async def cleanup_expired(self) -> int:
        """
        Delete entries older than the retention period.

        Removes all entries with timestamps older than `retention_days` from
        the current time.

        Returns:
            int: Number of entries deleted.

        Example:
            >>> # Delete entries older than retention_days
            >>> deleted_count = await logger.cleanup_expired()
            >>> print(f"Cleaned up {deleted_count} expired entries")

        Note:
            This operation may be slow for large datasets. Consider running
            during off-peak hours or using storage-native lifecycle policies
            (e.g., S3 lifecycle rules) for better performance.
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        start = datetime(1970, 1, 1)  # Unix epoch

        expired_entries = await self.storage.list_entries(start, cutoff)

        deleted_count = 0
        for entry in expired_entries:
            if await self.storage.delete(entry.id):
                deleted_count += 1

        return deleted_count

    def decrypt_content(self, encrypted_content: str) -> str:
        """
        Decrypt encrypted content from an audit entry.

        Convenience method for decrypting content stored in audit entries
        when encryption is enabled.

        Args:
            encrypted_content: The encrypted content string from an AuditEntry.

        Returns:
            str: The decrypted original content.

        Raises:
            ValueError: If no encryption manager is configured.
            cryptography.fernet.InvalidToken: If decryption fails.

        Example:
            >>> entry = await logger.get_entry("abc-123")
            >>> if entry and entry.input_content:
            ...     original_input = logger.decrypt_content(entry.input_content)
        """
        if not self.encryption:
            raise ValueError(
                "No encryption manager configured. "
                "Cannot decrypt content without the original encryption key."
            )
        return self.encryption.decrypt(encrypted_content)
