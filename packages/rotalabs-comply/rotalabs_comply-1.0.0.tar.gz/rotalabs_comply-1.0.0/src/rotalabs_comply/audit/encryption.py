"""
Encryption utilities for audit log data.

This module provides encryption, decryption, and hashing utilities for
securing audit log content. Uses Fernet symmetric encryption from the
cryptography library.
"""

from __future__ import annotations

import base64
import hashlib
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet

if TYPE_CHECKING:
    pass


def generate_key() -> bytes:
    """
    Generate a new Fernet encryption key.

    Returns:
        bytes: A 32-byte URL-safe base64-encoded key suitable for Fernet encryption.

    Example:
        >>> key = generate_key()
        >>> len(key)
        44
    """
    return Fernet.generate_key()


def encrypt(data: bytes, key: bytes) -> bytes:
    """
    Encrypt data using Fernet symmetric encryption.

    Args:
        data: The raw bytes to encrypt.
        key: The Fernet encryption key (from generate_key()).

    Returns:
        bytes: The encrypted data as bytes.

    Raises:
        cryptography.fernet.InvalidToken: If the key is invalid.

    Example:
        >>> key = generate_key()
        >>> encrypted = encrypt(b"secret message", key)
        >>> isinstance(encrypted, bytes)
        True
    """
    f = Fernet(key)
    return f.encrypt(data)


def decrypt(data: bytes, key: bytes) -> bytes:
    """
    Decrypt data that was encrypted with Fernet.

    Args:
        data: The encrypted bytes to decrypt.
        key: The same Fernet key used for encryption.

    Returns:
        bytes: The original decrypted data.

    Raises:
        cryptography.fernet.InvalidToken: If the key is wrong or data is corrupted.

    Example:
        >>> key = generate_key()
        >>> encrypted = encrypt(b"secret message", key)
        >>> decrypt(encrypted, key)
        b'secret message'
    """
    f = Fernet(key)
    return f.decrypt(data)


def hash_content(content: str) -> str:
    """
    Compute SHA-256 hash of string content.

    Useful for storing content fingerprints without storing actual content,
    enabling verification while maintaining privacy.

    Args:
        content: The string content to hash.

    Returns:
        str: Hexadecimal representation of the SHA-256 hash.

    Example:
        >>> hash_content("hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class EncryptionManager:
    """
    High-level encryption manager for string data.

    Provides a convenient interface for encrypting and decrypting string data,
    with automatic key generation if not provided.

    Args:
        key: Optional Fernet encryption key. If not provided, a new key is generated.

    Attributes:
        _key: The encryption key (kept private).
        _fernet: The Fernet cipher instance.

    Example:
        >>> manager = EncryptionManager()
        >>> encrypted = manager.encrypt("sensitive data")
        >>> manager.decrypt(encrypted)
        'sensitive data'

        >>> # Use existing key
        >>> key = generate_key()
        >>> manager = EncryptionManager(key)
        >>> manager.get_key() == key
        True
    """

    def __init__(self, key: bytes | None = None) -> None:
        """
        Initialize the encryption manager.

        Args:
            key: Optional Fernet encryption key. If None, generates a new key.
        """
        self._key = key if key is not None else generate_key()
        self._fernet = Fernet(self._key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string and return base64-encoded result.

        Args:
            data: The string to encrypt.

        Returns:
            str: Base64-encoded encrypted string, safe for storage in JSON.

        Example:
            >>> manager = EncryptionManager()
            >>> encrypted = manager.encrypt("secret")
            >>> isinstance(encrypted, str)
            True
        """
        encrypted_bytes = self._fernet.encrypt(data.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_bytes).decode("ascii")

    def decrypt(self, data: str) -> str:
        """
        Decrypt a base64-encoded encrypted string.

        Args:
            data: The base64-encoded encrypted string (from encrypt()).

        Returns:
            str: The original decrypted string.

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails.

        Example:
            >>> manager = EncryptionManager()
            >>> encrypted = manager.encrypt("secret")
            >>> manager.decrypt(encrypted)
            'secret'
        """
        encrypted_bytes = base64.urlsafe_b64decode(data.encode("ascii"))
        decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode("utf-8")

    def get_key(self) -> bytes:
        """
        Get the encryption key.

        Returns:
            bytes: The Fernet encryption key. Store this securely!

        Warning:
            The encryption key must be stored securely. If lost, encrypted
            data cannot be recovered.

        Example:
            >>> manager = EncryptionManager()
            >>> key = manager.get_key()
            >>> len(key)
            44
        """
        return self._key
