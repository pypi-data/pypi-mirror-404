"""
HIPAA compliance framework implementation.

The Health Insurance Portability and Accountability Act (HIPAA) of 1996,
along with the Health Information Technology for Economic and Clinical Health
(HITECH) Act of 2009, establishes requirements for protecting sensitive patient
health information (Protected Health Information - PHI).

This framework implements the Security Rule (45 CFR 164.312) technical safeguards
and Privacy Rule (45 CFR 164.500-534) requirements relevant to AI systems that
process PHI.

Key HIPAA components implemented:
- Security Rule Technical Safeguards (164.312)
- Privacy Rule Use and Disclosure (164.502)
- De-identification Standards (164.514)
- Administrative Requirements (164.530)

Categories:
- access_control: Controls for system and data access
- audit: Audit controls and logging requirements
- integrity: Data integrity protection
- authentication: Person/entity authentication
- transmission: Transmission security requirements
- privacy: Privacy rule compliance

Reference:
- 45 CFR Part 160 (General Administrative Requirements)
- 45 CFR Part 164 (Security and Privacy)
- HHS HIPAA Security Rule Guidance
"""

from typing import List, Optional

from .base import (
    AuditEntry,
    BaseFramework,
    ComplianceRule,
    ComplianceViolation,
    RiskLevel,
)


