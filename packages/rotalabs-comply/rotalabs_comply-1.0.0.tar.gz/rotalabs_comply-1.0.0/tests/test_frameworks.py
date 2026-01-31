"""Tests for compliance frameworks."""

from datetime import datetime

import pytest

from rotalabs_comply.frameworks.base import (
    AuditEntry,
    ComplianceProfile,
    RiskLevel,
)
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.hipaa import HIPAAFramework
from rotalabs_comply.frameworks.soc2 import SOC2Framework


@pytest.fixture
def default_profile():
    """Create a default compliance profile for testing."""
    return ComplianceProfile(
        profile_id="test-profile",
        name="Test Profile",
        description="Profile for testing",
    )


@pytest.fixture
def sample_entry():
    """Create a sample audit entry for testing."""
    return AuditEntry(
        entry_id="test-entry-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="user@example.com",
        action="Generated text response",
        resource="gpt-4",
        system_id="ai-system-001",
        data_classification="public",
        user_notified=True,
        human_oversight=True,
        error_handled=True,
        metadata={
            "accuracy_monitored": True,
            "access_controlled": True,
            "monitored": True,
        },
    )


class TestEUAIActFramework:
    """Tests for EU AI Act compliance framework."""

    def test_eu_ai_act_rules(self):
        """Check EU AI Act has expected rules."""
        framework = EUAIActFramework()

        # Check basic properties
        assert framework.name == "EU AI Act"
        assert framework.version == "2024"

        # Check expected rules exist
        rule_ids = [rule.rule_id for rule in framework.rules]
        assert "EUAI-001" in rule_ids  # Human Oversight
        assert "EUAI-002" in rule_ids  # Transparency
        assert "EUAI-003" in rule_ids  # Risk Assessment
        assert "EUAI-004" in rule_ids  # Technical Documentation
        assert "EUAI-005" in rule_ids  # Data Governance
        assert "EUAI-006" in rule_ids  # Robustness
        assert "EUAI-007" in rule_ids  # Accuracy Monitoring
        assert "EUAI-008" in rule_ids  # Cybersecurity

        # Verify rule count
        assert len(framework.rules) == 8

    @pytest.mark.asyncio
    async def test_eu_ai_act_check(self, default_profile, sample_entry):
        """Run compliance check on sample entry."""
        framework = EUAIActFramework()

        result = await framework.check(sample_entry, default_profile)

        # Basic result structure
        assert result.entry_id == sample_entry.entry_id
        assert result.framework == "EU AI Act"
        assert result.framework_version == "2024"
        assert result.timestamp is not None

        # Check counting
        assert result.rules_checked >= 0
        assert result.rules_passed >= 0
        assert isinstance(result.is_compliant, bool)

    @pytest.mark.asyncio
    async def test_eu_ai_act_transparency_violation(self, default_profile):
        """Test transparency rule violation."""
        framework = EUAIActFramework()

        # Create entry without user notification for user-facing interaction
        entry = AuditEntry(
            entry_id="test-transparency",
            timestamp=datetime.utcnow(),
            event_type="inference",  # User-facing event type
            actor="user@example.com",
            action="AI response",
            user_notified=False,  # Violation: user not notified
        )

        result = await framework.check(entry, default_profile)

        # Should have transparency violation
        transparency_violations = [
            v for v in result.violations if v.rule_id == "EUAI-002"
        ]
        assert len(transparency_violations) >= 1

    def test_eu_ai_act_get_rule(self):
        """Test getting specific rule by ID."""
        framework = EUAIActFramework()

        rule = framework.get_rule("EUAI-001")
        assert rule is not None
        assert rule.name == "Human Oversight Documentation"
        assert rule.severity == RiskLevel.HIGH
        assert rule.category == "oversight"

        # Nonexistent rule
        assert framework.get_rule("NONEXISTENT") is None


class TestSOC2Framework:
    """Tests for SOC2 compliance framework."""

    def test_soc2_rules(self):
        """Check SOC2 has expected rules."""
        framework = SOC2Framework()

        # Check basic properties
        assert framework.name == "SOC2 Type II"
        assert framework.version == "2017"

        # Check expected rules exist
        rule_ids = [rule.rule_id for rule in framework.rules]

        # Security (CC) rules
        assert "SOC2-CC6.1" in rule_ids  # Logical Access Controls
        assert "SOC2-CC6.2" in rule_ids  # System Boundary
        assert "SOC2-CC6.3" in rule_ids  # Change Management
        assert "SOC2-CC7.1" in rule_ids  # System Monitoring
        assert "SOC2-CC7.2" in rule_ids  # Incident Response
        assert "SOC2-CC8.1" in rule_ids  # Availability Monitoring

        # Availability (A) rules
        assert "SOC2-A1.1" in rule_ids  # Recovery Objectives

        # Processing Integrity (PI) rules
        assert "SOC2-PI1.1" in rule_ids

        # Confidentiality (C) rules
        assert "SOC2-C1.1" in rule_ids

        # Privacy (P) rules
        assert "SOC2-P1.1" in rule_ids

    @pytest.mark.asyncio
    async def test_soc2_check(self, default_profile, sample_entry):
        """Run SOC2 compliance check on sample entry."""
        framework = SOC2Framework()

        result = await framework.check(sample_entry, default_profile)

        assert result.entry_id == sample_entry.entry_id
        assert result.framework == "SOC2 Type II"
        assert result.framework_version == "2017"

    def test_soc2_get_rule(self):
        """Test getting specific SOC2 rule."""
        framework = SOC2Framework()

        rule = framework.get_rule("SOC2-CC6.1")
        assert rule is not None
        assert rule.name == "Logical Access Controls"
        assert rule.category == "security"


