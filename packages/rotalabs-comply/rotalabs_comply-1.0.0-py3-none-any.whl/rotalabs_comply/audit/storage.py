"""
Storage backends for audit log entries.

This module provides multiple storage backend implementations for persisting
audit log entries, including file-based, in-memory, and S3 storage options.
"""

from __future__ import annotations

import json
import os
import uuid
from abc import abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Protocol, runtime_checkable

import aiofiles
import aiofiles.os


@dataclass
class AuditEntry:
    """
    Represents a single audit log entry.

    Captures all relevant information about an AI interaction including
    inputs, outputs, safety evaluations, and performance metrics.

    Attributes:
        id: Unique identifier for this entry.
        timestamp: When the interaction occurred (ISO format).
        input_hash: SHA-256 hash of the input content.
        output_hash: SHA-256 hash of the output content.
        input_content: Actual input content (if store_content=True, may be encrypted).
        output_content: Actual output content (if store_content=True, may be encrypted).
        provider: The AI provider (e.g., "openai", "anthropic").
        model: The model identifier (e.g., "gpt-4", "claude-3-opus").
        conversation_id: Optional ID linking related interactions.
        safety_passed: Whether the interaction passed all safety checks.
        detectors_triggered: List of safety detector names that triggered.
        block_reason: Reason for blocking, if the request was blocked.
        alerts: List of alert messages generated.
        latency_ms: Time taken to process the request in milliseconds.
        input_tokens: Number of tokens in the input.
        output_tokens: Number of tokens in the output.
        metadata: Additional custom metadata.
    """

    id: str
    timestamp: str
    input_hash: str
    output_hash: str
    input_content: str | None = None
    output_content: str | None = None
    provider: str | None = None
    model: str | None = None
    conversation_id: str | None = None
    safety_passed: bool = True
    detectors_triggered: List[str] = field(default_factory=list)
    block_reason: str | None = None
    alerts: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        """Create entry from dictionary."""
        return cls(**data)


