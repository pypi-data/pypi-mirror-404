"""
Compliance frameworks for AI system evaluation.

This module provides implementations of major compliance frameworks
for evaluating AI system behavior against regulatory requirements:

- EU AI Act: European Union's comprehensive AI regulation
- ISO/IEC 42001: International standard for AI management systems
- SOC2 Type II: AICPA Trust Service Criteria for service organizations
- HIPAA: US healthcare data protection requirements
- NIST AI RMF: NIST AI Risk Management Framework (version 1.0, January 2023)
- MAS FEAT: Monetary Authority of Singapore FEAT principles and AI governance
- GDPR: General Data Protection Regulation (EU) 2016/679

Each framework implements the ComplianceFramework protocol and can be
used to check audit entries for compliance violations.

Example:
    >>> from rotalabs_comply.frameworks import EUAIActFramework, SOC2Framework
    >>> from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile
    >>>
    >>> # Create a framework instance
    >>> eu_ai = EUAIActFramework()
    >>>
    >>> # Create an audit entry to check
    >>> entry = AuditEntry(
    ...     entry_id="test-001",
    ...     timestamp=datetime.utcnow(),
    ...     event_type="inference",
    ...     actor="user@example.com",
    ...     action="Generated text response",
    ... )
    >>>
    >>> # Create a compliance profile
    >>> profile = ComplianceProfile(
    ...     profile_id="default",
    ...     name="Default Profile",
    ... )
    >>>
    >>> # Check compliance
    >>> result = await eu_ai.check(entry, profile)
    >>> print(f"Compliant: {result.is_compliant}")
"""

from .base import (
    AuditEntry,
    BaseFramework,
    ComplianceCheckResult,
    ComplianceFramework,
    ComplianceProfile,
    ComplianceRule,
    ComplianceViolation,
    RiskLevel,
)
from .eu_ai_act import EUAIActFramework
from .gdpr import GDPRFramework
from .hipaa import HIPAAFramework
from .iso_42001 import ISO42001Framework
from .mas import MASFramework
from .nist_ai_rmf import NISTAIRMFFramework
from .soc2 import SOC2Framework

__all__ = [
    # Base types
    "RiskLevel",
    "AuditEntry",
    "ComplianceProfile",
    "ComplianceViolation",
    "ComplianceCheckResult",
    "ComplianceRule",
    "ComplianceFramework",
    "BaseFramework",
    # Frameworks
    "EUAIActFramework",
    "GDPRFramework",
    "ISO42001Framework",
    "SOC2Framework",
    "HIPAAFramework",
    "NISTAIRMFFramework",
    "MASFramework",
]
