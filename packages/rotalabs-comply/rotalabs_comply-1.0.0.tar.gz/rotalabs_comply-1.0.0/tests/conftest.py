"""Pytest configuration and shared fixtures for rotalabs-comply tests."""

import pytest


@pytest.fixture
def tmp_audit_dir(tmp_path):
    """Create a temporary directory for audit files."""
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    return audit_dir
