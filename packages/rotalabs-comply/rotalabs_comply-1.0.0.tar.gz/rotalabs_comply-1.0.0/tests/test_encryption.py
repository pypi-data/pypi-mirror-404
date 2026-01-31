"""Tests for encryption utilities."""

import pytest


def test_generate_key():
    """Test key generation."""
    from rotalabs_comply.audit.encryption import generate_key

    key = generate_key()

    # Fernet keys are 44 bytes base64 encoded
    assert isinstance(key, bytes)
    assert len(key) == 44

    # Generate another key and verify uniqueness
    key2 = generate_key()
    assert key != key2


def test_encrypt_decrypt_bytes():
    """Test round-trip encryption and decryption of bytes."""
    from rotalabs_comply.audit.encryption import decrypt, encrypt, generate_key

    key = generate_key()
    original_data = b"This is secret data for testing"

    # Encrypt
    encrypted = encrypt(original_data, key)
    assert isinstance(encrypted, bytes)
    assert encrypted != original_data

    # Decrypt
    decrypted = decrypt(encrypted, key)
    assert decrypted == original_data


def test_encrypt_decrypt_different_data():
    """Test encryption with various data types."""
    from rotalabs_comply.audit.encryption import decrypt, encrypt, generate_key

    key = generate_key()

    # Test with empty bytes
    empty_encrypted = encrypt(b"", key)
    assert decrypt(empty_encrypted, key) == b""

    # Test with unicode content
    unicode_data = "Hello \u4e16\u754c".encode("utf-8")
    encrypted = encrypt(unicode_data, key)
    assert decrypt(encrypted, key) == unicode_data

    # Test with binary data
    binary_data = bytes(range(256))
    encrypted = encrypt(binary_data, key)
    assert decrypt(encrypted, key) == binary_data


def test_encryption_manager_roundtrip():
    """Test EncryptionManager encrypt/decrypt round-trip."""
    from rotalabs_comply.audit.encryption import EncryptionManager, generate_key

    key = generate_key()
    manager = EncryptionManager(key)

    original = "This is sensitive information"
    encrypted = manager.encrypt(original)

    # Encrypted should be different from original
    assert encrypted != original
    assert isinstance(encrypted, str)

    # Decrypt should return original
    decrypted = manager.decrypt(encrypted)
    assert decrypted == original


def test_encryption_manager_auto_key():
    """Test EncryptionManager with auto-generated key."""
    from rotalabs_comply.audit.encryption import EncryptionManager

    # Create manager without providing a key
    manager = EncryptionManager()

    # Should auto-generate a key
    key = manager.get_key()
    assert key is not None
    assert len(key) == 44

    # Should be able to encrypt/decrypt
    original = "Auto-key encryption test"
    encrypted = manager.encrypt(original)
    decrypted = manager.decrypt(encrypted)
    assert decrypted == original


def test_encryption_manager_get_key():
    """Test retrieving the encryption key."""
    from rotalabs_comply.audit.encryption import EncryptionManager, generate_key

    original_key = generate_key()
    manager = EncryptionManager(original_key)

    retrieved_key = manager.get_key()
    assert retrieved_key == original_key


def test_encryption_manager_different_instances():
    """Test that managers with same key can decrypt each other's data."""
    from rotalabs_comply.audit.encryption import EncryptionManager, generate_key

    key = generate_key()
    manager1 = EncryptionManager(key)
    manager2 = EncryptionManager(key)

    original = "Cross-manager test"
    encrypted = manager1.encrypt(original)

    # Manager 2 should be able to decrypt
    decrypted = manager2.decrypt(encrypted)
    assert decrypted == original


def test_hash_content():
    """Test SHA-256 content hashing."""
    from rotalabs_comply.audit.encryption import hash_content

    content = "hello world"
    hashed = hash_content(content)

    # SHA-256 produces a 64-character hex string
    assert len(hashed) == 64
    assert isinstance(hashed, str)

    # Known SHA-256 hash for "hello world"
    expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert hashed == expected_hash


def test_hash_content_deterministic():
    """Test that same input produces same hash."""
    from rotalabs_comply.audit.encryption import hash_content

    content = "consistent hashing test"

    hash1 = hash_content(content)
    hash2 = hash_content(content)

    assert hash1 == hash2


def test_hash_content_different_inputs():
    """Test that different inputs produce different hashes."""
    from rotalabs_comply.audit.encryption import hash_content

    hash1 = hash_content("input one")
    hash2 = hash_content("input two")
    hash3 = hash_content("input one ")  # With trailing space

    assert hash1 != hash2
    assert hash1 != hash3


def test_hash_content_unicode():
    """Test hashing with unicode content."""
    from rotalabs_comply.audit.encryption import hash_content

    unicode_content = "Hello \u4e16\u754c \U0001F600"
    hashed = hash_content(unicode_content)

    assert len(hashed) == 64
    # Should be deterministic
    assert hash_content(unicode_content) == hashed


def test_decrypt_with_wrong_key():
    """Test that decryption with wrong key fails."""
    from cryptography.fernet import InvalidToken

    from rotalabs_comply.audit.encryption import decrypt, encrypt, generate_key

    key1 = generate_key()
    key2 = generate_key()

    encrypted = encrypt(b"secret", key1)

    # Decrypting with wrong key should raise
    with pytest.raises(InvalidToken):
        decrypt(encrypted, key2)
