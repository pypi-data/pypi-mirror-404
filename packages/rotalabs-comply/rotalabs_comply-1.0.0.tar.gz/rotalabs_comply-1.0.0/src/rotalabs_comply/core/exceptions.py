"""
Custom exceptions for rotalabs-comply.

This module defines the exception hierarchy used throughout the compliance
package for handling various error conditions in audit logging, storage,
encryption, and framework validation.
"""

from typing import Any, Dict, Optional


class ComplianceError(Exception):
    """
    Base exception for all compliance-related errors.

    All other exceptions in this module inherit from this class,
    allowing for broad exception catching when needed.

    Attributes:
        message: Human-readable error description.
        details: Optional dictionary with additional error context.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize a ComplianceError.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional context about the error.
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AuditError(ComplianceError):
    """
    Exception raised for audit logging failures.

    This exception is raised when there are issues with:
    - Writing audit entries
    - Reading audit logs
    - Audit log rotation
    - Audit data validation

    Examples:
        >>> raise AuditError("Failed to write audit entry", {"entry_id": "abc123"})
    """

    pass


class StorageError(ComplianceError):
    """
    Exception raised for storage backend failures.

    This exception is raised when there are issues with:
    - Connecting to storage backends (file, S3, etc.)
    - Reading or writing data to storage
    - Storage configuration problems
    - Permission issues

    Examples:
        >>> raise StorageError("S3 bucket not accessible", {"bucket": "my-bucket"})
    """

    pass


class EncryptionError(ComplianceError):
    """
    Exception raised for encryption/decryption failures.

    This exception is raised when there are issues with:
    - Encrypting audit data
    - Decrypting stored data
    - Key management
    - Invalid encryption configuration

    Examples:
        >>> raise EncryptionError("Invalid encryption key format")
    """

    pass


class ValidationError(ComplianceError):
    """
    Exception raised for data validation failures.

    This exception is raised when there are issues with:
    - Invalid input data format
    - Missing required fields
    - Data type mismatches
    - Schema validation failures

    Attributes:
        field: Optional name of the field that failed validation.
        value: Optional value that caused the validation failure.

    Examples:
        >>> raise ValidationError(
        ...     "Invalid risk level",
        ...     details={"field": "risk_level", "value": "UNKNOWN"}
        ... )
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> None:
        """
        Initialize a ValidationError.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional context.
            field: Optional name of the field that failed validation.
            value: Optional value that caused the validation failure.
        """
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)
        self.field = field
        self.value = value


class FrameworkError(ComplianceError):
    """
    Exception raised for regulatory framework-related failures.

    This exception is raised when there are issues with:
    - Unsupported framework operations
    - Framework rule validation
    - Framework configuration errors
    - Incompatible framework combinations

    Attributes:
        framework: Optional identifier of the framework that caused the error.

    Examples:
        >>> raise FrameworkError(
        ...     "Framework not supported",
        ...     details={"framework": "UNKNOWN_FRAMEWORK"}
        ... )
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        framework: Optional[str] = None,
    ) -> None:
        """
        Initialize a FrameworkError.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional context.
            framework: Optional identifier of the framework that caused the error.
        """
        details = details or {}
        if framework:
            details["framework"] = framework
        super().__init__(message, details)
        self.framework = framework
