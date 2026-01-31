"""Tests for core data types and enums."""

from datetime import datetime

import pytest


def test_risk_level_enum():
    """Test RiskLevel enum values."""
    from rotalabs_comply.core.types import RiskLevel

    # Test all values exist
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
    assert RiskLevel.CRITICAL.value == "critical"

    # Test string conversion
    assert str(RiskLevel.LOW) == "RiskLevel.LOW"
    assert RiskLevel.LOW.name == "LOW"

    # Test comparison
    assert RiskLevel.LOW != RiskLevel.HIGH
    assert RiskLevel.MEDIUM == RiskLevel.MEDIUM


def test_framework_enum():
    """Test Framework enum values."""
    from rotalabs_comply.core.types import Framework

    # Test all values exist
    assert Framework.EU_AI_ACT.value == "eu_ai_act"
    assert Framework.SOC2.value == "soc2"
    assert Framework.HIPAA.value == "hipaa"
    assert Framework.GDPR.value == "gdpr"
    assert Framework.NIST_AI_RMF.value == "nist_ai_rmf"
    assert Framework.ISO_42001.value == "iso_42001"

    # Test membership
    assert Framework.EU_AI_ACT in Framework


def test_audit_entry_creation():
    """Create AuditEntry with required fields."""
    from rotalabs_comply.core.types import AuditEntry

    entry = AuditEntry(
        input_hash="abc123def456",
        output_hash="789xyz012",
        safety_passed=True,
        latency_ms=150.5,
    )

    # Verify required fields
    assert entry.input_hash == "abc123def456"
    assert entry.output_hash == "789xyz012"
    assert entry.safety_passed is True
    assert entry.latency_ms == 150.5

    # Verify auto-generated fields
    assert entry.id is not None
    assert len(entry.id) > 0
    assert entry.timestamp is not None
    assert isinstance(entry.timestamp, datetime)


def test_audit_entry_optional_fields():
    """Test AuditEntry optional fields."""
    from rotalabs_comply.core.types import AuditEntry

    entry = AuditEntry(
        input_hash="abc123",
        output_hash="def456",
        safety_passed=True,
        latency_ms=100.0,
        provider="openai",
        model="gpt-4",
        conversation_id="conv-123",
        input_content="What is 2+2?",
        output_content="4",
        detectors_triggered=["toxicity", "pii"],
        block_reason="PII detected",
        alerts=["Alert 1", "Alert 2"],
        input_tokens=10,
        output_tokens=5,
        metadata={"session_id": "sess-123", "user": "test"},
    )

    # Verify optional fields are set correctly
    assert entry.provider == "openai"
    assert entry.model == "gpt-4"
    assert entry.conversation_id == "conv-123"
    assert entry.input_content == "What is 2+2?"
    assert entry.output_content == "4"
    assert entry.detectors_triggered == ["toxicity", "pii"]
    assert entry.block_reason == "PII detected"
    assert entry.alerts == ["Alert 1", "Alert 2"]
    assert entry.input_tokens == 10
    assert entry.output_tokens == 5
    assert entry.metadata == {"session_id": "sess-123", "user": "test"}


def test_compliance_profile_defaults():
    """Test ComplianceProfile default values."""
    from rotalabs_comply.core.types import ComplianceProfile, RiskLevel

    profile = ComplianceProfile()

    # Verify default values
    assert profile.frameworks == []
    assert profile.risk_level == RiskLevel.MEDIUM
    assert profile.required_documentation is True
    assert profile.data_retention_days == 365
    assert profile.encrypt_audit_logs is True
    assert profile.store_content is False
    assert profile.custom_policies == {}


def test_compliance_profile_custom_values():
    """Test ComplianceProfile with custom values."""
    from rotalabs_comply.core.types import ComplianceProfile, Framework, RiskLevel

    profile = ComplianceProfile(
        frameworks=[Framework.EU_AI_ACT, Framework.GDPR],
        risk_level=RiskLevel.LOW,
        required_documentation=False,
        data_retention_days=730,
        encrypt_audit_logs=False,
        store_content=True,
        custom_policies={"allow_pii": False},
    )

    assert len(profile.frameworks) == 2
    assert Framework.EU_AI_ACT in profile.frameworks
    assert profile.risk_level == RiskLevel.LOW
    assert profile.required_documentation is False
    assert profile.data_retention_days == 730
    assert profile.encrypt_audit_logs is False
    assert profile.store_content is True
    assert profile.custom_policies == {"allow_pii": False}


def test_compliance_violation_creation():
    """Test ComplianceViolation creation."""
    from rotalabs_comply.core.types import ComplianceViolation, Framework, RiskLevel

    violation = ComplianceViolation(
        framework=Framework.EU_AI_ACT,
        rule_id="EUAI-001",
        severity=RiskLevel.HIGH,
        description="Human oversight documentation missing",
        evidence={"field": "human_oversight", "value": False},
        remediation="Add human oversight documentation",
    )

    assert violation.framework == Framework.EU_AI_ACT
    assert violation.rule_id == "EUAI-001"
    assert violation.severity == RiskLevel.HIGH
    assert violation.description == "Human oversight documentation missing"
    assert violation.evidence == {"field": "human_oversight", "value": False}
    assert violation.remediation == "Add human oversight documentation"
    assert violation.timestamp is not None


def test_compliance_check_result():
    """Test ComplianceCheckResult creation."""
    from rotalabs_comply.core.types import (
        ComplianceCheckResult,
        ComplianceViolation,
        Framework,
        RiskLevel,
    )

    violation = ComplianceViolation(
        framework=Framework.SOC2,
        rule_id="SOC2-CC6.1",
        severity=RiskLevel.MEDIUM,
        description="Access control missing",
        evidence={},
        remediation="Implement RBAC",
    )

    result = ComplianceCheckResult(
        passed=False,
        framework=Framework.SOC2,
        violations=[violation],
        warnings=["Consider enabling MFA"],
        recommendations=["Enable audit logging"],
    )

    assert result.passed is False
    assert result.framework == Framework.SOC2
    assert len(result.violations) == 1
    assert result.violations[0].rule_id == "SOC2-CC6.1"
    assert result.warnings == ["Consider enabling MFA"]
    assert result.recommendations == ["Enable audit logging"]
    assert result.checked_at is not None


def test_compliance_check_result_passed():
    """Test ComplianceCheckResult with no violations."""
    from rotalabs_comply.core.types import ComplianceCheckResult, Framework

    result = ComplianceCheckResult(
        passed=True,
        framework=Framework.HIPAA,
        violations=[],
        warnings=[],
        recommendations=[],
    )

    assert result.passed is True
    assert len(result.violations) == 0
