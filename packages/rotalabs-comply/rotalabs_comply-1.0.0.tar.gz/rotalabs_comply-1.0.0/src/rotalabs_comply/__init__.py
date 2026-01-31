"""rotalabs-comply - AI compliance and audit logging infrastructure.

Provides comprehensive compliance tooling for AI systems:
- Audit logging with encryption and multiple storage backends
- Compliance frameworks (EU AI Act, SOC2, HIPAA)
- Report generation with customizable templates
- Privacy-first design (hash-only or encrypted content)

Example:
    >>> from rotalabs_comply import (
    ...     AuditLogger,
    ...     EncryptionManager,
    ...     ComplianceProfile,
    ...     EUAIActFramework,
    ...     ReportGenerator,
    ... )
    >>>
    >>> # Set up encrypted audit logging
    >>> encryption = EncryptionManager()
    >>> logger = AuditLogger("/var/log/audit", encryption=encryption)
    >>>
    >>> # Log an AI interaction
    >>> entry_id = await logger.log(
    ...     input="User question",
    ...     output="AI response",
    ...     provider="openai",
    ...     model="gpt-4",
    ...     safety_passed=True,
    ... )
    >>>
    >>> # Check compliance
    >>> framework = EUAIActFramework()
    >>> result = await framework.check(entry, profile)
    >>>
    >>> # Generate reports
    >>> generator = ReportGenerator(logger)
    >>> report = await generator.generate(
    ...     period_start=start_date,
    ...     period_end=end_date,
    ...     profile=profile,
    ... )
"""

from rotalabs_comply._version import __version__

# Core types and configuration
from rotalabs_comply.core import (
    # Enums
    RiskLevel,
    Framework,
    # Data models
    AuditEntry,
    ComplianceProfile,
    ComplianceViolation,
    ComplianceCheckResult,
    # Configuration
    AuditConfig,
    StorageConfig,
    # Exceptions
    ComplianceError,
    AuditError,
    StorageError,
    EncryptionError,
    ValidationError,
    FrameworkError,
)

# Audit logging
from rotalabs_comply.audit import (
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

# Compliance frameworks
from rotalabs_comply.frameworks import (
    ComplianceRule,
    ComplianceFramework,
    BaseFramework,
    EUAIActFramework,
    SOC2Framework,
    HIPAAFramework,
    GDPRFramework,
    NISTAIRMFFramework,
    ISO42001Framework,
    MASFramework,
)

# Report generation
from rotalabs_comply.reports import (
    ReportSection,
    ReportTemplate,
    ComplianceReport,
    ReportGenerator,
    EU_AI_ACT_TEMPLATE,
    SOC2_TEMPLATE,
    HIPAA_TEMPLATE,
    EXECUTIVE_SUMMARY_TEMPLATE,
)

# Utilities
from rotalabs_comply.utils import (
    format_period,
    parse_period,
    calculate_statistics,
    group_by_date,
    severity_weight,
    json_serializer,
    dump_json,
    load_json,
)

__all__ = [
    # Version
    "__version__",
    # Enums
    "RiskLevel",
    "Framework",
    # Core data models
    "AuditEntry",
    "ComplianceProfile",
    "ComplianceViolation",
    "ComplianceCheckResult",
    # Configuration
    "AuditConfig",
    "StorageConfig",
    # Exceptions
    "ComplianceError",
    "AuditError",
    "StorageError",
    "EncryptionError",
    "ValidationError",
    "FrameworkError",
    # Audit logging
    "AuditLogger",
    "EncryptionManager",
    "generate_key",
    "encrypt",
    "decrypt",
    "hash_content",
    "StorageBackend",
    "FileStorage",
    "MemoryStorage",
    "S3Storage",
    # Frameworks
    "ComplianceRule",
    "ComplianceFramework",
    "BaseFramework",
    "EUAIActFramework",
    "SOC2Framework",
    "HIPAAFramework",
    "GDPRFramework",
    "NISTAIRMFFramework",
    "ISO42001Framework",
    "MASFramework",
    # Reports
    "ReportSection",
    "ReportTemplate",
    "ComplianceReport",
    "ReportGenerator",
    "EU_AI_ACT_TEMPLATE",
    "SOC2_TEMPLATE",
    "HIPAA_TEMPLATE",
    "EXECUTIVE_SUMMARY_TEMPLATE",
    # Utilities
    "format_period",
    "parse_period",
    "calculate_statistics",
    "group_by_date",
    "severity_weight",
    "json_serializer",
    "dump_json",
    "load_json",
]