@runtime_checkable
class StorageBackend(Protocol):
    """
    Protocol defining the interface for audit log storage backends.

    All storage backends must implement these async methods to support
    writing, reading, listing, deleting, and counting audit entries.
    """

    @abstractmethod
    async def write(self, entry: AuditEntry) -> str:
        """
        Write an audit entry to storage.

        Args:
            entry: The audit entry to store.

        Returns:
            str: The entry ID (same as entry.id).
        """
        ...

    @abstractmethod
    async def read(self, entry_id: str) -> AuditEntry | None:
        """
        Read an audit entry by ID.

        Args:
            entry_id: The unique identifier of the entry.

        Returns:
            AuditEntry | None: The entry if found, None otherwise.
        """
        ...

    @abstractmethod
    async def list_entries(
        self, start: datetime, end: datetime
    ) -> List[AuditEntry]:
        """
        List all entries within a time range.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).

        Returns:
            List[AuditEntry]: Entries within the specified time range.
        """
        ...

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """
        Delete an entry by ID.

        Args:
            entry_id: The unique identifier of the entry to delete.

        Returns:
            bool: True if the entry was deleted, False if not found.
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """
        Count total number of entries in storage.

        Returns:
            int: Total number of stored entries.
        """
        ...


class FileStorage:
    """
    File-based storage backend using JSONL format.

    Stores audit entries as JSON Lines files with automatic rotation
    when files exceed the configured size limit.

    Args:
        path: Directory path for storing audit files.
        rotation_size_mb: Maximum file size in MB before rotation (default: 100).

    Attributes:
        path: The storage directory path.
        rotation_size_bytes: Maximum file size in bytes.

    Example:
        >>> storage = FileStorage("/var/log/audit")
        >>> entry_id = await storage.write(entry)
        >>> retrieved = await storage.read(entry_id)
    """

    def __init__(self, path: str, rotation_size_mb: int = 100) -> None:
        """
        Initialize file storage.

        Args:
            path: Directory path for storing audit files.
            rotation_size_mb: Maximum file size in MB before rotation.
        """
        self.path = Path(path)
        self.rotation_size_bytes = rotation_size_mb * 1024 * 1024
        self._entry_index: Dict[str, str] = {}  # entry_id -> filename

    def _get_current_filename(self) -> str:
        """Get the current audit file name based on date."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        return f"audit_{date_str}.jsonl"

    def _get_current_filepath(self) -> Path:
        """Get the full path to the current audit file."""
        return self.path / self._get_current_filename()

    async def _ensure_directory(self) -> None:
        """Ensure the storage directory exists."""
        if not self.path.exists():
            os.makedirs(self.path, exist_ok=True)

    async def _should_rotate(self, filepath: Path) -> bool:
        """Check if the file should be rotated based on size."""
        if not filepath.exists():
            return False
        try:
            stat = await aiofiles.os.stat(filepath)
            return stat.st_size >= self.rotation_size_bytes
        except FileNotFoundError:
            return False

    async def _rotate_file(self, filepath: Path) -> None:
        """Rotate the file by adding a sequence number."""
        if not filepath.exists():
            return

        base = filepath.stem
        suffix = filepath.suffix
        counter = 1

        while True:
            new_name = f"{base}_{counter:03d}{suffix}"
            new_path = self.path / new_name
            if not new_path.exists():
                os.rename(filepath, new_path)
                break
            counter += 1

    async def write(self, entry: AuditEntry) -> str:
        """
        Write an audit entry to a JSONL file.

        Auto-rotates the file if it exceeds the configured size limit.

        Args:
            entry: The audit entry to store.

        Returns:
            str: The entry ID.
        """
        await self._ensure_directory()
        filepath = self._get_current_filepath()

        if await self._should_rotate(filepath):
            await self._rotate_file(filepath)

        entry_json = json.dumps(entry.to_dict())

        async with aiofiles.open(filepath, "a", encoding="utf-8") as f:
            await f.write(entry_json + "\n")

        self._entry_index[entry.id] = str(filepath)
        return entry.id

    async def read(self, entry_id: str) -> AuditEntry | None:
        """
        Read an audit entry by ID.

        Searches through all JSONL files if the entry is not in the index.

        Args:
            entry_id: The unique identifier of the entry.

        Returns:
            AuditEntry | None: The entry if found, None otherwise.
        """
        await self._ensure_directory()

        # Check index first
        if entry_id in self._entry_index:
            filepath = Path(self._entry_index[entry_id])
            if filepath.exists():
                async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                    async for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            if data.get("id") == entry_id:
                                return AuditEntry.from_dict(data)

        # Search all files
        for filepath in sorted(self.path.glob("audit_*.jsonl")):
            async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        if data.get("id") == entry_id:
                            self._entry_index[entry_id] = str(filepath)
                            return AuditEntry.from_dict(data)

        return None

    async def list_entries(
        self, start: datetime, end: datetime
    ) -> List[AuditEntry]:
        """
        List all entries within a time range.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).

        Returns:
            List[AuditEntry]: Entries within the specified time range.
        """
        await self._ensure_directory()
        entries: List[AuditEntry] = []

        for filepath in sorted(self.path.glob("audit_*.jsonl")):
            async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        timestamp = datetime.fromisoformat(data["timestamp"])
                        if start <= timestamp <= end:
                            entries.append(AuditEntry.from_dict(data))

        return entries

    async def delete(self, entry_id: str) -> bool:
        """
        Delete an entry by ID.

        Note: This rewrites the file without the deleted entry, which may be
        slow for large files. Consider using retention policies instead.

        Args:
            entry_id: The unique identifier of the entry to delete.

        Returns:
            bool: True if the entry was deleted, False if not found.
        """
        await self._ensure_directory()
        deleted = False

        for filepath in sorted(self.path.glob("audit_*.jsonl")):
            lines_to_keep: List[str] = []
            found_in_file = False

            async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        if data.get("id") == entry_id:
                            found_in_file = True
                            deleted = True
                        else:
                            lines_to_keep.append(line)

            if found_in_file:
                async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                    for line in lines_to_keep:
                        await f.write(line + "\n")

                if entry_id in self._entry_index:
                    del self._entry_index[entry_id]
                break

        return deleted

    async def count(self) -> int:
        """
        Count total number of entries in storage.

        Returns:
            int: Total number of stored entries.
        """
        await self._ensure_directory()
        total = 0

        for filepath in self.path.glob("audit_*.jsonl"):
            async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                async for line in f:
                    if line.strip():
                        total += 1

        return total