class HIPAAFramework(BaseFramework):
    """
    HIPAA compliance framework.

    Implements compliance checks based on HIPAA Security Rule technical
    safeguards and Privacy Rule requirements. This framework evaluates
    audit entries for AI systems that process Protected Health Information
    (PHI) or electronic PHI (ePHI).

    HIPAA requires covered entities and business associates to:
    - Ensure confidentiality, integrity, and availability of ePHI
    - Protect against anticipated threats and hazards
    - Protect against unauthorized uses or disclosures
    - Ensure workforce compliance

    This implementation focuses on technical safeguards (164.312) which
    are most relevant to AI system operations:
    - Access controls (164.312(a))
    - Audit controls (164.312(b))
    - Integrity controls (164.312(c))
    - Authentication (164.312(d))
    - Transmission security (164.312(e))

    Example:
        >>> framework = HIPAAFramework()
        >>> result = await framework.check(entry, profile)
        >>> if not result.is_compliant:
        ...     for violation in result.violations:
        ...         print(f"{violation.rule_id}: {violation.description}")
    """

    # PHI-related data classifications
    PHI_CLASSIFICATIONS = {
        "PHI", "ePHI", "protected_health_information",
        "health_data", "medical", "clinical"
    }

    def __init__(self):
        """Initialize the HIPAA framework with all defined rules."""
        rules = self._create_rules()
        super().__init__(name="HIPAA", version="1996/2013", rules=rules)

    def _create_rules(self) -> List[ComplianceRule]:
        """
        Create all HIPAA compliance rules.

        Returns:
            List of ComplianceRule objects representing HIPAA requirements
        """
        return [
            # Security Rule - Technical Safeguards
            ComplianceRule(
                rule_id="HIPAA-164.312(a)",
                name="Access Control",
                description=(
                    "Implement technical policies and procedures for electronic "
                    "information systems that maintain electronic protected health "
                    "information to allow access only to those persons or software "
                    "programs that have been granted access rights as specified in "
                    "164.308(a)(4). This includes: unique user identification, "
                    "emergency access procedures, automatic logoff, and encryption "
                    "and decryption mechanisms."
                ),
                severity=RiskLevel.CRITICAL,
                category="access_control",
                remediation=(
                    "Implement comprehensive access controls including: unique user "
                    "IDs for all users accessing ePHI, role-based access policies, "
                    "automatic session timeouts, emergency access procedures, and "
                    "encryption for ePHI at rest. Document all access control "
                    "policies and procedures."
                ),
                references=[
                    "45 CFR 164.312(a)(1)",
                    "45 CFR 164.312(a)(2)(i-iv)",
                ],
            ),
            ComplianceRule(
                rule_id="HIPAA-164.312(b)",
                name="Audit Controls",
                description=(
                    "Implement hardware, software, and/or procedural mechanisms that "
                    "record and examine activity in information systems that contain "
                    "or use electronic protected health information. Audit controls "
                    "must capture sufficient information to support review of system "
                    "activity, including who accessed what data and when."
                ),
                severity=RiskLevel.HIGH,
                category="audit",
                remediation=(
                    "Implement comprehensive audit logging for all systems containing "
                    "ePHI. Logs should capture: user identification, timestamp, type "
                    "of access, data accessed, and success/failure status. Implement "
                    "log retention policies and regular log review procedures."
                ),
                references=[
                    "45 CFR 164.312(b)",
                ],
            ),
            ComplianceRule(
                rule_id="HIPAA-164.312(c)",
                name="Integrity Controls",
                description=(
                    "Implement policies and procedures to protect electronic protected "
                    "health information from improper alteration or destruction. "
                    "Implement electronic mechanisms to corroborate that electronic "
                    "protected health information has not been altered or destroyed "
                    "in an unauthorized manner."
                ),
                severity=RiskLevel.HIGH,
                category="integrity",
                remediation=(
                    "Implement integrity controls including: checksums or digital "
                    "signatures for ePHI, change detection mechanisms, version "
                    "control for data modifications, and procedures for detecting "
                    "unauthorized changes. Document all integrity verification "
                    "procedures."
                ),
                references=[
                    "45 CFR 164.312(c)(1)",
                    "45 CFR 164.312(c)(2)",
                ],
            ),
            ComplianceRule(
                rule_id="HIPAA-164.312(d)",
                name="Person or Entity Authentication",
                description=(
                    "Implement procedures to verify that a person or entity seeking "
                    "access to electronic protected health information is the one "
                    "claimed. Authentication mechanisms should be appropriate for "
                    "the risk level of the systems and data being accessed."
                ),
                severity=RiskLevel.CRITICAL,
                category="authentication",
                remediation=(
                    "Implement strong authentication mechanisms for all ePHI access. "
                    "Consider multi-factor authentication for high-risk access. "
                    "Implement password policies meeting industry standards. "
                    "Document authentication procedures and verify identity before "
                    "granting access credentials."
                ),
                references=[
                    "45 CFR 164.312(d)",
                ],
            ),
            ComplianceRule(
                rule_id="HIPAA-164.312(e)",
                name="Transmission Security",
                description=(
                    "Implement technical security measures to guard against "
                    "unauthorized access to electronic protected health information "
                    "that is being transmitted over an electronic communications "
                    "network. This includes integrity controls and encryption for "
                    "data in transit."
                ),
                severity=RiskLevel.HIGH,
                category="transmission",
                remediation=(
                    "Implement encryption for all ePHI transmitted over networks "
                    "(TLS 1.2+ recommended). Use secure protocols for data transfer. "
                    "Implement integrity verification for transmitted data. "
                    "Document transmission security policies and procedures."
                ),
                references=[
                    "45 CFR 164.312(e)(1)",
                    "45 CFR 164.312(e)(2)(i-ii)",
                ],
            ),

            # Privacy Rule
            ComplianceRule(
                rule_id="HIPAA-164.502",
                name="Uses and Disclosures",
                description=(
                    "A covered entity or business associate may not use or disclose "
                    "protected health information, except as permitted or required. "
                    "The minimum necessary standard requires limiting PHI use, "
                    "disclosure, and requests to the minimum necessary to accomplish "
                    "the intended purpose. AI systems must respect these limitations."
                ),
                severity=RiskLevel.CRITICAL,
                category="privacy",
                remediation=(
                    "Implement minimum necessary controls for PHI access by AI "
                    "systems. Document the purpose for each PHI access. Limit data "
                    "exposure to only what is required for the specific use case. "
                    "Implement data masking or filtering where possible. Maintain "
                    "records of all PHI disclosures."
                ),
                references=[
                    "45 CFR 164.502",
                    "45 CFR 164.514(d)",
                ],
            ),
            ComplianceRule(
                rule_id="HIPAA-164.514",
                name="De-identification Standards",
                description=(
                    "Health information that does not identify an individual and "
                    "with respect to which there is no reasonable basis to believe "
                    "that the information can be used to identify an individual is "
                    "not individually identifiable health information. De-identification "
                    "may be achieved through expert determination or safe harbor methods."
                ),
                severity=RiskLevel.HIGH,
                category="privacy",
                remediation=(
                    "When using health data for AI training or analytics, implement "
                    "de-identification following HIPAA Safe Harbor (remove 18 "
                    "identifiers) or Expert Determination methods. Document "
                    "de-identification procedures and maintain records of "
                    "de-identification status for all datasets."
                ),
                references=[
                    "45 CFR 164.514(a)",
                    "45 CFR 164.514(b)",
                ],
            ),
            ComplianceRule(
                rule_id="HIPAA-164.530",
                name="Administrative Requirements",
                description=(
                    "A covered entity must maintain, until six years after the later "
                    "of the date of their creation or last effective date, its "
                    "privacy policies and procedures, its privacy practices notices, "
                    "disposition of complaints, and other actions, activities, and "
                    "designations that the Privacy Rule requires to be documented."
                ),
                severity=RiskLevel.MEDIUM,
                category="privacy",
                remediation=(
                    "Maintain comprehensive documentation of all privacy policies, "
                    "procedures, and practices related to AI systems processing PHI. "
                    "Retain all documentation for at least six years. Implement "
                    "procedures for responding to individual rights requests "
                    "(access, amendment, accounting of disclosures)."
                ),
                references=[
                    "45 CFR 164.530(j)",
                ],
            ),
        ]

    def _is_phi_related(self, entry: AuditEntry) -> bool:
        """
        Determine if an audit entry involves PHI.

        Args:
            entry: The audit entry to check

        Returns:
            True if the entry involves PHI, False otherwise
        """
        classification_upper = entry.data_classification.upper()
        return any(
            phi.upper() in classification_upper
            for phi in self.PHI_CLASSIFICATIONS
        )

    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single HIPAA rule against an audit entry.

        HIPAA rules are only evaluated for entries involving PHI.
        Non-PHI entries are automatically compliant.

        Args:
            entry: The audit entry to check
            rule: The rule to evaluate

        Returns:
            ComplianceViolation if the rule is violated, None otherwise
        """
        # HIPAA rules only apply to PHI-related entries
        if not self._is_phi_related(entry):
            return None

        # Use custom check function if provided
        if rule.check_fn is not None:
            is_compliant = rule.check_fn(entry)
            if not is_compliant:
                return self._create_violation(entry, rule, "Custom check failed")
            return None

        # Framework-specific rule checks
        if rule.rule_id == "HIPAA-164.312(a)":
            return self._check_access_control(entry, rule)
        elif rule.rule_id == "HIPAA-164.312(b)":
            return self._check_audit_controls(entry, rule)
        elif rule.rule_id == "HIPAA-164.312(c)":
            return self._check_integrity_controls(entry, rule)
        elif rule.rule_id == "HIPAA-164.312(d)":
            return self._check_authentication(entry, rule)
        elif rule.rule_id == "HIPAA-164.312(e)":
            return self._check_transmission_security(entry, rule)
        elif rule.rule_id == "HIPAA-164.502":
            return self._check_uses_and_disclosures(entry, rule)
        elif rule.rule_id == "HIPAA-164.514":
            return self._check_deidentification(entry, rule)
        elif rule.rule_id == "HIPAA-164.530":
            return self._check_administrative_requirements(entry, rule)

        return None

    def _check_access_control(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.312(a): Access control required.

        PHI access must have proper access controls including unique user ID,
        authorization validation, and encryption.
        """
        # Check for unique user identification
        has_unique_user = bool(entry.actor and entry.actor != "anonymous")
        if not has_unique_user:
            return self._create_violation(
                entry,
                rule,
                f"PHI access (type={entry.event_type}) performed without "
                f"unique user identification (actor={entry.actor})",
            )

        # Check for access control validation
        has_access_control = entry.metadata.get("access_controlled", False)
        if not has_access_control:
            return self._create_violation(
                entry,
                rule,
                f"PHI access (type={entry.event_type}) without documented "
                f"access control validation",
            )

        # For data access, check for encryption
        data_events = {"data_access", "data_export", "inference"}
        if entry.event_type.lower() in data_events:
            has_encryption = entry.metadata.get("encryption_enabled", False)
            if not has_encryption:
                return self._create_violation(
                    entry,
                    rule,
                    f"PHI data access (type={entry.event_type}) without "
                    f"encryption enabled",
                )

        return None

    def _check_audit_controls(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.312(b): Audit controls required.

        All PHI access must be logged with sufficient detail.
        """
        # Check that entry has required audit fields
        required_fields = [
            ("entry_id", entry.entry_id),
            ("timestamp", entry.timestamp),
            ("actor", entry.actor),
            ("event_type", entry.event_type),
            ("action", entry.action),
        ]

        missing_fields = [
            field_name for field_name, field_value in required_fields
            if not field_value
        ]

        if missing_fields:
            return self._create_violation(
                entry,
                rule,
                f"PHI event missing required audit fields: {', '.join(missing_fields)}",
            )

        # Check for audit logging confirmation
        has_audit_logged = entry.metadata.get("audit_logged", True)  # Assume logged if entry exists
        if not has_audit_logged:
            return self._create_violation(
                entry,
                rule,
                f"PHI event (type={entry.event_type}) without confirmation "
                f"of audit logging",
            )

        return None

    def _check_integrity_controls(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.312(c): Integrity controls.

        PHI modifications must have integrity verification.
        """
        modification_events = {
            "update", "modify", "write", "training", "data_transformation",
            "data_processing"
        }
        if entry.event_type.lower() not in modification_events:
            return None

        has_integrity_check = entry.metadata.get("integrity_verified", False)
        if not has_integrity_check:
            return self._create_violation(
                entry,
                rule,
                f"PHI modification (type={entry.event_type}) without "
                f"integrity verification controls",
            )

        return None

    def _check_authentication(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.312(d): Person authentication.

        PHI access requires verified authentication.
        """
        # Must have authenticated user
        if not entry.actor or entry.actor == "anonymous":
            return self._create_violation(
                entry,
                rule,
                f"PHI access (type={entry.event_type}) without authenticated "
                f"user identification",
            )

        # Check for authentication verification
        has_authentication = entry.metadata.get("authenticated", False)
        if not has_authentication:
            return self._create_violation(
                entry,
                rule,
                f"PHI access (type={entry.event_type}) without documented "
                f"authentication verification",
            )

        # For high-risk operations, check for strong authentication
        high_risk_events = {"data_export", "bulk_access", "admin_access"}
        if entry.event_type.lower() in high_risk_events:
            has_mfa = entry.metadata.get("mfa_verified", False)
            if not has_mfa:
                return self._create_violation(
                    entry,
                    rule,
                    f"High-risk PHI operation (type={entry.event_type}) without "
                    f"multi-factor authentication",
                )

        return None

    def _check_transmission_security(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.312(e): Transmission security.

        PHI transmission must be encrypted and secured.
        """
        transmission_events = {
            "data_transfer", "data_export", "api_call", "external_integration",
            "inference"  # May involve PHI transmission
        }
        if entry.event_type.lower() not in transmission_events:
            return None

        has_encryption = entry.metadata.get("transmission_encrypted", False)
        if not has_encryption:
            return self._create_violation(
                entry,
                rule,
                f"PHI transmission (type={entry.event_type}) without "
                f"documented encryption",
            )

        # Check for secure protocol
        protocol = entry.metadata.get("protocol", "")
        insecure_protocols = {"http", "ftp", "telnet"}
        if protocol.lower() in insecure_protocols:
            return self._create_violation(
                entry,
                rule,
                f"PHI transmission (type={entry.event_type}) using insecure "
                f"protocol ({protocol})",
            )

        return None

    def _check_uses_and_disclosures(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.502: Uses and disclosures.

        PHI use must be limited to minimum necessary and properly authorized.
        """
        # Check for documented purpose
        has_purpose = entry.metadata.get("purpose_documented", False)
        if not has_purpose:
            return self._create_violation(
                entry,
                rule,
                f"PHI use (type={entry.event_type}) without documented "
                f"purpose for access",
            )

        # Check for minimum necessary compliance
        has_minimum_necessary = entry.metadata.get("minimum_necessary_applied", False)
        if not has_minimum_necessary:
            return self._create_violation(
                entry,
                rule,
                f"PHI use (type={entry.event_type}) without minimum necessary "
                f"standard applied",
            )

        # For disclosures, check for authorization
        disclosure_events = {"data_export", "data_share", "external_integration"}
        if entry.event_type.lower() in disclosure_events:
            has_authorization = entry.metadata.get("disclosure_authorized", False)
            if not has_authorization:
                return self._create_violation(
                    entry,
                    rule,
                    f"PHI disclosure (type={entry.event_type}) without "
                    f"documented authorization",
                )

        return None

    def _check_deidentification(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.514: De-identification standards.

        Training and analytics should use de-identified data where possible.
        """
        # Check events where de-identification is typically required
        deidentification_events = {"training", "analytics", "research", "data_aggregation"}
        if entry.event_type.lower() not in deidentification_events:
            return None

        # Check if de-identification was applied
        is_deidentified = entry.metadata.get("deidentified", False)
        has_deidentification_exception = entry.metadata.get(
            "deidentification_exception_documented", False
        )

        if not is_deidentified and not has_deidentification_exception:
            return self._create_violation(
                entry,
                rule,
                f"PHI used for {entry.event_type} without de-identification "
                f"or documented exception",
            )

        return None

    def _check_administrative_requirements(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check HIPAA-164.530: Administrative requirements.

        PHI operations should reference documentation and policies.
        """
        # Check for policy compliance documentation
        has_policy_ref = entry.documentation_ref is not None
        has_policy_compliance = entry.metadata.get("policy_compliant", False)

        if not has_policy_ref and not has_policy_compliance:
            return self._create_violation(
                entry,
                rule,
                f"PHI operation (type={entry.event_type}) without reference "
                f"to privacy policies or documented compliance",
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