class TestHIPAAFramework:
    """Tests for HIPAA compliance framework."""

    def test_hipaa_rules(self):
        """Check HIPAA has expected rules."""
        framework = HIPAAFramework()

        # Check basic properties
        assert framework.name == "HIPAA"
        assert framework.version == "1996/2013"

        # Check expected rules exist
        rule_ids = [rule.rule_id for rule in framework.rules]

        # Security Rule - Technical Safeguards
        assert "HIPAA-164.312(a)" in rule_ids  # Access Control
        assert "HIPAA-164.312(b)" in rule_ids  # Audit Controls
        assert "HIPAA-164.312(c)" in rule_ids  # Integrity Controls
        assert "HIPAA-164.312(d)" in rule_ids  # Authentication
        assert "HIPAA-164.312(e)" in rule_ids  # Transmission Security

        # Privacy Rule
        assert "HIPAA-164.502" in rule_ids  # Uses and Disclosures
        assert "HIPAA-164.514" in rule_ids  # De-identification
        assert "HIPAA-164.530" in rule_ids  # Administrative Requirements

    @pytest.mark.asyncio
    async def test_hipaa_check_non_phi(self, default_profile, sample_entry):
        """Test HIPAA check on non-PHI data (should pass all rules)."""
        framework = HIPAAFramework()

        # Sample entry has public data classification, not PHI
        result = await framework.check(sample_entry, default_profile)

        # Should be compliant since no PHI involved
        assert result.is_compliant is True
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_hipaa_check_phi_data(self, default_profile):
        """Test HIPAA check on PHI data."""
        framework = HIPAAFramework()

        # Create entry with PHI data classification
        phi_entry = AuditEntry(
            entry_id="phi-entry-001",
            timestamp=datetime.utcnow(),
            event_type="data_access",
            actor="doctor@hospital.com",
            action="Accessed patient record",
            data_classification="PHI",
            metadata={
                "access_controlled": True,
                "authenticated": True,
                "purpose_documented": True,
                "minimum_necessary_applied": True,
                "policy_compliant": True,
            },
        )

        result = await framework.check(phi_entry, default_profile)

        # May have violations depending on completeness of metadata
        assert result.entry_id == "phi-entry-001"
        assert result.framework == "HIPAA"


class TestFrameworkCategories:
    """Tests for framework category listing."""

    def test_eu_ai_act_categories(self):
        """Test EU AI Act list_categories()."""
        framework = EUAIActFramework()

        categories = framework.list_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "transparency" in categories
        assert "oversight" in categories
        assert "risk_management" in categories
        assert "documentation" in categories
        assert "security" in categories

        # Should be sorted
        assert categories == sorted(categories)

    def test_soc2_categories(self):
        """Test SOC2 list_categories()."""
        framework = SOC2Framework()

        categories = framework.list_categories()

        assert "security" in categories
        assert "availability" in categories
        assert "processing_integrity" in categories
        assert "confidentiality" in categories
        assert "privacy" in categories

    def test_hipaa_categories(self):
        """Test HIPAA list_categories()."""
        framework = HIPAAFramework()

        categories = framework.list_categories()

        assert "access_control" in categories
        assert "audit" in categories
        assert "integrity" in categories
        assert "authentication" in categories
        assert "transmission" in categories
        assert "privacy" in categories


class TestProfileFiltering:
    """Tests for compliance profile filtering."""

    @pytest.mark.asyncio
    async def test_profile_category_filter(self, sample_entry):
        """Test filtering by enabled categories."""
        framework = EUAIActFramework()

        # Profile with only transparency category
        profile = ComplianceProfile(
            profile_id="transparency-only",
            name="Transparency Only",
            enabled_categories=["transparency"],
        )

        result = await framework.check(sample_entry, profile)

        # Should only check transparency rules
        for violation in result.violations:
            assert violation.category == "transparency"

    @pytest.mark.asyncio
    async def test_profile_excluded_rules(self, sample_entry):
        """Test excluding specific rules."""
        framework = EUAIActFramework()

        # Profile excluding specific rules
        profile = ComplianceProfile(
            profile_id="exclude-some",
            name="Exclude Some Rules",
            excluded_rules=["EUAI-001", "EUAI-002"],
        )

        result = await framework.check(sample_entry, profile)

        # Excluded rules should not appear in violations
        violated_rule_ids = [v.rule_id for v in result.violations]
        assert "EUAI-001" not in violated_rule_ids
        assert "EUAI-002" not in violated_rule_ids

    @pytest.mark.asyncio
    async def test_profile_min_severity(self, sample_entry):
        """Test minimum severity filtering."""
        framework = EUAIActFramework()

        # Profile with high minimum severity
        profile = ComplianceProfile(
            profile_id="high-severity-only",
            name="High Severity Only",
            min_severity=RiskLevel.HIGH,
        )

        result = await framework.check(sample_entry, profile)

        # All violations should be HIGH or CRITICAL severity
        for violation in result.violations:
            assert violation.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]
