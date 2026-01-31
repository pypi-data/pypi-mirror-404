"""
Core data models for rotalabs-comply.

This module defines the primary data structures used throughout the compliance
package, including risk levels, regulatory frameworks, audit entries, and
compliance check results.

All models use Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    """
    Risk severity levels for compliance classification.

    These levels are used to categorize the severity of compliance
    violations and to set risk thresholds for AI systems.

    Attributes:
        LOW: Minor risk with minimal compliance impact.
        MEDIUM: Moderate risk requiring attention.
        HIGH: Significant risk requiring immediate action.
        CRITICAL: Severe risk with potential regulatory consequences.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Framework(str, Enum):
    """
    Supported regulatory compliance frameworks.

    Each framework represents a set of compliance requirements
    that can be validated against AI system operations.

    Attributes:
        EU_AI_ACT: European Union AI Act requirements.
        SOC2: Service Organization Control 2 security standards.
        HIPAA: Health Insurance Portability and Accountability Act.
        GDPR: General Data Protection Regulation.
        NIST_AI_RMF: NIST AI Risk Management Framework.
        ISO_42001: ISO/IEC 42001 AI Management System standard.
        MAS: Monetary Authority of Singapore FEAT principles.
    """

    EU_AI_ACT = "eu_ai_act"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    NIST_AI_RMF = "nist_ai_rmf"
    ISO_42001 = "iso_42001"
    MAS = "mas"


class AuditEntry(BaseModel):
    """
    A single audit log entry capturing an AI system interaction.

    This model captures comprehensive information about AI model invocations,
    including input/output data (or hashes for privacy), safety checks,
    and performance metrics.

    Attributes:
        id: Unique identifier for this audit entry (UUID).
        timestamp: When the interaction occurred.
        provider: AI provider name (e.g., "openai", "anthropic").
        model: Model identifier (e.g., "gpt-4", "claude-3-opus").
        conversation_id: Optional ID linking related interactions.
        input_hash: SHA-256 hash of the input content.
        output_hash: SHA-256 hash of the output content.
        input_content: Actual input text (only if store_content enabled).
        output_content: Actual output text (only if store_content enabled).
        safety_passed: Whether all safety checks passed.
        detectors_triggered: List of detector names that flagged content.
        block_reason: Reason if the interaction was blocked.
        alerts: List of alert messages generated.
        latency_ms: Response time in milliseconds.
        input_tokens: Number of input tokens (if available).
        output_tokens: Number of output tokens (if available).
        metadata: Additional custom metadata.

    Example:
        >>> entry = AuditEntry(
        ...     provider="openai",
        ...     model="gpt-4",
        ...     input_hash="abc123...",
        ...     output_hash="def456...",
        ...     safety_passed=True,
        ...     detectors_triggered=[],
        ...     latency_ms=245.5,
        ... )
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this audit entry",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the interaction occurred",
    )
    provider: Optional[str] = Field(
        default=None,
        description="AI provider name (e.g., 'openai', 'anthropic')",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model identifier (e.g., 'gpt-4', 'claude-3-opus')",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional ID linking related interactions",
    )
    input_hash: str = Field(
        ...,
        description="SHA-256 hash of the input content",
    )
    output_hash: str = Field(
        ...,
        description="SHA-256 hash of the output content",
    )
    input_content: Optional[str] = Field(
        default=None,
        description="Actual input text (only if store_content enabled)",
    )
    output_content: Optional[str] = Field(
        default=None,
        description="Actual output text (only if store_content enabled)",
    )
    safety_passed: bool = Field(
        ...,
        description="Whether all safety checks passed",
    )
    detectors_triggered: List[str] = Field(
        default_factory=list,
        description="List of detector names that flagged content",
    )
    block_reason: Optional[str] = Field(
        default=None,
        description="Reason if the interaction was blocked",
    )
    alerts: List[str] = Field(
        default_factory=list,
        description="List of alert messages generated",
    )
    latency_ms: float = Field(
        ...,
        ge=0,
        description="Response time in milliseconds",
    )
    input_tokens: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of input tokens (if available)",
    )
    output_tokens: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of output tokens (if available)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata",
    )


class ComplianceProfile(BaseModel):
    """
    Configuration profile defining compliance requirements.

    This model specifies which regulatory frameworks apply, risk tolerance,
    documentation requirements, and data handling policies for an AI system.

    Attributes:
        frameworks: List of regulatory frameworks to comply with.
        risk_level: Maximum acceptable risk level.
        required_documentation: Whether comprehensive docs are required.
        data_retention_days: How long to retain audit data.
        encrypt_audit_logs: Whether to encrypt stored audit logs.
        store_content: Whether to store actual content vs just hashes.
        custom_policies: Additional custom policy configurations.

    Example:
        >>> profile = ComplianceProfile(
        ...     frameworks=[Framework.GDPR, Framework.EU_AI_ACT],
        ...     risk_level=RiskLevel.MEDIUM,
        ...     data_retention_days=365,
        ...     store_content=False,  # Privacy mode
        ... )
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
    )

    frameworks: List[Framework] = Field(
        default_factory=list,
        description="List of regulatory frameworks to comply with",
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM,
        description="Maximum acceptable risk level",
    )
    required_documentation: bool = Field(
        default=True,
        description="Whether comprehensive documentation is required",
    )
    data_retention_days: int = Field(
        default=365,
        ge=1,
        description="How long to retain audit data in days",
    )
    encrypt_audit_logs: bool = Field(
        default=True,
        description="Whether to encrypt stored audit logs",
    )
    store_content: bool = Field(
        default=False,
        description="Whether to store actual content vs just hashes",
    )
    custom_policies: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom policy configurations",
    )


