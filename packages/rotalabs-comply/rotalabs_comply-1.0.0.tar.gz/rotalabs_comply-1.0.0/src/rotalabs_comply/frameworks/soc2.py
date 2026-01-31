"""
SOC2 Type II compliance framework implementation.

SOC2 (Service Organization Control 2) is a framework developed by the American
Institute of CPAs (AICPA) for managing customer data based on five Trust Service
Criteria (TSC):

1. Security (Common Criteria - CC): Protection against unauthorized access
2. Availability (A): System availability for operation and use
3. Processing Integrity (PI): Complete, valid, accurate, timely processing
4. Confidentiality (C): Information designated as confidential is protected
5. Privacy (P): Personal information is collected, used, retained, disclosed,
   and disposed of in conformity with commitments

This framework implements Type II controls which assess operational effectiveness
over a period of time (typically 6-12 months), not just design at a point in time.

Categories:
- security: Common Criteria (CC) controls for access and security
- availability: Controls ensuring system availability
- processing_integrity: Controls ensuring data processing accuracy
- confidentiality: Controls protecting confidential information
- privacy: Controls for personal information protection

Reference: AICPA Trust Services Criteria (2017)
"""

from typing import List, Optional

from .base import (
    AuditEntry,
    BaseFramework,
    ComplianceRule,
    ComplianceViolation,
    RiskLevel,
)


