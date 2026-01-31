"""
EU AI Act compliance framework implementation.

The EU AI Act (Regulation (EU) 2024/1689) is the European Union's comprehensive
framework for regulating artificial intelligence systems. It establishes a
risk-based approach with requirements varying by the AI system's risk level.

This framework implements checks for high-risk AI systems, which have the most
stringent requirements including:
- Human oversight and intervention capabilities
- Transparency and user notification
- Risk management systems
- Technical documentation
- Data governance
- Robustness and accuracy monitoring
- Cybersecurity measures

Categories:
- transparency: Rules ensuring users understand AI involvement
- oversight: Rules requiring human oversight capabilities
- risk_management: Rules for risk assessment and mitigation
- documentation: Rules for technical documentation
- security: Rules for cybersecurity measures

Reference: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
"""

from typing import List, Optional

from .base import (
    AuditEntry,
    BaseFramework,
    ComplianceProfile,
    ComplianceRule,
    ComplianceViolation,
    RiskLevel,
)


class EUAIActFramework(BaseFramework):
    """
    EU AI Act compliance framework.

    Implements compliance checks based on the EU AI Act (2024) requirements
    for high-risk AI systems. The framework evaluates audit entries against
    the Act's requirements for transparency, human oversight, risk management,
    documentation, and security.

    The EU AI Act classifies AI systems into risk categories:
    - Unacceptable risk: Prohibited systems
    - High-risk: Systems subject to strict requirements (this framework's focus)
    - Limited risk: Systems with transparency obligations
    - Minimal risk: Most AI systems with few requirements

    This implementation focuses on high-risk system requirements as they
    represent the most comprehensive compliance obligations.

    Example:
        >>> framework = EUAIActFramework()
        >>> result = await framework.check(entry, profile)
        >>> if not result.is_compliant:
        ...     for violation in result.violations:
        ...         print(f"{violation.rule_id}: {violation.description}")
    """

    def __init__(self):
        """Initialize the EU AI Act framework with all defined rules."""
        rules = self._create_rules()
        super().__init__(name="EU AI Act", version="2024", rules=rules)

    def _create_rules(self) -> List[ComplianceRule]:
        """
        Create all EU AI Act compliance rules.

        Returns:
            List of ComplianceRule objects representing EU AI Act requirements
        """
        return [
            ComplianceRule(
                rule_id="EUAI-001",
                name="Human Oversight Documentation",
                description=(
                    "High-risk AI systems shall be designed and developed in such a way "
                    "that they can be effectively overseen by natural persons during the "
                    "period in which they are in use. Human oversight shall aim to prevent "
                    "or minimise the risks to health, safety or fundamental rights that may "
                    "emerge when a high-risk AI system is used in accordance with its "
                    "intended purpose or under conditions of reasonably foreseeable misuse. "
                    "(Article 14)"
                ),
                severity=RiskLevel.HIGH,
                category="oversight",
                remediation=(
                    "Ensure human oversight mechanisms are in place and documented. "
                    "Implement 'human-in-the-loop', 'human-on-the-loop', or "
                    "'human-in-command' approaches as appropriate for the risk level."
                ),
                references=["EU AI Act Article 14", "Annex IV point 3"],
            ),
            ComplianceRule(
                rule_id="EUAI-002",
                name="Transparency - AI Interaction Notification",
                description=(
                    "Providers shall ensure that AI systems intended to interact directly "
                    "with natural persons are designed and developed in such a way that "
                    "the natural persons concerned are informed that they are interacting "
                    "with an AI system, unless this is obvious from the circumstances and "
                    "the context of use. (Article 50)"
                ),
                severity=RiskLevel.HIGH,
                category="transparency",
                remediation=(
                    "Implement clear notification mechanisms to inform users when they "
                    "are interacting with an AI system. This notification should be "
                    "provided before or at the start of the interaction."
                ),
                references=["EU AI Act Article 50(1)"],
            ),
            ComplianceRule(
                rule_id="EUAI-003",
                name="Risk Assessment for High-Risk Systems",
                description=(
                    "High-risk AI systems shall be subject to a risk management system "
                    "consisting of a continuous iterative process planned and run "
                    "throughout the entire lifecycle of a high-risk AI system, requiring "
                    "regular systematic updating. It shall include identification, "
                    "estimation, and evaluation of risks. (Article 9)"
                ),
                severity=RiskLevel.CRITICAL,
                category="risk_management",
                remediation=(
                    "Implement a comprehensive risk management system that identifies, "
                    "analyzes, estimates, and evaluates risks throughout the AI system's "
                    "lifecycle. Document all risk assessments and mitigation measures."
                ),
                references=["EU AI Act Article 9", "Annex IV point 2"],
            ),
            ComplianceRule(
                rule_id="EUAI-004",
                name="Technical Documentation Maintenance",
                description=(
                    "The technical documentation of a high-risk AI system shall be drawn "
                    "up before that system is placed on the market or put into service "
                    "and shall be kept up to date. Technical documentation shall contain "
                    "at minimum the elements set out in Annex IV. (Article 11)"
                ),
                severity=RiskLevel.HIGH,
                category="documentation",
                remediation=(
                    "Maintain comprehensive technical documentation including: general "
                    "description, detailed description of elements, development process, "
                    "monitoring and functioning information, and description of "
                    "appropriate human oversight measures."
                ),
                references=["EU AI Act Article 11", "Annex IV"],
            ),
            ComplianceRule(
                rule_id="EUAI-005",
                name="Data Governance - Training Data Documentation",
                description=(
                    "High-risk AI systems which make use of techniques involving the "
                    "training of AI models with data shall be developed on the basis of "
                    "training, validation and testing data sets that meet quality criteria. "
                    "Training data must be documented regarding data collection, "
                    "preparation, and assumptions. (Article 10)"
                ),
                severity=RiskLevel.HIGH,
                category="documentation",
                remediation=(
                    "Document all training, validation, and testing datasets including: "
                    "data collection processes, data preparation operations (annotation, "
                    "labeling, cleaning), relevant assumptions, prior assessment of "
                    "availability, quantity and suitability of datasets, and examination "
                    "of possible biases."
                ),
                references=["EU AI Act Article 10", "Annex IV point 2(d)"],
            ),
            ComplianceRule(
                rule_id="EUAI-006",
                name="Robustness - Error Handling",
                description=(
                    "High-risk AI systems shall be designed and developed in such a way "
                    "that they achieve an appropriate level of robustness and that they "
                    "can handle errors or inconsistencies during all lifecycle phases, "
                    "including interaction with other systems. (Article 15)"
                ),
                severity=RiskLevel.MEDIUM,
                category="risk_management",
                remediation=(
                    "Implement robust error handling mechanisms including: graceful "
                    "degradation, fallback procedures, and appropriate logging. Systems "
                    "should continue to operate safely even when errors occur."
                ),
                references=["EU AI Act Article 15(1)(2)"],
            ),
            ComplianceRule(
                rule_id="EUAI-007",
                name="Accuracy Monitoring",
                description=(
                    "High-risk AI systems shall be designed and developed in such a way "
                    "that they achieve an appropriate level of accuracy, robustness and "
                    "cybersecurity. Accuracy levels shall be specified in the accompanying "
                    "instructions of use and monitored throughout the system's lifecycle. "
                    "(Article 15)"
                ),
                severity=RiskLevel.MEDIUM,
                category="risk_management",
                remediation=(
                    "Implement accuracy monitoring systems that track system performance "
                    "over time. Document accuracy metrics in technical documentation and "
                    "instructions for use. Establish thresholds for acceptable accuracy."
                ),
                references=["EU AI Act Article 15(1)", "Annex IV point 2(g)"],
            ),
            ComplianceRule(
                rule_id="EUAI-008",
                name="Cybersecurity Measures",
                description=(
                    "High-risk AI systems shall be designed and developed in such a way "
                    "that they achieve an appropriate level of cybersecurity. The AI "
                    "system shall be resilient against attempts by unauthorized third "
                    "parties to alter its use, outputs or performance by exploiting "
                    "system vulnerabilities. (Article 15)"
                ),
                severity=RiskLevel.HIGH,
                category="security",
                remediation=(
                    "Implement comprehensive cybersecurity measures including: access "
                    "controls, input validation, adversarial robustness testing, and "
                    "regular security assessments. Document security measures in "
                    "technical documentation."
                ),
                references=["EU AI Act Article 15(4)(5)"],
            ),
        ]

    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single EU AI Act rule against an audit entry.

        Evaluates the audit entry against the specific rule requirements
        and returns a violation if the entry does not comply.

        Args:
            entry: The audit entry to check
            rule: The rule to evaluate

        Returns:
            ComplianceViolation if the rule is violated, None otherwise
        """
        # Use custom check function if provided
        if rule.check_fn is not None:
            is_compliant = rule.check_fn(entry)
            if not is_compliant:
                return self._create_violation(entry, rule, "Custom check failed")
            return None

        # Framework-specific rule checks
        if rule.rule_id == "EUAI-001":
            return self._check_human_oversight(entry, rule)
        elif rule.rule_id == "EUAI-002":
            return self._check_transparency(entry, rule)
        elif rule.rule_id == "EUAI-003":
            return self._check_risk_assessment(entry, rule)
        elif rule.rule_id == "EUAI-004":
            return self._check_technical_documentation(entry, rule)
        elif rule.rule_id == "EUAI-005":
            return self._check_data_governance(entry, rule)
        elif rule.rule_id == "EUAI-006":
            return self._check_robustness(entry, rule)
        elif rule.rule_id == "EUAI-007":
            return self._check_accuracy_monitoring(entry, rule)
        elif rule.rule_id == "EUAI-008":
            return self._check_cybersecurity(entry, rule)

        return None

    def _check_human_oversight(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-001: Human oversight documentation required for high-risk.

        High-risk AI operations must have human oversight documented.
        This is evaluated based on the risk_level and human_oversight flags.
        """
        # Only applies to high-risk operations
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        if not entry.human_oversight:
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (level={entry.risk_level.value}) performed "
                f"without documented human oversight",
            )
        return None

    def _check_transparency(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-002: Users must know they're interacting with AI.

        User-facing interactions must include AI disclosure notification.
        """
        # Check if this is a user-facing interaction
        user_facing_events = {"inference", "chat", "completion", "interaction", "response"}
        if entry.event_type.lower() not in user_facing_events:
            return None

        if not entry.user_notified:
            return self._create_violation(
                entry,
                rule,
                f"User-facing AI interaction (type={entry.event_type}) performed "
                f"without notifying user of AI involvement",
            )
        return None

    def _check_risk_assessment(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-003: Risk assessment required for high-risk systems.

        High-risk operations must have risk assessment documentation.
        """
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        # Check for risk assessment documentation in metadata
        has_risk_assessment = entry.metadata.get("risk_assessment_documented", False)
        if not has_risk_assessment:
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (level={entry.risk_level.value}) performed "
                f"without documented risk assessment",
            )
        return None

    def _check_technical_documentation(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-004: Technical documentation must be maintained.

        All operations should reference technical documentation.
        """
        # Only check for significant operations
        significant_events = {"deployment", "training", "fine_tuning", "model_update"}
        if entry.event_type.lower() not in significant_events:
            return None

        if not entry.documentation_ref:
            return self._create_violation(
                entry,
                rule,
                f"Significant operation (type={entry.event_type}) performed "
                f"without reference to technical documentation",
            )
        return None

    def _check_data_governance(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-005: Training data must be documented.

        Training-related operations must document data governance.
        """
        training_events = {"training", "fine_tuning", "data_preparation", "data_ingestion"}
        if entry.event_type.lower() not in training_events:
            return None

        has_data_governance = entry.metadata.get("data_governance_documented", False)
        if not has_data_governance:
            return self._create_violation(
                entry,
                rule,
                f"Training operation (type={entry.event_type}) performed "
                f"without documented data governance",
            )
        return None

    def _check_robustness(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-006: System must handle errors gracefully.

        Operations should demonstrate proper error handling.
        """
        if not entry.error_handled:
            return self._create_violation(
                entry,
                rule,
                f"Operation (type={entry.event_type}) indicates error was not "
                f"handled gracefully",
            )
        return None

    def _check_accuracy_monitoring(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-007: Accuracy monitoring required.

        Inference operations should include accuracy monitoring metadata.
        """
        inference_events = {"inference", "prediction", "completion"}
        if entry.event_type.lower() not in inference_events:
            return None

        has_accuracy_monitoring = entry.metadata.get("accuracy_monitored", False)
        if not has_accuracy_monitoring:
            return self._create_violation(
                entry,
                rule,
                f"Inference operation (type={entry.event_type}) performed "
                f"without accuracy monitoring",
            )
        return None

    def _check_cybersecurity(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check EUAI-008: Cybersecurity measures required.

        Check for security-related metadata on operations.
        """
        # Only check for operations that could have security implications
        security_relevant_events = {
            "inference", "data_access", "model_access", "api_call",
            "authentication", "data_export"
        }
        if entry.event_type.lower() not in security_relevant_events:
            return None

        # Check for security metadata
        has_security_check = entry.metadata.get("security_validated", False)
        has_access_control = entry.metadata.get("access_controlled", False)

        if not (has_security_check or has_access_control):
            return self._create_violation(
                entry,
                rule,
                f"Security-relevant operation (type={entry.event_type}) performed "
                f"without documented cybersecurity validation",
            )
        return None

    def _create_violation(
        self, entry: AuditEntry, rule: ComplianceRule, evidence: str
    ) -> ComplianceViolation:
        """
        Create a compliance violation object.

        Args:
            entry: The audit entry that triggered the violation
            rule: The rule that was violated
            evidence: Specific evidence describing the violation

        Returns:
            ComplianceViolation object
        """
        return ComplianceViolation(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            description=rule.description,
            evidence=evidence,
            remediation=rule.remediation,
            entry_id=entry.entry_id,
            category=rule.category,
            framework=self._name,
        )
