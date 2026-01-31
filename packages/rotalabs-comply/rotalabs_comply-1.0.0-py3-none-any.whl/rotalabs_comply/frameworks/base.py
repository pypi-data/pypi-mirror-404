"""
Base compliance framework interface and types.

This module defines the core abstractions for compliance frameworks including:
- ComplianceRule: Individual compliance requirements
- ComplianceFramework: Protocol for framework implementations
- BaseFramework: Abstract base class with common functionality

Compliance frameworks check AI system behaviors against regulatory requirements
and industry standards (EU AI Act, SOC2, HIPAA, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable


class RiskLevel(Enum):
    """
    Risk severity levels for compliance violations.

    These levels indicate the urgency and potential impact of a compliance issue:
    - CRITICAL: Immediate action required, potential legal/regulatory consequences
    - HIGH: Significant risk, should be addressed within 24-48 hours
    - MEDIUM: Moderate risk, should be addressed within 1-2 weeks
    - LOW: Minor issues, can be addressed during regular review cycles
    - INFO: Informational findings, no immediate action required
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AuditEntry:
    """
    Represents a single audit log entry for an AI system interaction.

    Audit entries capture the essential metadata about AI system operations
    that compliance frameworks need to evaluate against regulatory requirements.

    Attributes:
        entry_id: Unique identifier for this audit entry
        timestamp: When the event occurred
        event_type: Type of event (e.g., "inference", "training", "data_access")
        actor: Identifier for the user, system, or agent that triggered the event
        action: Description of the action taken
        resource: The resource being accessed or modified
        metadata: Additional context-specific information about the event
        risk_level: Assessed risk level of this operation
        system_id: Identifier for the AI system involved
        data_classification: Classification of data involved (e.g., "PII", "PHI", "public")
        user_notified: Whether the user was notified about AI involvement
        human_oversight: Whether human oversight was present
        error_handled: Whether errors were handled gracefully
        documentation_ref: Reference to related technical documentation
    """
    entry_id: str
    timestamp: datetime
    event_type: str
    actor: str
    action: str
    resource: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    system_id: str = ""
    data_classification: str = "unclassified"
    user_notified: bool = False
    human_oversight: bool = False
    error_handled: bool = True
    documentation_ref: Optional[str] = None


@dataclass
class ComplianceProfile:
    """
    Configuration profile for compliance evaluation.

    Profiles define which rules to apply, severity thresholds, and
    system-specific compliance requirements.

    Attributes:
        profile_id: Unique identifier for this profile
        name: Human-readable profile name
        description: Detailed description of the profile's purpose
        enabled_frameworks: List of framework names to evaluate against
        enabled_categories: Categories of rules to check (empty = all)
        min_severity: Minimum severity level to report
        system_classification: Classification of the AI system being evaluated
        custom_rules: Additional custom rule IDs to include
        excluded_rules: Rule IDs to exclude from evaluation
        metadata: Additional profile configuration
    """
    profile_id: str
    name: str
    description: str = ""
    enabled_frameworks: List[str] = field(default_factory=list)
    enabled_categories: List[str] = field(default_factory=list)
    min_severity: RiskLevel = RiskLevel.LOW
    system_classification: str = "standard"
    custom_rules: List[str] = field(default_factory=list)
    excluded_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceViolation:
    """
    Represents a single compliance violation detected during evaluation.

    Violations are the output of rule checks that identify non-compliance
    with regulatory requirements.

    Attributes:
        rule_id: ID of the rule that was violated
        rule_name: Human-readable name of the violated rule
        severity: Severity level of the violation
        description: Detailed description of what was violated
        evidence: Specific evidence from the audit entry
        remediation: Suggested steps to remediate the violation
        entry_id: ID of the audit entry that triggered this violation
        category: Category of the violated rule
        framework: Name of the framework containing the rule
    """
    rule_id: str
    rule_name: str
    severity: RiskLevel
    description: str
    evidence: str
    remediation: str
    entry_id: str
    category: str
    framework: str


