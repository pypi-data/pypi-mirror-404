"""
Audit logging module for AI compliance.

This module provides comprehensive audit logging capabilities for AI systems,
including encrypted storage, multiple backend options, and retention management.

Classes:
    AuditLogger: Main interface for logging AI interactions.
    AuditEntry: Data class representing a single audit log entry.
    EncryptionManager: High-level encryption utilities for content protection.
    StorageBackend: Protocol for implementing custom storage backends.
    FileStorage: JSONL file-based storage with rotation.
    MemoryStorage: In-memory storage for testing.
    S3Storage: AWS S3 storage backend.

Functions:
    generate_key: Generate a new Fernet encryption key.
    encrypt: Low-level encryption function.
    decrypt: Low-level decryption function.
    hash_content: Compute SHA-256 hash of content.

Example:
    Basic audit logging:

    >>> from rotalabs_comply.audit import AuditLogger
    >>> logger = AuditLogger("/var/log/audit")
    >>> entry_id = await logger.log(
    ...     input="User question",
    ...     output="AI response",
    ...     provider="openai",
    ...     model="gpt-4",
    ... )

    With encryption:

    >>> from rotalabs_comply.audit import AuditLogger, EncryptionManager
    >>> encryption = EncryptionManager()
    >>> logger = AuditLogger(
    ...     "/var/log/audit",
    ...     encryption=encryption,
    ...     store_content=True,
    ... )
    >>> # Save the key securely!
    >>> key = encryption.get_key()

    With S3 storage:

    >>> from rotalabs_comply.audit import AuditLogger, S3Storage
    >>> storage = S3Storage("my-audit-bucket", prefix="audit/")
    >>> logger = AuditLogger(storage)
"""

from .encryption import (
    EncryptionManager,
    decrypt,
    encrypt,
    generate_key,
    hash_content,
)
from .logger import AuditLogger
from .storage import (
    AuditEntry,
    FileStorage,
    MemoryStorage,
    S3Storage,
    StorageBackend,
    create_entry_id,
)

__all__ = [
    # Main classes
    "AuditLogger",
    "AuditEntry",
    # Encryption
    "EncryptionManager",
    "generate_key",
    "encrypt",
    "decrypt",
    "hash_content",
    # Storage backends
    "StorageBackend",
    "FileStorage",
    "MemoryStorage",
    "S3Storage",
    # Utilities
    "create_entry_id",
]
