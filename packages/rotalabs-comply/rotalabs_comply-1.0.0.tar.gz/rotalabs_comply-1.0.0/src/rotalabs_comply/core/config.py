"""
Configuration classes for rotalabs-comply.

This module defines configuration models for audit logging and storage
backends, using Pydantic v2 for validation and type safety.
"""

import secrets
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuditConfig(BaseModel):
    """
    Configuration for audit logging behavior.

    This model defines how audit entries are stored, encrypted,
    rotated, and retained over time.

    Attributes:
        destination: File path or S3 URL (s3://bucket/prefix) for audit logs.
        encryption_enabled: Whether to encrypt audit log data at rest.
        encryption_key: Base64-encoded encryption key (auto-generated if not provided).
        retention_days: Number of days to retain audit logs before deletion.
        max_file_size_mb: Maximum size of a single audit log file before rotation.
        rotation_enabled: Whether to enable automatic log rotation.
        compression_enabled: Whether to compress audit log files.

    Example:
        >>> config = AuditConfig(
        ...     destination="/var/log/ai-audit/",
        ...     encryption_enabled=True,
        ...     retention_days=365,
        ...     rotation_enabled=True,
        ... )

        >>> s3_config = AuditConfig(
        ...     destination="s3://my-bucket/audit-logs/",
        ...     encryption_enabled=True,
        ...     compression_enabled=True,
        ... )
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_default=True,
        extra="forbid",
    )

    destination: str = Field(
        ...,
        description="File path or S3 URL (s3://bucket/prefix) for audit logs",
    )
    encryption_enabled: bool = Field(
        default=True,
        description="Whether to encrypt audit log data at rest",
    )
    encryption_key: Optional[str] = Field(
        default=None,
        description="Base64-encoded encryption key (auto-generated if not provided)",
    )
    retention_days: int = Field(
        default=365,
        ge=1,
        le=3650,  # Max 10 years
        description="Number of days to retain audit logs before deletion",
    )
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum size of a single audit log file before rotation (MB)",
    )
    rotation_enabled: bool = Field(
        default=True,
        description="Whether to enable automatic log rotation",
    )
    compression_enabled: bool = Field(
        default=False,
        description="Whether to compress audit log files",
    )

    def model_post_init(self, __context) -> None:
        """Auto-generate encryption key if encryption is enabled but no key provided."""
        if self.encryption_enabled and self.encryption_key is None:
            # Generate a secure 256-bit key (32 bytes) as hex string
            object.__setattr__(self, "encryption_key", secrets.token_hex(32))

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: str) -> str:
        """Validate that destination is a valid path or S3 URL."""
        v = v.strip()
        if not v:
            raise ValueError("destination cannot be empty")
        # Allow file paths (absolute or relative) and S3 URLs
        if v.startswith("s3://"):
            # Basic S3 URL validation
            parts = v[5:].split("/", 1)
            if not parts[0]:
                raise ValueError("S3 URL must include bucket name")
        return v

    @property
    def is_s3_destination(self) -> bool:
        """Check if the destination is an S3 URL."""
        return self.destination.startswith("s3://")

    @property
    def s3_bucket(self) -> Optional[str]:
        """Extract S3 bucket name from destination if applicable."""
        if not self.is_s3_destination:
            return None
        return self.destination[5:].split("/", 1)[0]

    @property
    def s3_prefix(self) -> Optional[str]:
        """Extract S3 key prefix from destination if applicable."""
        if not self.is_s3_destination:
            return None
        parts = self.destination[5:].split("/", 1)
        return parts[1] if len(parts) > 1 else ""


class StorageConfig(BaseModel):
    """
    Configuration for storage backend selection and settings.

    This model defines which storage backend to use and its
    specific configuration options.

    Attributes:
        backend: Storage backend type ("file", "s3", or "memory").
        path: Local file path for file backend.
        bucket: S3 bucket name for S3 backend.
        prefix: S3 key prefix for organizing objects.
        region: AWS region for S3 backend.

    Example:
        >>> file_storage = StorageConfig(
        ...     backend="file",
        ...     path="/var/log/ai-audit/",
        ... )

        >>> s3_storage = StorageConfig(
        ...     backend="s3",
        ...     bucket="my-audit-bucket",
        ...     prefix="prod/audit-logs/",
        ...     region="us-west-2",
        ... )

        >>> memory_storage = StorageConfig(
        ...     backend="memory",  # For testing
        ... )
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_default=True,
        extra="forbid",
    )

    backend: Literal["file", "s3", "memory"] = Field(
        default="file",
        description="Storage backend type",
    )
    path: Optional[str] = Field(
        default=None,
        description="Local file path for file backend",
    )
    bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket name for S3 backend",
    )
    prefix: Optional[str] = Field(
        default=None,
        description="S3 key prefix for organizing objects",
    )
    region: Optional[str] = Field(
        default=None,
        description="AWS region for S3 backend",
    )

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize file path."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v: Optional[str]) -> Optional[str]:
        """Validate S3 bucket name."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            # Basic S3 bucket naming validation
            if len(v) < 3 or len(v) > 63:
                raise ValueError("S3 bucket name must be between 3 and 63 characters")
            if not v[0].isalnum():
                raise ValueError("S3 bucket name must start with a letter or number")
        return v

    def model_post_init(self, __context) -> None:
        """Validate backend-specific requirements."""
        if self.backend == "file" and not self.path:
            raise ValueError("path is required for file backend")
        if self.backend == "s3" and not self.bucket:
            raise ValueError("bucket is required for S3 backend")