class ComplianceViolation(BaseModel):
    """
    A single compliance violation detected during checking.

    This model captures details about a specific compliance rule violation,
    including the framework, severity, and recommended remediation steps.

    Attributes:
        framework: The regulatory framework that was violated.
        rule_id: Identifier of the specific rule that was violated.
        severity: How severe the violation is.
        description: Human-readable description of the violation.
        evidence: Data supporting the violation finding.
        remediation: Recommended steps to fix the violation.
        timestamp: When the violation was detected.

    Example:
        >>> violation = ComplianceViolation(
        ...     framework=Framework.GDPR,
        ...     rule_id="GDPR-ART13-1",
        ...     severity=RiskLevel.HIGH,
        ...     description="Personal data processed without consent record",
        ...     evidence={"field": "user_email", "record_id": "123"},
        ...     remediation="Implement consent tracking mechanism",
        ... )
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
    )

    framework: Framework = Field(
        ...,
        description="The regulatory framework that was violated",
    )
    rule_id: str = Field(
        ...,
        description="Identifier of the specific rule that was violated",
    )
    severity: RiskLevel = Field(
        ...,
        description="How severe the violation is",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the violation",
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data supporting the violation finding",
    )
    remediation: str = Field(
        ...,
        description="Recommended steps to fix the violation",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the violation was detected",
    )


class ComplianceCheckResult(BaseModel):
    """
    Result of a compliance check against a regulatory framework.

    This model captures the outcome of validating an AI system's operations
    against compliance requirements, including any violations found.

    Attributes:
        passed: Whether the check passed (no critical violations).
        framework: The framework that was checked against.
        violations: List of compliance violations found.
        warnings: Non-critical issues that should be addressed.
        recommendations: Suggestions for improving compliance posture.
        checked_at: When the compliance check was performed.

    Example:
        >>> result = ComplianceCheckResult(
        ...     passed=False,
        ...     framework=Framework.SOC2,
        ...     violations=[violation],
        ...     warnings=["Audit log rotation not configured"],
        ...     recommendations=["Enable encryption for audit logs"],
        ... )
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
    )

    passed: bool = Field(
        ...,
        description="Whether the check passed (no critical violations)",
    )
    framework: Framework = Field(
        ...,
        description="The framework that was checked against",
    )
    violations: List[ComplianceViolation] = Field(
        default_factory=list,
        description="List of compliance violations found",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-critical issues that should be addressed",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving compliance posture",
    )
    checked_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the compliance check was performed",
    )
