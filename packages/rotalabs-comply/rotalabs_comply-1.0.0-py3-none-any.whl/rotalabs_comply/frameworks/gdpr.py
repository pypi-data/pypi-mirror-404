"""
GDPR (General Data Protection Regulation) compliance framework implementation.

The General Data Protection Regulation (EU) 2016/679 is the European Union's
comprehensive data protection law that governs the processing of personal data
of individuals within the EU. It establishes strict requirements for organizations
that collect, store, or process personal data.

This framework implements checks for AI systems processing personal data, covering:
- Data processing principles (lawfulness, fairness, transparency)
- Legal basis requirements
- Consent conditions
- Transparency and disclosure obligations
- Data subject rights (access, erasure, portability)
- Automated decision-making restrictions
- Privacy by design requirements
- Security and accountability measures

Categories:
- data_protection: Rules for core data protection principles
- legal_basis: Rules for lawful processing requirements
- consent: Rules for valid consent conditions
- transparency: Rules for information provision and communication
- data_subject_rights: Rules for individual rights
- security: Rules for data security measures
- accountability: Rules for demonstrating compliance

Reference: https://eur-lex.europa.eu/eli/reg/2016/679/oj
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


class GDPRFramework(BaseFramework):
    """
    GDPR compliance framework.

    Implements compliance checks based on the General Data Protection Regulation
    (GDPR) requirements for processing personal data. The framework evaluates
    audit entries against the Regulation's requirements for data protection,
    consent, transparency, data subject rights, security, and accountability.

    The GDPR applies to:
    - Organizations established in the EU processing personal data
    - Organizations outside the EU offering goods/services to EU residents
    - Organizations monitoring behavior of individuals in the EU

    Key principles enforced:
    - Lawfulness, fairness, and transparency
    - Purpose limitation
    - Data minimization
    - Accuracy
    - Storage limitation
    - Integrity and confidentiality
    - Accountability

    Example:
        >>> framework = GDPRFramework()
        >>> result = await framework.check(entry, profile)
        >>> if not result.is_compliant:
        ...     for violation in result.violations:
        ...         print(f"{violation.rule_id}: {violation.description}")
    """

    def __init__(self):
        """Initialize the GDPR framework with all defined rules."""
        rules = self._create_rules()
        super().__init__(name="GDPR", version="2016/679", rules=rules)

    def _create_rules(self) -> List[ComplianceRule]:
        """
        Create all GDPR compliance rules.

        Returns:
            List of ComplianceRule objects representing GDPR requirements
        """
        return [
            ComplianceRule(
                rule_id="GDPR-Art5",
                name="Data Processing Principles",
                description=(
                    "Personal data shall be processed lawfully, fairly and in a transparent "
                    "manner in relation to the data subject ('lawfulness, fairness and "
                    "transparency'). Data must be collected for specified, explicit and "
                    "legitimate purposes and not further processed in a manner incompatible "
                    "with those purposes. Data shall be adequate, relevant and limited to "
                    "what is necessary ('data minimisation'), accurate and kept up to date, "
                    "kept for no longer than necessary ('storage limitation'), and processed "
                    "in a manner that ensures appropriate security ('integrity and "
                    "confidentiality'). The controller shall be responsible for, and be able "
                    "to demonstrate compliance with these principles ('accountability'). "
                    "(Article 5)"
                ),
                severity=RiskLevel.CRITICAL,
                category="data_protection",
                remediation=(
                    "Ensure all personal data processing adheres to GDPR principles: "
                    "1) Document the lawful basis for processing, 2) Limit data collection "
                    "to what is necessary, 3) Implement data accuracy checks, 4) Define "
                    "retention periods, 5) Apply appropriate security measures, and "
                    "6) Maintain records demonstrating compliance."
                ),
                references=["GDPR Article 5(1)(2)", "Recitals 39-47"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art6",
                name="Lawful Basis for Processing",
                description=(
                    "Processing shall be lawful only if and to the extent that at least one "
                    "of the following applies: (a) consent, (b) contract necessity, "
                    "(c) legal obligation, (d) vital interests, (e) public interest or "
                    "official authority, or (f) legitimate interests (except where "
                    "overridden by data subject's interests or fundamental rights). Each "
                    "processing activity must have a documented legal basis before "
                    "processing begins. (Article 6)"
                ),
                severity=RiskLevel.CRITICAL,
                category="legal_basis",
                remediation=(
                    "Identify and document the appropriate lawful basis for each processing "
                    "activity before processing begins. For consent, ensure it meets GDPR "
                    "requirements. For legitimate interests, conduct a balancing test. "
                    "Record the lawful basis in your processing records and privacy notices."
                ),
                references=["GDPR Article 6(1)", "Recitals 40-50"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art7",
                name="Conditions for Consent",
                description=(
                    "Where processing is based on consent, the controller shall be able to "
                    "demonstrate that the data subject has consented to processing. Consent "
                    "must be freely given, specific, informed and unambiguous. The request "
                    "for consent shall be presented in a manner clearly distinguishable from "
                    "other matters, in an intelligible and easily accessible form, using "
                    "clear and plain language. The data subject shall have the right to "
                    "withdraw consent at any time, and withdrawal must be as easy as giving "
                    "consent. (Article 7)"
                ),
                severity=RiskLevel.HIGH,
                category="consent",
                remediation=(
                    "Implement consent mechanisms that: 1) Require affirmative action "
                    "(no pre-ticked boxes), 2) Are specific to each processing purpose, "
                    "3) Provide clear information about data use, 4) Are separate from "
                    "other terms, 5) Allow easy withdrawal, and 6) Maintain consent records. "
                    "Regularly review and refresh consent where appropriate."
                ),
                references=["GDPR Article 7(1-4)", "Recitals 32, 42, 43"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art12",
                name="Transparent Information and Communication",
                description=(
                    "The controller shall take appropriate measures to provide any "
                    "information referred to in Articles 13 and 14 and any communication "
                    "under Articles 15 to 22 relating to processing to the data subject "
                    "in a concise, transparent, intelligible and easily accessible form, "
                    "using clear and plain language. Information shall be provided in "
                    "writing, or by other means including electronic means. The controller "
                    "shall facilitate the exercise of data subject rights. (Article 12)"
                ),
                severity=RiskLevel.HIGH,
                category="transparency",
                remediation=(
                    "Develop clear, accessible privacy notices using plain language. "
                    "Provide information through multiple channels (website, app, paper). "
                    "Establish procedures to respond to data subject requests within one "
                    "month. Train staff on handling requests. Use layered approaches for "
                    "complex information. Test readability of notices."
                ),
                references=["GDPR Article 12(1-6)", "Recitals 58-59"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art13",
                name="Information at Collection",
                description=(
                    "Where personal data are collected from the data subject, the controller "
                    "shall, at the time when personal data are obtained, provide the data "
                    "subject with: controller identity and contact details, DPO contact "
                    "details, purposes and legal basis for processing, legitimate interests "
                    "pursued, recipients or categories of recipients, intention to transfer "
                    "data to third countries, retention period, data subject rights, right "
                    "to withdraw consent, right to lodge complaint, whether provision is "
                    "statutory/contractual requirement, and existence of automated "
                    "decision-making including profiling. (Article 13)"
                ),
                severity=RiskLevel.HIGH,
                category="transparency",
                remediation=(
                    "Create comprehensive privacy notices that include all required "
                    "information under Article 13. Provide this information at the point "
                    "of data collection. For AI systems, clearly explain any automated "
                    "decision-making, profiling, and the logic involved. Update notices "
                    "when processing changes."
                ),
                references=["GDPR Article 13(1-3)", "Recitals 60-62"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art15",
                name="Right of Access",
                description=(
                    "The data subject shall have the right to obtain from the controller "
                    "confirmation as to whether or not personal data concerning him or her "
                    "are being processed, and, where that is the case, access to the personal "
                    "data and information including: purposes of processing, categories of "
                    "data, recipients, retention period, existence of rights (rectification, "
                    "erasure, restriction, objection), right to lodge complaint, source of "
                    "data, and existence of automated decision-making. The controller shall "
                    "provide a copy of the personal data undergoing processing. (Article 15)"
                ),
                severity=RiskLevel.HIGH,
                category="data_subject_rights",
                remediation=(
                    "Implement systems to: 1) Verify data subject identity, 2) Search and "
                    "retrieve all personal data across systems, 3) Generate comprehensive "
                    "response within one month, 4) Provide data in commonly used electronic "
                    "format, 5) Include all supplementary information required. Establish "
                    "processes for handling complex or repeated requests."
                ),
                references=["GDPR Article 15(1-4)", "Recitals 63-64"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art17",
                name="Right to Erasure (Right to be Forgotten)",
                description=(
                    "The data subject shall have the right to obtain from the controller the "
                    "erasure of personal data without undue delay where: data no longer "
                    "necessary for original purposes, consent withdrawn, data subject objects "
                    "and no overriding legitimate grounds, data unlawfully processed, legal "
                    "obligation requires erasure, or data collected in relation to offer of "
                    "information society services to a child. Where data has been made public, "
                    "the controller must take reasonable steps to inform other controllers "
                    "processing the data. Exceptions apply for legal claims, legal obligations, "
                    "public health, archiving, and research. (Article 17)"
                ),
                severity=RiskLevel.HIGH,
                category="data_subject_rights",
                remediation=(
                    "Implement erasure capabilities that: 1) Can identify all instances of "
                    "personal data, 2) Securely delete data from all systems including backups, "
                    "3) Notify third parties who received the data, 4) Document the erasure "
                    "process, and 5) Respond within one month. For AI systems, consider "
                    "whether data in training sets can be removed or models retrained."
                ),
                references=["GDPR Article 17(1-3)", "Recitals 65-66"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art20",
                name="Right to Data Portability",
                description=(
                    "The data subject shall have the right to receive personal data concerning "
                    "him or her, which he or she has provided to a controller, in a structured, "
                    "commonly used and machine-readable format and have the right to transmit "
                    "those data to another controller without hindrance where: processing is "
                    "based on consent or contract, and processing is carried out by automated "
                    "means. The data subject shall have the right to have data transmitted "
                    "directly from one controller to another, where technically feasible. "
                    "(Article 20)"
                ),
                severity=RiskLevel.MEDIUM,
                category="data_subject_rights",
                remediation=(
                    "Implement data export functionality that: 1) Provides data in structured, "
                    "machine-readable formats (JSON, CSV, XML), 2) Includes all data provided "
                    "by the data subject, 3) Allows direct transmission to other controllers "
                    "where feasible, 4) Responds within one month. Distinguish between data "
                    "'provided' by the subject and data 'derived' through processing."
                ),
                references=["GDPR Article 20(1-4)", "Recital 68"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art22",
                name="Automated Decision-Making and Profiling",
                description=(
                    "The data subject shall have the right not to be subject to a decision "
                    "based solely on automated processing, including profiling, which produces "
                    "legal effects concerning him or her or similarly significantly affects "
                    "him or her. This does not apply if the decision: is necessary for a "
                    "contract, is authorised by law, or is based on explicit consent. In "
                    "those cases, the controller shall implement suitable measures to safeguard "
                    "the data subject's rights and freedoms and legitimate interests, at least "
                    "the right to obtain human intervention, to express his or her point of "
                    "view and to contest the decision. (Article 22)"
                ),
                severity=RiskLevel.CRITICAL,
                category="data_subject_rights",
                remediation=(
                    "For AI systems making automated decisions: 1) Implement human review "
                    "mechanisms for decisions with legal or significant effects, 2) Provide "
                    "meaningful information about the logic involved, 3) Allow data subjects "
                    "to express their views and contest decisions, 4) Conduct DPIAs for "
                    "profiling activities, and 5) Document the necessity and safeguards. "
                    "Consider whether purely automated decisions can be avoided."
                ),
                references=["GDPR Article 22(1-4)", "Recitals 71-72"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art25",
                name="Data Protection by Design and Default",
                description=(
                    "The controller shall, both at the time of the determination of the means "
                    "for processing and at the time of the processing itself, implement "
                    "appropriate technical and organisational measures designed to implement "
                    "data-protection principles (such as data minimisation) in an effective "
                    "manner and to integrate the necessary safeguards into the processing. "
                    "The controller shall implement appropriate measures for ensuring that, "
                    "by default, only personal data which are necessary for each specific "
                    "purpose of the processing are processed. (Article 25)"
                ),
                severity=RiskLevel.HIGH,
                category="accountability",
                remediation=(
                    "Embed privacy into system design from the outset: 1) Conduct privacy "
                    "impact assessments during development, 2) Implement data minimisation "
                    "by default, 3) Use pseudonymisation and encryption, 4) Build in consent "
                    "mechanisms, 5) Design for data subject rights, 6) Limit access by default, "
                    "7) Document design decisions. Review and update as technology evolves."
                ),
                references=["GDPR Article 25(1-3)", "Recitals 78"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art30",
                name="Records of Processing Activities",
                description=(
                    "Each controller shall maintain a record of processing activities under "
                    "its responsibility. That record shall contain: name and contact details "
                    "of controller and DPO, purposes of processing, description of categories "
                    "of data subjects and personal data, categories of recipients, transfers "
                    "to third countries, retention periods, and description of technical and "
                    "organisational security measures. These records shall be in writing, "
                    "including electronic form, and made available to the supervisory "
                    "authority on request. (Article 30)"
                ),
                severity=RiskLevel.HIGH,
                category="accountability",
                remediation=(
                    "Create and maintain comprehensive records of all processing activities "
                    "(ROPA) that include all required elements. Review and update records "
                    "regularly. Ensure records cover all systems including AI/ML systems. "
                    "Use a consistent format that can be provided to supervisory authorities. "
                    "Train staff responsible for maintaining records."
                ),
                references=["GDPR Article 30(1-5)", "Recital 82"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art32",
                name="Security of Processing",
                description=(
                    "The controller and processor shall implement appropriate technical and "
                    "organisational measures to ensure a level of security appropriate to the "
                    "risk, including as appropriate: (a) pseudonymisation and encryption of "
                    "personal data, (b) ability to ensure ongoing confidentiality, integrity, "
                    "availability and resilience of systems, (c) ability to restore "
                    "availability and access to data in timely manner following an incident, "
                    "(d) process for regularly testing, assessing and evaluating effectiveness "
                    "of measures. The controller and processor shall take steps to ensure any "
                    "person acting under their authority with access to personal data processes "
                    "only on instructions. (Article 32)"
                ),
                severity=RiskLevel.CRITICAL,
                category="security",
                remediation=(
                    "Implement security measures appropriate to the risk: 1) Encrypt personal "
                    "data in transit and at rest, 2) Implement access controls and "
                    "authentication, 3) Maintain backup and recovery procedures, 4) Conduct "
                    "regular security testing and audits, 5) Train personnel on security "
                    "procedures, 6) Document security measures. For AI systems, also consider "
                    "model security and adversarial robustness."
                ),
                references=["GDPR Article 32(1-4)", "Recitals 83"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art33",
                name="Personal Data Breach Notification",
                description=(
                    "In the case of a personal data breach, the controller shall without "
                    "undue delay and, where feasible, not later than 72 hours after having "
                    "become aware of it, notify the personal data breach to the supervisory "
                    "authority, unless the breach is unlikely to result in a risk to rights "
                    "and freedoms. Where notification is not made within 72 hours, it shall "
                    "be accompanied by reasons for the delay. The notification shall describe: "
                    "nature of breach including categories and approximate numbers of data "
                    "subjects and records, DPO contact details, likely consequences, and "
                    "measures taken or proposed to address the breach. (Article 33)"
                ),
                severity=RiskLevel.CRITICAL,
                category="security",
                remediation=(
                    "Establish breach detection and response procedures: 1) Implement "
                    "monitoring to detect breaches quickly, 2) Create incident response plan "
                    "with clear escalation paths, 3) Prepare notification templates, "
                    "4) Document all breaches in a breach register, 5) Conduct post-incident "
                    "reviews, 6) Train staff on breach identification and reporting. "
                    "Ensure 72-hour notification capability is tested."
                ),
                references=["GDPR Article 33(1-5)", "Recitals 85-88"],
            ),
            ComplianceRule(
                rule_id="GDPR-Art35",
                name="Data Protection Impact Assessment",
                description=(
                    "Where a type of processing, in particular using new technologies, and "
                    "taking into account the nature, scope, context and purposes of the "
                    "processing, is likely to result in a high risk to the rights and freedoms "
                    "of natural persons, the controller shall, prior to the processing, carry "
                    "out an assessment of the impact of the envisaged processing operations "
                    "on the protection of personal data. A DPIA is required in particular for: "
                    "(a) systematic and extensive evaluation of personal aspects based on "
                    "automated processing, including profiling, (b) large scale processing of "
                    "special categories of data or criminal convictions data, (c) systematic "
                    "monitoring of a publicly accessible area on a large scale. (Article 35)"
                ),
                severity=RiskLevel.HIGH,
                category="accountability",
                remediation=(
                    "Conduct DPIAs for high-risk processing, especially AI/ML systems: "
                    "1) Describe processing operations and purposes, 2) Assess necessity "
                    "and proportionality, 3) Identify and assess risks to data subjects, "
                    "4) Identify measures to address risks, 5) Consult with DPO, "
                    "6) Review and update as processing changes. For new AI systems, "
                    "complete DPIA before deployment."
                ),
                references=["GDPR Article 35(1-11)", "Recitals 89-92"],
            ),
        ]

    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single GDPR rule against an audit entry.

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
        if rule.rule_id == "GDPR-Art5":
            return self._check_data_processing_principles(entry, rule)
        elif rule.rule_id == "GDPR-Art6":
            return self._check_lawful_basis(entry, rule)
        elif rule.rule_id == "GDPR-Art7":
            return self._check_consent(entry, rule)
        elif rule.rule_id == "GDPR-Art12":
            return self._check_transparent_communication(entry, rule)
        elif rule.rule_id == "GDPR-Art13":
            return self._check_information_at_collection(entry, rule)
        elif rule.rule_id == "GDPR-Art15":
            return self._check_right_of_access(entry, rule)
        elif rule.rule_id == "GDPR-Art17":
            return self._check_right_to_erasure(entry, rule)
        elif rule.rule_id == "GDPR-Art20":
            return self._check_data_portability(entry, rule)
        elif rule.rule_id == "GDPR-Art22":
            return self._check_automated_decision_making(entry, rule)
        elif rule.rule_id == "GDPR-Art25":
            return self._check_privacy_by_design(entry, rule)
        elif rule.rule_id == "GDPR-Art30":
            return self._check_processing_records(entry, rule)
        elif rule.rule_id == "GDPR-Art32":
            return self._check_security(entry, rule)
        elif rule.rule_id == "GDPR-Art33":
            return self._check_breach_notification(entry, rule)
        elif rule.rule_id == "GDPR-Art35":
            return self._check_dpia(entry, rule)

        return None

    def _check_data_processing_principles(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art5: Data processing must follow core GDPR principles.

        Operations involving personal data must demonstrate compliance with
        lawfulness, fairness, transparency, purpose limitation, data minimisation,
        accuracy, storage limitation, integrity, confidentiality, and accountability.
        """
        # Check if processing involves personal data
        pii_classifications = {"pii", "personal", "sensitive", "special_category"}
        if entry.data_classification.lower() not in pii_classifications:
            return None

        # Check for documented principles compliance
        has_lawful_basis = entry.metadata.get("lawful_basis_documented", False)
        has_purpose_limitation = entry.metadata.get("purpose_documented", False)

        if not (has_lawful_basis and has_purpose_limitation):
            return self._create_violation(
                entry,
                rule,
                f"Personal data processing (classification={entry.data_classification}) "
                f"without documented lawful basis or purpose limitation",
            )
        return None

    def _check_lawful_basis(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art6: Processing must have a documented lawful basis.

        Each processing operation must identify one of the six lawful bases:
        consent, contract, legal obligation, vital interests, public interest,
        or legitimate interests.
        """
        pii_classifications = {"pii", "personal", "sensitive", "special_category"}
        if entry.data_classification.lower() not in pii_classifications:
            return None

        lawful_basis = entry.metadata.get("lawful_basis")
        valid_bases = {
            "consent", "contract", "legal_obligation",
            "vital_interests", "public_interest", "legitimate_interests"
        }

        if not lawful_basis or lawful_basis.lower() not in valid_bases:
            return self._create_violation(
                entry,
                rule,
                f"Personal data processing (classification={entry.data_classification}) "
                f"without valid lawful basis. Provided: {lawful_basis or 'None'}",
            )
        return None

    def _check_consent(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art7: When consent is the lawful basis, it must meet requirements.

        Consent must be freely given, specific, informed, unambiguous, and
        demonstrable. The data subject must be able to withdraw consent easily.
        """
        # Only applies when consent is the lawful basis
        lawful_basis = entry.metadata.get("lawful_basis", "").lower()
        if lawful_basis != "consent":
            return None

        consent_recorded = entry.metadata.get("consent_recorded", False)
        consent_specific = entry.metadata.get("consent_specific", False)
        consent_informed = entry.metadata.get("consent_informed", False)

        if not all([consent_recorded, consent_specific, consent_informed]):
            missing = []
            if not consent_recorded:
                missing.append("recorded")
            if not consent_specific:
                missing.append("specific")
            if not consent_informed:
                missing.append("informed")
            return self._create_violation(
                entry,
                rule,
                f"Consent-based processing without valid consent. Missing: {', '.join(missing)}",
            )
        return None

    def _check_transparent_communication(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art12: Information must be provided transparently.

        Communications about data processing must be concise, transparent,
        intelligible, and easily accessible, using clear and plain language.
        """
        # Check for user-facing data collection events
        collection_events = {"data_collection", "registration", "signup", "form_submission"}
        if entry.event_type.lower() not in collection_events:
            return None

        privacy_notice_provided = entry.metadata.get("privacy_notice_provided", False)
        if not privacy_notice_provided:
            return self._create_violation(
                entry,
                rule,
                f"Data collection event (type={entry.event_type}) without "
                f"transparent privacy information provided to data subject",
            )
        return None

    def _check_information_at_collection(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art13: Required information must be provided at collection.

        When collecting personal data, data subjects must receive comprehensive
        information about the processing including controller identity, purposes,
        legal basis, rights, and retention periods.
        """
        collection_events = {"data_collection", "registration", "signup", "form_submission"}
        if entry.event_type.lower() not in collection_events:
            return None

        pii_classifications = {"pii", "personal", "sensitive", "special_category"}
        if entry.data_classification.lower() not in pii_classifications:
            return None

        disclosure_complete = entry.metadata.get("art13_disclosure_complete", False)
        if not disclosure_complete:
            return self._create_violation(
                entry,
                rule,
                f"Personal data collection (type={entry.event_type}) without "
                f"complete Article 13 information disclosure",
            )
        return None

    def _check_right_of_access(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art15: Data subject access requests must be handled properly.

        When a data subject requests access, the controller must provide
        confirmation of processing and a copy of personal data within one month.
        """
        access_events = {"data_subject_access_request", "dsar", "subject_access_request"}
        if entry.event_type.lower() not in access_events:
            return None

        response_within_deadline = entry.metadata.get("response_within_deadline", False)
        complete_response = entry.metadata.get("complete_response_provided", False)

        if not response_within_deadline:
            return self._create_violation(
                entry,
                rule,
                f"Data subject access request (type={entry.event_type}) not "
                f"responded to within the required timeframe",
            )

        if not complete_response:
            return self._create_violation(
                entry,
                rule,
                f"Data subject access request (type={entry.event_type}) response "
                f"incomplete - must include all personal data and required information",
            )
        return None

    def _check_right_to_erasure(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art17: Erasure requests must be handled properly.

        When a data subject requests erasure and it is valid, the controller
        must erase data without undue delay and notify third parties.
        """
        erasure_events = {"erasure_request", "deletion_request", "right_to_be_forgotten"}
        if entry.event_type.lower() not in erasure_events:
            return None

        erasure_complete = entry.metadata.get("erasure_complete", False)
        third_parties_notified = entry.metadata.get("third_parties_notified", True)  # Default True if N/A

        if not erasure_complete:
            return self._create_violation(
                entry,
                rule,
                f"Erasure request (type={entry.event_type}) not completed - "
                f"personal data must be erased from all systems",
            )

        if not third_parties_notified:
            return self._create_violation(
                entry,
                rule,
                f"Erasure request (type={entry.event_type}) - third party "
                f"recipients of data not notified of erasure requirement",
            )
        return None

    def _check_data_portability(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art20: Portability requests must provide data in machine-readable format.

        Data subjects have the right to receive their data in a structured,
        commonly used, and machine-readable format.
        """
        portability_events = {"portability_request", "data_export_request"}
        if entry.event_type.lower() not in portability_events:
            return None

        machine_readable_format = entry.metadata.get("machine_readable_format", False)
        if not machine_readable_format:
            return self._create_violation(
                entry,
                rule,
                f"Data portability request (type={entry.event_type}) - data not "
                f"provided in structured, machine-readable format",
            )
        return None

    def _check_automated_decision_making(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art22: Automated decisions with significant effects need safeguards.

        Data subjects have the right not to be subject to solely automated
        decisions with legal or similarly significant effects without safeguards.
        """
        automated_decision_events = {
            "automated_decision", "profiling", "scoring",
            "credit_decision", "hiring_decision", "eligibility_decision"
        }
        if entry.event_type.lower() not in automated_decision_events:
            return None

        # Check if decision has significant effects
        has_significant_effect = entry.metadata.get("significant_effect", False)
        if not has_significant_effect:
            return None

        # Check for required safeguards
        human_intervention_available = entry.metadata.get("human_intervention_available", False)
        right_to_contest_enabled = entry.metadata.get("right_to_contest_enabled", False)
        logic_explained = entry.metadata.get("logic_explained", False)

        if not human_intervention_available:
            return self._create_violation(
                entry,
                rule,
                f"Automated decision with significant effect (type={entry.event_type}) "
                f"without human intervention mechanism available",
            )

        if not right_to_contest_enabled:
            return self._create_violation(
                entry,
                rule,
                f"Automated decision with significant effect (type={entry.event_type}) "
                f"without right to contest the decision",
            )

        if not logic_explained:
            return self._create_violation(
                entry,
                rule,
                f"Automated decision with significant effect (type={entry.event_type}) "
                f"without meaningful information about the logic involved",
            )
        return None

    def _check_privacy_by_design(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art25: Systems must implement privacy by design and default.

        Controllers must implement technical and organisational measures
        to implement data protection principles and ensure minimal data
        processing by default.
        """
        design_events = {"system_deployment", "feature_launch", "processing_change"}
        if entry.event_type.lower() not in design_events:
            return None

        privacy_by_design_assessment = entry.metadata.get("privacy_by_design_assessment", False)
        data_minimisation_default = entry.metadata.get("data_minimisation_default", False)

        if not privacy_by_design_assessment:
            return self._create_violation(
                entry,
                rule,
                f"System deployment/change (type={entry.event_type}) without "
                f"documented privacy by design assessment",
            )

        if not data_minimisation_default:
            return self._create_violation(
                entry,
                rule,
                f"System deployment/change (type={entry.event_type}) without "
                f"data minimisation implemented by default",
            )
        return None

    def _check_processing_records(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art30: Records of processing activities must be maintained.

        Controllers must maintain written records of processing activities
        including purposes, data categories, recipients, and security measures.
        """
        pii_classifications = {"pii", "personal", "sensitive", "special_category"}
        if entry.data_classification.lower() not in pii_classifications:
            return None

        # Check for significant processing operations
        significant_events = {"data_processing", "data_transfer", "new_processing_activity"}
        if entry.event_type.lower() not in significant_events:
            return None

        ropa_entry_exists = entry.metadata.get("ropa_entry_exists", False)
        if not ropa_entry_exists:
            return self._create_violation(
                entry,
                rule,
                f"Processing activity (type={entry.event_type}) not recorded in "
                f"the Records of Processing Activities (ROPA)",
            )
        return None

    def _check_security(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art32: Appropriate security measures must be in place.

        Processing must implement security measures appropriate to the risk,
        including encryption, access controls, and regular security testing.
        """
        pii_classifications = {"pii", "personal", "sensitive", "special_category"}
        if entry.data_classification.lower() not in pii_classifications:
            return None

        # Check for security-relevant operations
        security_relevant_events = {
            "data_access", "data_transfer", "data_processing",
            "data_export", "api_call", "model_inference"
        }
        if entry.event_type.lower() not in security_relevant_events:
            return None

        encryption_applied = entry.metadata.get("encryption_applied", False)
        access_controlled = entry.metadata.get("access_controlled", False)

        if not encryption_applied:
            return self._create_violation(
                entry,
                rule,
                f"Personal data operation (type={entry.event_type}) without "
                f"appropriate encryption measures",
            )

        if not access_controlled:
            return self._create_violation(
                entry,
                rule,
                f"Personal data operation (type={entry.event_type}) without "
                f"appropriate access control measures",
            )
        return None

    def _check_breach_notification(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art33: Breaches must be notified within 72 hours.

        Personal data breaches must be notified to the supervisory authority
        within 72 hours of becoming aware, unless unlikely to result in risk.
        """
        breach_events = {"data_breach", "security_incident", "unauthorized_access"}
        if entry.event_type.lower() not in breach_events:
            return None

        # Check if this is a reportable breach
        risk_to_rights = entry.metadata.get("risk_to_rights_freedoms", True)
        if not risk_to_rights:
            return None  # No notification required if no risk

        notification_sent = entry.metadata.get("supervisory_authority_notified", False)
        notification_within_72h = entry.metadata.get("notification_within_72_hours", False)

        if not notification_sent:
            return self._create_violation(
                entry,
                rule,
                f"Personal data breach (type={entry.event_type}) not notified "
                f"to supervisory authority",
            )

        if not notification_within_72h:
            return self._create_violation(
                entry,
                rule,
                f"Personal data breach (type={entry.event_type}) notification "
                f"exceeded 72-hour requirement without documented justification",
            )
        return None

    def _check_dpia(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check GDPR-Art35: High-risk processing requires DPIA.

        A Data Protection Impact Assessment is required for processing
        likely to result in high risk, including profiling, large-scale
        special category processing, and systematic monitoring.
        """
        # Check for high-risk processing types
        high_risk_events = {
            "profiling", "automated_decision", "large_scale_processing",
            "systematic_monitoring", "special_category_processing",
            "new_technology_deployment", "ai_model_deployment"
        }
        if entry.event_type.lower() not in high_risk_events:
            return None

        # Also trigger for high-risk level entries
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        dpia_completed = entry.metadata.get("dpia_completed", False)
        dpia_reviewed = entry.metadata.get("dpia_reviewed_by_dpo", False)

        if not dpia_completed:
            return self._create_violation(
                entry,
                rule,
                f"High-risk processing (type={entry.event_type}) commenced "
                f"without completing Data Protection Impact Assessment",
            )

        if not dpia_reviewed:
            return self._create_violation(
                entry,
                rule,
                f"High-risk processing (type={entry.event_type}) DPIA not "
                f"reviewed by Data Protection Officer",
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
