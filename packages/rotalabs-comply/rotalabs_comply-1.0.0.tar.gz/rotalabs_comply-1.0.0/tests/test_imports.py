"""Tests for verifying package imports and exports."""

import pytest


def test_version():
    """Check version is '0.1.0'."""
    from rotalabs_comply import __version__

    assert __version__ == "0.2.0"


def test_core_imports():
    """Test all core type imports."""
    from rotalabs_comply import (
        RiskLevel,
        Framework,
        AuditEntry,
        ComplianceProfile,
        ComplianceViolation,
        ComplianceCheckResult,
        AuditConfig,
        StorageConfig,
        ComplianceError,
        AuditError,
        StorageError,
        EncryptionError,
        ValidationError,
        FrameworkError,
    )

    # Verify enums
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
    assert RiskLevel.CRITICAL.value == "critical"

    assert Framework.EU_AI_ACT.value == "eu_ai_act"
    assert Framework.SOC2.value == "soc2"
    assert Framework.HIPAA.value == "hipaa"

    # Verify classes are importable
    assert AuditEntry is not None
    assert ComplianceProfile is not None
    assert ComplianceViolation is not None
    assert ComplianceCheckResult is not None
    assert AuditConfig is not None
    assert StorageConfig is not None

    # Verify exceptions are exception subclasses
    assert issubclass(ComplianceError, Exception)
    assert issubclass(AuditError, Exception)
    assert issubclass(StorageError, Exception)
    assert issubclass(EncryptionError, Exception)
    assert issubclass(ValidationError, Exception)
    assert issubclass(FrameworkError, Exception)


def test_audit_imports():
    """Test audit module imports."""
    from rotalabs_comply import (
        AuditLogger,
        EncryptionManager,
        generate_key,
        encrypt,
        decrypt,
        hash_content,
        StorageBackend,
        FileStorage,
        MemoryStorage,
        S3Storage,
    )

    # Verify classes exist
    assert AuditLogger is not None
    assert EncryptionManager is not None
    assert FileStorage is not None
    assert MemoryStorage is not None
    assert S3Storage is not None

    # Verify functions are callable
    assert callable(generate_key)
    assert callable(encrypt)
    assert callable(decrypt)
    assert callable(hash_content)


def test_framework_imports():
    """Test framework imports."""
    from rotalabs_comply import (
        ComplianceRule,
        ComplianceFramework,
        BaseFramework,
        EUAIActFramework,
        SOC2Framework,
        HIPAAFramework,
    )

    # Verify classes exist
    assert ComplianceRule is not None
    assert ComplianceFramework is not None
    assert BaseFramework is not None
    assert EUAIActFramework is not None
    assert SOC2Framework is not None
    assert HIPAAFramework is not None

    # Verify frameworks can be instantiated
    eu_ai = EUAIActFramework()
    soc2 = SOC2Framework()
    hipaa = HIPAAFramework()

    assert eu_ai.name == "EU AI Act"
    assert soc2.name == "SOC2 Type II"
    assert hipaa.name == "HIPAA"


def test_report_imports():
    """Test report module imports."""
    from rotalabs_comply import (
        ReportSection,
        ReportTemplate,
        ComplianceReport,
        ReportGenerator,
        EU_AI_ACT_TEMPLATE,
        SOC2_TEMPLATE,
        HIPAA_TEMPLATE,
        EXECUTIVE_SUMMARY_TEMPLATE,
    )

    # Verify classes exist
    assert ReportSection is not None
    assert ReportTemplate is not None
    assert ComplianceReport is not None
    assert ReportGenerator is not None

    # Verify templates exist
    assert EU_AI_ACT_TEMPLATE is not None
    assert SOC2_TEMPLATE is not None
    assert HIPAA_TEMPLATE is not None
    assert EXECUTIVE_SUMMARY_TEMPLATE is not None


def test_utils_imports():
    """Test utility imports."""
    from rotalabs_comply import (
        format_period,
        parse_period,
        calculate_statistics,
        group_by_date,
        severity_weight,
        json_serializer,
        dump_json,
        load_json,
    )

    # Verify functions are callable
    assert callable(format_period)
    assert callable(parse_period)
    assert callable(calculate_statistics)
    assert callable(group_by_date)
    assert callable(severity_weight)
    assert callable(json_serializer)
    assert callable(dump_json)
    assert callable(load_json)


def test_all_exports():
    """Verify all __all__ items are importable."""
    import rotalabs_comply

    all_exports = rotalabs_comply.__all__

    for name in all_exports:
        assert hasattr(rotalabs_comply, name), f"Missing export: {name}"
        obj = getattr(rotalabs_comply, name)
        assert obj is not None, f"Export is None: {name}"