@dataclass
class ComplianceCheckResult:
    """
    Result of a compliance check against an audit entry.

    Contains all violations found, along with summary statistics
    about the compliance evaluation.

    Attributes:
        entry_id: ID of the audit entry that was checked
        framework: Name of the framework used for evaluation
        framework_version: Version of the framework
        timestamp: When the check was performed
        violations: List of all violations found
        rules_checked: Total number of rules evaluated
        rules_passed: Number of rules that passed
        is_compliant: Whether the entry is fully compliant (no violations)
        metadata: Additional check result metadata
    """
    entry_id: str
    framework: str
    framework_version: str
    timestamp: datetime
    violations: List[ComplianceViolation] = field(default_factory=list)
    rules_checked: int = 0
    rules_passed: int = 0
    is_compliant: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Update is_compliant based on violations."""
        self.is_compliant = len(self.violations) == 0


@dataclass
class ComplianceRule:
    """
    Definition of a single compliance rule within a framework.

    Rules represent specific regulatory requirements that AI systems
    must satisfy. Each rule has an associated check function that
    evaluates audit entries for compliance.

    Attributes:
        rule_id: Unique identifier for this rule within the framework
        name: Human-readable name of the rule
        description: Detailed description of the requirement
        severity: Default severity level for violations of this rule
        category: Category grouping for the rule
        check_fn: Optional custom check function for specialized validation
        remediation: Default remediation guidance for violations
        references: External references (regulation sections, standards, etc.)
    """
    rule_id: str
    name: str
    description: str
    severity: RiskLevel
    category: str
    check_fn: Optional[Callable[[AuditEntry], bool]] = None
    remediation: str = ""
    references: List[str] = field(default_factory=list)


@runtime_checkable
class ComplianceFramework(Protocol):
    """
    Protocol defining the interface for compliance frameworks.

    All compliance frameworks must implement this protocol to ensure
    consistent behavior across different regulatory standards.

    Frameworks evaluate audit entries against their rules and produce
    compliance check results with any violations found.
    """

    @property
    def name(self) -> str:
        """
        Get the name of this compliance framework.

        Returns:
            Human-readable name (e.g., "EU AI Act", "SOC2 Type II")
        """
        ...

    @property
    def version(self) -> str:
        """
        Get the version of the framework being implemented.

        Returns:
            Version string (e.g., "2024", "2017")
        """
        ...

    @property
    def rules(self) -> List[ComplianceRule]:
        """
        Get all rules defined in this framework.

        Returns:
            List of all compliance rules
        """
        ...

    async def check(
        self, entry: AuditEntry, profile: ComplianceProfile
    ) -> ComplianceCheckResult:
        """
        Check an audit entry for compliance violations.

        Evaluates the entry against all applicable rules based on
        the provided compliance profile.

        Args:
            entry: The audit entry to evaluate
            profile: Configuration profile controlling evaluation

        Returns:
            ComplianceCheckResult containing any violations found
        """
        ...

    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """
        Get a specific rule by its ID.

        Args:
            rule_id: The unique identifier of the rule

        Returns:
            The ComplianceRule if found, None otherwise
        """
        ...

    def list_categories(self) -> List[str]:
        """
        List all rule categories in this framework.

        Returns:
            List of unique category names
        """
        ...


class BaseFramework(ABC):
    """
    Abstract base class for compliance frameworks.

    Provides common functionality for all framework implementations
    including rule management, category listing, and the main check
    loop. Subclasses must implement the _check_rule method to define
    framework-specific validation logic.

    Attributes:
        _name: Framework name
        _version: Framework version
        _rules: List of rules in this framework
        _rules_by_id: Dictionary mapping rule IDs to rules for fast lookup
    """

    def __init__(self, name: str, version: str, rules: List[ComplianceRule]):
        """
        Initialize the base framework.

        Args:
            name: Human-readable framework name
            version: Framework version string
            rules: List of compliance rules
        """
        self._name = name
        self._version = version
        self._rules = rules
        self._rules_by_id: Dict[str, ComplianceRule] = {
            rule.rule_id: rule for rule in rules
        }

    @property
    def name(self) -> str:
        """Get the framework name."""
        return self._name

    @property
    def version(self) -> str:
        """Get the framework version."""
        return self._version

    @property
    def rules(self) -> List[ComplianceRule]:
        """Get all rules in this framework."""
        return self._rules

    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """
        Get a specific rule by its ID.

        Args:
            rule_id: The unique identifier of the rule

        Returns:
            The ComplianceRule if found, None otherwise
        """
        return self._rules_by_id.get(rule_id)

    def list_categories(self) -> List[str]:
        """
        List all unique rule categories in this framework.

        Returns:
            Sorted list of unique category names
        """
        categories = set(rule.category for rule in self._rules)
        return sorted(categories)

    async def check(
        self, entry: AuditEntry, profile: ComplianceProfile
    ) -> ComplianceCheckResult:
        """
        Check an audit entry for compliance violations.

        Evaluates the entry against all applicable rules based on
        the provided compliance profile, respecting category filters
        and excluded rules.

        Args:
            entry: The audit entry to evaluate
            profile: Configuration profile controlling evaluation

        Returns:
            ComplianceCheckResult containing any violations found
        """
        violations: List[ComplianceViolation] = []
        rules_checked = 0

        for rule in self._rules:
            # Skip excluded rules
            if rule.rule_id in profile.excluded_rules:
                continue

            # Filter by category if specified
            if profile.enabled_categories and rule.category not in profile.enabled_categories:
                continue

            # Filter by minimum severity
            severity_order = [
                RiskLevel.INFO,
                RiskLevel.LOW,
                RiskLevel.MEDIUM,
                RiskLevel.HIGH,
                RiskLevel.CRITICAL,
            ]
            if severity_order.index(rule.severity) < severity_order.index(profile.min_severity):
                continue

            rules_checked += 1

            # Check the rule
            violation = self._check_rule(entry, rule)
            if violation is not None:
                violations.append(violation)

        return ComplianceCheckResult(
            entry_id=entry.entry_id,
            framework=self._name,
            framework_version=self._version,
            timestamp=datetime.utcnow(),
            violations=violations,
            rules_checked=rules_checked,
            rules_passed=rules_checked - len(violations),
            is_compliant=len(violations) == 0,
        )

    @abstractmethod
    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single rule against an audit entry.

        This method must be implemented by subclasses to define
        framework-specific validation logic.

        Args:
            entry: The audit entry to check
            rule: The rule to evaluate

        Returns:
            ComplianceViolation if the rule is violated, None otherwise
        """
        ...