class MemoryStorage:
    """
    In-memory storage backend for testing and development.

    Stores entries in a dictionary. Data is lost when the process ends.

    Args:
        max_entries: Optional maximum number of entries to store.
            When exceeded, oldest entries are removed.

    Example:
        >>> storage = MemoryStorage(max_entries=1000)
        >>> entry_id = await storage.write(entry)
        >>> count = await storage.count()
    """

    def __init__(self, max_entries: int | None = None) -> None:
        """
        Initialize memory storage.

        Args:
            max_entries: Optional maximum number of entries to store.
        """
        self.max_entries = max_entries
        self._entries: Dict[str, AuditEntry] = {}
        self._insertion_order: List[str] = []

    async def write(self, entry: AuditEntry) -> str:
        """
        Write an audit entry to memory.

        If max_entries is set and exceeded, removes the oldest entry.

        Args:
            entry: The audit entry to store.

        Returns:
            str: The entry ID.
        """
        if (
            self.max_entries
            and len(self._entries) >= self.max_entries
            and entry.id not in self._entries
        ):
            # Remove oldest entry
            oldest_id = self._insertion_order.pop(0)
            del self._entries[oldest_id]

        self._entries[entry.id] = entry
        if entry.id not in self._insertion_order:
            self._insertion_order.append(entry.id)

        return entry.id

    async def read(self, entry_id: str) -> AuditEntry | None:
        """
        Read an audit entry by ID.

        Args:
            entry_id: The unique identifier of the entry.

        Returns:
            AuditEntry | None: The entry if found, None otherwise.
        """
        return self._entries.get(entry_id)

    async def list_entries(
        self, start: datetime, end: datetime
    ) -> List[AuditEntry]:
        """
        List all entries within a time range.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).

        Returns:
            List[AuditEntry]: Entries within the specified time range.
        """
        entries: List[AuditEntry] = []
        for entry in self._entries.values():
            timestamp = datetime.fromisoformat(entry.timestamp)
            if start <= timestamp <= end:
                entries.append(entry)
        return entries

    async def delete(self, entry_id: str) -> bool:
        """
        Delete an entry by ID.

        Args:
            entry_id: The unique identifier of the entry to delete.

        Returns:
            bool: True if the entry was deleted, False if not found.
        """
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._insertion_order.remove(entry_id)
            return True
        return False

    async def count(self) -> int:
        """
        Count total number of entries in storage.

        Returns:
            int: Total number of stored entries.
        """
        return len(self._entries)