class SOC2Framework(BaseFramework):
    """
    SOC2 Type II compliance framework.

    Implements compliance checks based on the AICPA Trust Service Criteria
    for SOC2 Type II reporting. This framework evaluates audit entries against
    the five trust service principles: Security, Availability, Processing
    Integrity, Confidentiality, and Privacy.

    SOC2 Type II reports assess both the design and operating effectiveness
    of controls over a specified period. This implementation focuses on
    controls relevant to AI systems and their operational characteristics.

    Trust Service Categories:
    - CC (Common Criteria): Security-related controls
    - A: Availability controls
    - PI: Processing Integrity controls
    - C: Confidentiality controls
    - P: Privacy controls

    Example:
        >>> framework = SOC2Framework()
        >>> result = await framework.check(entry, profile)
        >>> if not result.is_compliant:
        ...     for violation in result.violations:
        ...         print(f"{violation.rule_id}: {violation.description}")
    """

    def __init__(self):
        """Initialize the SOC2 Type II framework with all defined rules."""
        rules = self._create_rules()
        super().__init__(name="SOC2 Type II", version="2017", rules=rules)

    def _create_rules(self) -> List[ComplianceRule]:
        """
        Create all SOC2 Type II compliance rules.

        Returns:
            List of ComplianceRule objects representing SOC2 Trust Service Criteria
        """
        return [
            # Security (Common Criteria)
            ComplianceRule(
                rule_id="SOC2-CC6.1",
                name="Logical Access Controls",
                description=(
                    "The entity implements logical access security software, "
                    "infrastructure, and architectures over protected information "
                    "assets to protect them from security events to meet the entity's "
                    "objectives. Logical access security measures restrict access to "
                    "information resources based on the user's identity, role, or other "
                    "criteria, and are designed to permit access only to authorized users."
                ),
                severity=RiskLevel.HIGH,
                category="security",
                remediation=(
                    "Implement role-based access control (RBAC) or attribute-based "
                    "access control (ABAC). Ensure all access to AI systems and data "
                    "is authenticated and authorized. Log all access attempts."
                ),
                references=[
                    "AICPA TSC CC6.1",
                    "NIST SP 800-53 AC-2, AC-3",
                ],
            ),
            ComplianceRule(
                rule_id="SOC2-CC6.2",
                name="System Boundary Definition",
                description=(
                    "Prior to issuing system credentials and granting system access, "
                    "the entity registers and authorizes new internal and external "
                    "users whose access is administered by the entity. For those users "
                    "whose access is administered by the entity, user system credentials "
                    "are removed when user access is no longer authorized."
                ),
                severity=RiskLevel.MEDIUM,
                category="security",
                remediation=(
                    "Maintain a clear inventory of system boundaries and authorized "
                    "users. Implement user provisioning and deprovisioning processes. "
                    "Conduct regular access reviews to ensure only authorized users "
                    "have access."
                ),
                references=[
                    "AICPA TSC CC6.2",
                    "NIST SP 800-53 AC-2",
                ],
            ),
            ComplianceRule(
                rule_id="SOC2-CC6.3",
                name="Change Management",
                description=(
                    "The entity authorizes, designs, develops or acquires, configures, "
                    "documents, tests, approves, and implements changes to "
                    "infrastructure, data, software, and procedures to meet its "
                    "objectives. Changes are authorized, documented, tested, and "
                    "approved before implementation."
                ),
                severity=RiskLevel.MEDIUM,
                category="security",
                remediation=(
                    "Establish formal change management procedures for AI systems. "
                    "Document all changes to models, configurations, and infrastructure. "
                    "Require approval before production deployment. Test changes in "
                    "non-production environments first."
                ),
                references=[
                    "AICPA TSC CC6.3",
                    "NIST SP 800-53 CM-3",
                ],
            ),
            ComplianceRule(
                rule_id="SOC2-CC7.1",
                name="System Monitoring",
                description=(
                    "To meet its objectives, the entity uses detection and monitoring "
                    "procedures to identify (1) changes to configurations that result "
                    "in the introduction of new vulnerabilities, and (2) susceptibilities "
                    "to newly discovered vulnerabilities. The entity monitors system "
                    "components for anomalies and investigates identified anomalies."
                ),
                severity=RiskLevel.HIGH,
                category="security",
                remediation=(
                    "Implement comprehensive monitoring for AI systems including: "
                    "performance metrics, error rates, drift detection, and security "
                    "events. Establish alerting thresholds and response procedures. "
                    "Review logs regularly for anomalies."
                ),
                references=[
                    "AICPA TSC CC7.1",
                    "NIST SP 800-53 AU-6, SI-4",
                ],
            ),
            ComplianceRule(
                rule_id="SOC2-CC7.2",
                name="Incident Response",
                description=(
                    "The entity monitors system components and the operation of those "
                    "components for anomalies that are indicative of malicious acts, "
                    "natural disasters, and errors affecting the entity's ability to "
                    "meet its objectives; anomalies are analyzed to determine whether "
                    "they represent security events."
                ),
                severity=RiskLevel.HIGH,
                category="security",
                remediation=(
                    "Establish an incident response plan specific to AI systems. "
                    "Define procedures for detecting, analyzing, containing, eradicating, "
                    "and recovering from incidents. Include procedures for model "
                    "rollback and bias/fairness incidents."
                ),
                references=[
                    "AICPA TSC CC7.2",
                    "NIST SP 800-53 IR-4, IR-5",
                ],
            ),

            # Availability
            ComplianceRule(
                rule_id="SOC2-CC8.1",
                name="Availability Monitoring",
                description=(
                    "The entity authorizes, designs, develops or acquires, implements, "
                    "operates, approves, maintains, and monitors environmental "
                    "protections, software, data backup processes, and recovery "
                    "infrastructure to meet its objectives. System availability is "
                    "monitored against service level commitments."
                ),
                severity=RiskLevel.MEDIUM,
                category="availability",
                remediation=(
                    "Implement availability monitoring for all AI system components. "
                    "Define and monitor SLAs for inference latency, throughput, and "
                    "uptime. Establish alerting for availability degradation. "
                    "Maintain redundancy for critical components."
                ),
                references=[
                    "AICPA TSC CC8.1",
                    "NIST SP 800-53 CP-2, CP-7",
                ],
            ),
            ComplianceRule(
                rule_id="SOC2-A1.1",
                name="Recovery Objectives Defined",
                description=(
                    "The entity maintains, monitors, and evaluates current processing "
                    "capacity and use of system components (infrastructure, data, and "
                    "software) to manage capacity demand and to enable the implementation "
                    "of additional capacity to help meet its objectives. Recovery time "
                    "objectives (RTO) and recovery point objectives (RPO) are defined."
                ),
                severity=RiskLevel.MEDIUM,
                category="availability",
                remediation=(
                    "Define and document RTO and RPO for AI systems. Implement backup "
                    "procedures for models, configurations, and data. Test recovery "
                    "procedures regularly. Ensure capacity planning considers peak loads."
                ),
                references=[
                    "AICPA TSC A1.1",
                    "NIST SP 800-53 CP-9, CP-10",
                ],
            ),

            # Processing Integrity
            ComplianceRule(
                rule_id="SOC2-PI1.1",
                name="Processing Integrity Validation",
                description=(
                    "The entity implements policies and procedures over system inputs "
                    "including controls over input processes that help ensure "
                    "completeness, accuracy, timeliness, and authorization of system "
                    "inputs. Processing integrity refers to the completeness, validity, "
                    "accuracy, timeliness, and authorization of system processing."
                ),
                severity=RiskLevel.MEDIUM,
                category="processing_integrity",
                remediation=(
                    "Implement input validation for all AI system inputs. Validate "
                    "data formats, ranges, and consistency. Log all inputs with "
                    "timestamps. Implement data quality checks and monitoring for "
                    "data drift."
                ),
                references=[
                    "AICPA TSC PI1.1",
                    "NIST SP 800-53 SI-10",
                ],
            ),

            # Confidentiality
            ComplianceRule(
                rule_id="SOC2-C1.1",
                name="Confidentiality Classification",
                description=(
                    "The entity identifies and maintains confidential information to "
                    "meet the entity's objectives related to confidentiality. "
                    "Information is classified by the entity according to its "
                    "sensitivity and is protected accordingly. Confidential information "
                    "is identified based on regulatory requirements, contractual "
                    "commitments, and business needs."
                ),
                severity=RiskLevel.HIGH,
                category="confidentiality",
                remediation=(
                    "Implement data classification for all data processed by AI systems. "
                    "Label data according to sensitivity levels (public, internal, "
                    "confidential, restricted). Apply appropriate protection measures "
                    "based on classification. Document handling procedures."
                ),
                references=[
                    "AICPA TSC C1.1",
                    "NIST SP 800-53 RA-2",
                ],
            ),

            # Privacy
            ComplianceRule(
                rule_id="SOC2-P1.1",
                name="Privacy Notice Provided",
                description=(
                    "The entity provides notice to data subjects about its privacy "
                    "practices to meet the entity's objectives related to privacy. "
                    "The notice is provided to data subjects at or before the time "
                    "their personal information is collected. The notice describes "
                    "the purposes for which personal information is collected, used, "
                    "retained, and disclosed."
                ),
                severity=RiskLevel.HIGH,
                category="privacy",
                remediation=(
                    "Provide clear privacy notices before collecting personal data "
                    "for AI processing. Document how personal data is used in AI "
                    "training and inference. Implement consent mechanisms where "
                    "required. Maintain records of privacy notices provided."
                ),
                references=[
                    "AICPA TSC P1.1",
                    "GDPR Article 13",
                ],
            ),
        ]

    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single SOC2 rule against an audit entry.

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
        if rule.rule_id == "SOC2-CC6.1":
            return self._check_logical_access(entry, rule)
        elif rule.rule_id == "SOC2-CC6.2":
            return self._check_system_boundary(entry, rule)
        elif rule.rule_id == "SOC2-CC6.3":
            return self._check_change_management(entry, rule)
        elif rule.rule_id == "SOC2-CC7.1":
            return self._check_system_monitoring(entry, rule)
        elif rule.rule_id == "SOC2-CC7.2":
            return self._check_incident_response(entry, rule)
        elif rule.rule_id == "SOC2-CC8.1":
            return self._check_availability_monitoring(entry, rule)
        elif rule.rule_id == "SOC2-A1.1":
            return self._check_recovery_objectives(entry, rule)
        elif rule.rule_id == "SOC2-PI1.1":
            return self._check_processing_integrity(entry, rule)
        elif rule.rule_id == "SOC2-C1.1":
            return self._check_confidentiality_classification(entry, rule)
        elif rule.rule_id == "SOC2-P1.1":
            return self._check_privacy_notice(entry, rule)

        return None

    def _check_logical_access(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-CC6.1: Logical access controls.

        All data access and model operations should have access controls.
        """
        access_events = {
            "data_access", "model_access", "api_call", "authentication",
            "inference", "training", "data_export"
        }
        if entry.event_type.lower() not in access_events:
            return None

        # Check for access control metadata
        has_authentication = bool(entry.actor and entry.actor != "anonymous")
        has_access_control = entry.metadata.get("access_controlled", False)

        if not has_authentication:
            return self._create_violation(
                entry,
                rule,
                f"Access event (type={entry.event_type}) performed by "
                f"unauthenticated or anonymous user",
            )

        if not has_access_control:
            return self._create_violation(
                entry,
                rule,
                f"Access event (type={entry.event_type}) performed without "
                f"documented access control validation",
            )

        return None

    def _check_system_boundary(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-CC6.2: System boundary definition.

        Users should be registered and authorized before access.
        """
        # Check for external access events
        external_events = {"api_call", "external_integration", "data_import", "data_export"}
        if entry.event_type.lower() not in external_events:
            return None

        # Check that system_id is defined (system boundary is known)
        if not entry.system_id:
            return self._create_violation(
                entry,
                rule,
                f"External event (type={entry.event_type}) performed without "
                f"defined system boundary (missing system_id)",
            )

        return None

    def _check_change_management(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-CC6.3: Change management.

        Changes should be authorized, documented, and tested.
        """
        change_events = {
            "deployment", "model_update", "config_change", "training",
            "fine_tuning", "rollback"
        }
        if entry.event_type.lower() not in change_events:
            return None

        has_change_approval = entry.metadata.get("change_approved", False)
        has_change_documentation = entry.documentation_ref is not None

        if not has_change_approval:
            return self._create_violation(
                entry,
                rule,
                f"Change event (type={entry.event_type}) performed without "
                f"documented change approval",
            )

        if not has_change_documentation:
            return self._create_violation(
                entry,
                rule,
                f"Change event (type={entry.event_type}) performed without "
                f"documentation reference",
            )

        return None

    def _check_system_monitoring(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-CC7.1: System monitoring.

        System operations should be monitored for anomalies.
        """
        # All entries should have monitoring; check for monitoring metadata
        has_monitoring = entry.metadata.get("monitored", True)  # Default to true for basic entries

        # For significant operations, require explicit monitoring documentation
        significant_events = {"inference", "training", "deployment", "data_access"}
        if entry.event_type.lower() in significant_events:
            has_monitoring = entry.metadata.get("monitored", False)

            if not has_monitoring:
                return self._create_violation(
                    entry,
                    rule,
                    f"Significant operation (type={entry.event_type}) performed "
                    f"without documented monitoring",
                )

        return None

    def _check_incident_response(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-CC7.2: Incident response.

        Security events should trigger incident response procedures.
        """
        # Check for error or security events
        if entry.error_handled is False:
            has_incident_response = entry.metadata.get("incident_logged", False)

            if not has_incident_response:
                return self._create_violation(
                    entry,
                    rule,
                    f"Error event (type={entry.event_type}) occurred without "
                    f"incident response logging",
                )

        # Check for security-related events
        security_events = {"authentication_failure", "access_denied", "security_alert"}
        if entry.event_type.lower() in security_events:
            has_incident_response = entry.metadata.get("incident_logged", False)

            if not has_incident_response:
                return self._create_violation(
                    entry,
                    rule,
                    f"Security event (type={entry.event_type}) without "
                    f"incident response logging",
                )

        return None

    def _check_availability_monitoring(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-CC8.1: Availability monitoring.

        System availability should be monitored against SLAs.
        """
        availability_events = {"health_check", "deployment", "scaling", "recovery"}
        if entry.event_type.lower() not in availability_events:
            return None

        has_sla_monitoring = entry.metadata.get("sla_monitored", False)

        if not has_sla_monitoring:
            return self._create_violation(
                entry,
                rule,
                f"Availability event (type={entry.event_type}) without "
                f"documented SLA monitoring",
            )

        return None

    def _check_recovery_objectives(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-A1.1: Recovery objectives defined.

        RTO and RPO should be defined for recovery operations.
        """
        recovery_events = {"backup", "restore", "recovery", "disaster_recovery"}
        if entry.event_type.lower() not in recovery_events:
            return None

        has_rto_defined = entry.metadata.get("rto_defined", False)
        has_rpo_defined = entry.metadata.get("rpo_defined", False)

        if not has_rto_defined or not has_rpo_defined:
            return self._create_violation(
                entry,
                rule,
                f"Recovery event (type={entry.event_type}) without defined "
                f"RTO/RPO objectives (rto={has_rto_defined}, rpo={has_rpo_defined})",
            )

        return None

    def _check_processing_integrity(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-PI1.1: Processing integrity validation.

        Data processing should validate input integrity.
        """
        processing_events = {"inference", "training", "data_processing", "data_transformation"}
        if entry.event_type.lower() not in processing_events:
            return None

        has_input_validation = entry.metadata.get("input_validated", False)

        if not has_input_validation:
            return self._create_violation(
                entry,
                rule,
                f"Processing event (type={entry.event_type}) without "
                f"documented input validation",
            )

        return None

    def _check_confidentiality_classification(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-C1.1: Confidentiality classification.

        Data should be classified according to sensitivity.
        """
        data_events = {"data_access", "data_processing", "inference", "training", "data_export"}
        if entry.event_type.lower() not in data_events:
            return None

        # Check if data classification is documented
        is_classified = entry.data_classification != "unclassified"

        if not is_classified:
            return self._create_violation(
                entry,
                rule,
                f"Data event (type={entry.event_type}) with unclassified data "
                f"(classification should be specified)",
            )

        return None

    def _check_privacy_notice(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check SOC2-P1.1: Privacy notice provided.

        Personal data collection should include privacy notice.
        """
        # Check for PII-related events
        pii_classifications = {"PII", "PHI", "personal", "sensitive"}
        if entry.data_classification.upper() not in {c.upper() for c in pii_classifications}:
            return None

        has_privacy_notice = entry.metadata.get("privacy_notice_provided", False)

        if not has_privacy_notice:
            return self._create_violation(
                entry,
                rule,
                f"Personal data event (type={entry.event_type}, "
                f"classification={entry.data_classification}) without "
                f"documented privacy notice",
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