class S3Storage:
    """
    AWS S3 storage backend for audit logs.

    Stores each audit entry as a separate JSON file in S3, organized
    by date for easy querying and lifecycle management.

    Requires boto3 to be installed (optional dependency).

    Args:
        bucket: S3 bucket name.
        prefix: Key prefix for audit files (default: "audit/").
        region: AWS region (optional, uses default if not specified).

    File structure:
        {prefix}{YYYY-MM-DD}/{entry_id}.json

    Example:
        >>> storage = S3Storage("my-audit-bucket", prefix="logs/audit/")
        >>> entry_id = await storage.write(entry)
        # Stored at: s3://my-audit-bucket/logs/audit/2024-01-15/abc123.json
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "audit/",
        region: str | None = None,
    ) -> None:
        """
        Initialize S3 storage.

        Args:
            bucket: S3 bucket name.
            prefix: Key prefix for audit files.
            region: AWS region (optional).
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip("/") + "/" if prefix else ""
        self.region = region
        self._client = None

    def _get_client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for S3Storage. "
                    "Install it with: pip install boto3"
                )

            if self.region:
                self._client = boto3.client("s3", region_name=self.region)
            else:
                self._client = boto3.client("s3")
        return self._client

    def _get_key(self, entry: AuditEntry) -> str:
        """Get the S3 key for an entry."""
        timestamp = datetime.fromisoformat(entry.timestamp)
        date_str = timestamp.strftime("%Y-%m-%d")
        return f"{self.prefix}{date_str}/{entry.id}.json"

    def _get_key_from_id(self, entry_id: str, date_str: str) -> str:
        """Get the S3 key from entry ID and date."""
        return f"{self.prefix}{date_str}/{entry_id}.json"

    async def write(self, entry: AuditEntry) -> str:
        """
        Write an audit entry to S3.

        Args:
            entry: The audit entry to store.

        Returns:
            str: The entry ID.
        """
        client = self._get_client()
        key = self._get_key(entry)
        body = json.dumps(entry.to_dict())

        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )

        return entry.id

    async def read(self, entry_id: str) -> AuditEntry | None:
        """
        Read an audit entry by ID.

        Note: This searches through date prefixes which may be slow.
        Consider maintaining an index for production use.

        Args:
            entry_id: The unique identifier of the entry.

        Returns:
            AuditEntry | None: The entry if found, None otherwise.
        """
        client = self._get_client()

        # List all date prefixes
        paginator = client.get_paginator("list_objects_v2")

        for page in paginator.paginate(
            Bucket=self.bucket, Prefix=self.prefix, Delimiter="/"
        ):
            for prefix_info in page.get("CommonPrefixes", []):
                date_prefix = prefix_info["Prefix"]
                key = f"{date_prefix}{entry_id}.json"

                try:
                    response = client.get_object(Bucket=self.bucket, Key=key)
                    body = response["Body"].read().decode("utf-8")
                    data = json.loads(body)
                    return AuditEntry.from_dict(data)
                except client.exceptions.NoSuchKey:
                    continue

        return None

    async def list_entries(
        self, start: datetime, end: datetime
    ) -> List[AuditEntry]:
        """
        List all entries within a time range.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).

        Returns:
            List[AuditEntry]: Entries within the specified time range.
        """
        client = self._get_client()
        entries: List[AuditEntry] = []

        # Generate date range
        current_date = start.date()
        end_date = end.date()

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            date_prefix = f"{self.prefix}{date_str}/"

            paginator = client.get_paginator("list_objects_v2")

            for page in paginator.paginate(
                Bucket=self.bucket, Prefix=date_prefix
            ):
                for obj in page.get("Contents", []):
                    response = client.get_object(
                        Bucket=self.bucket, Key=obj["Key"]
                    )
                    body = response["Body"].read().decode("utf-8")
                    data = json.loads(body)
                    entry = AuditEntry.from_dict(data)

                    timestamp = datetime.fromisoformat(entry.timestamp)
                    if start <= timestamp <= end:
                        entries.append(entry)

            current_date = current_date.replace(
                day=current_date.day + 1
            ) if current_date.day < 28 else (
                current_date.replace(month=current_date.month + 1, day=1)
                if current_date.month < 12
                else current_date.replace(year=current_date.year + 1, month=1, day=1)
            )

        return entries

    async def delete(self, entry_id: str) -> bool:
        """
        Delete an entry by ID.

        Args:
            entry_id: The unique identifier of the entry to delete.

        Returns:
            bool: True if the entry was deleted, False if not found.
        """
        client = self._get_client()

        # Find the entry first
        paginator = client.get_paginator("list_objects_v2")

        for page in paginator.paginate(
            Bucket=self.bucket, Prefix=self.prefix, Delimiter="/"
        ):
            for prefix_info in page.get("CommonPrefixes", []):
                date_prefix = prefix_info["Prefix"]
                key = f"{date_prefix}{entry_id}.json"

                try:
                    client.head_object(Bucket=self.bucket, Key=key)
                    client.delete_object(Bucket=self.bucket, Key=key)
                    return True
                except client.exceptions.ClientError:
                    continue

        return False

    async def count(self) -> int:
        """
        Count total number of entries in storage.

        Returns:
            int: Total number of stored entries.
        """
        client = self._get_client()
        total = 0

        paginator = client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".json"):
                    total += 1

        return total


def create_entry_id() -> str:
    """Generate a unique entry ID."""
    return str(uuid.uuid4())
