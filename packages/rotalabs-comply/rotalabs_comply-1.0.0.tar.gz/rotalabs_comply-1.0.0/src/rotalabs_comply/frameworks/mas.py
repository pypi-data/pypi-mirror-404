"""
MAS (Monetary Authority of Singapore) AI governance compliance framework.

The Monetary Authority of Singapore (MAS) has established comprehensive guidelines
for the use of Artificial Intelligence and Data Analytics (AIDA) in financial
institutions. This framework implements compliance checks based on:

1. **FEAT Principles** (Fairness, Ethics, Accountability, Transparency):
   The core framework guiding responsible AI adoption in Singapore's financial
   sector, published in the "Principles to Promote Fairness, Ethics, Accountability
   and Transparency (FEAT) in the Use of Artificial Intelligence and Data Analytics
   in Singapore's Financial Sector" document.

2. **Model Risk Management (MRM)** Guidelines:
   Requirements for governance, development, validation, and monitoring of AI/ML
   models used in material decision-making processes.

3. **Technology Risk Management (TRM)** Guidelines:
   Operational resilience requirements for technology systems including AI.

This framework is specifically designed for financial institutions regulated by MAS,
including banks, insurers, capital market intermediaries, and payment service providers
operating in Singapore.

Categories:
- fairness: Rules ensuring AI decisions are fair and unbiased
- ethics: Rules for ethical use of data and AI alignment with firm standards
- accountability: Rules requiring clear accountability and human oversight
- transparency: Rules for explainability and customer notification
- model_risk: Rules for model development, validation, and monitoring
- data_governance: Rules for data quality, lineage, and privacy
- operations: Rules for system resilience and incident management

References:
- MAS FEAT Principles: https://www.mas.gov.sg/publications/monographs-or-information-paper/2018/FEAT
- MAS Guidelines on Technology Risk Management: https://www.mas.gov.sg/regulation/guidelines/technology-risk-management-guidelines
- MAS Information Papers on AI Governance: https://www.mas.gov.sg/publications/monographs-or-information-paper
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


class MASFramework(BaseFramework):
    """
    MAS (Monetary Authority of Singapore) AI governance compliance framework.

    Implements compliance checks based on MAS FEAT principles and AI governance
    guidelines for financial institutions operating in Singapore. The framework
    evaluates audit entries against requirements for fairness, ethics, accountability,
    transparency, model risk management, data governance, and operational resilience.

    The FEAT principles establish expectations for financial institutions to:
    - Ensure AI-driven decisions are fair and do not result in unfair treatment
    - Use data and AI in an ethical manner aligned with firm values
    - Maintain clear accountability structures for AI decisions
    - Provide transparency to customers about AI use and decision-making

    Additionally, the framework incorporates MAS model risk management requirements
    and technology risk management guidelines relevant to AI systems.

    Example:
        >>> framework = MASFramework()
        >>> result = await framework.check(entry, profile)
        >>> if not result.is_compliant:
        ...     for violation in result.violations:
        ...         print(f"{violation.rule_id}: {violation.description}")

    Note:
        This framework is specifically designed for financial institutions
        regulated by MAS. Organizations outside MAS jurisdiction should
        use other appropriate frameworks.
    """

    def __init__(self):
        """Initialize the MAS framework with all defined rules."""
        rules = self._create_rules()
        super().__init__(name="MAS FEAT", version="2022", rules=rules)

    def _create_rules(self) -> List[ComplianceRule]:
        """
        Create all MAS compliance rules.

        Returns:
            List of ComplianceRule objects representing MAS FEAT principles
            and AI governance requirements
        """
        return [
            # ================================================================
            # FEAT Principles - Fairness
            # ================================================================
            ComplianceRule(
                rule_id="MAS-FEAT-F1",
                name="Fair AI-Driven Decisions",
                description=(
                    "Financial institutions should ensure that AI-driven decisions are "
                    "fair and do not systematically disadvantage individuals or groups. "
                    "AI systems used in customer-facing decisions (e.g., credit scoring, "
                    "insurance underwriting, fraud detection) must be designed to avoid "
                    "unfair discrimination based on protected attributes such as race, "
                    "gender, age, religion, or nationality, except where such attributes "
                    "are legitimate risk factors permitted by law."
                ),
                severity=RiskLevel.HIGH,
                category="fairness",
                remediation=(
                    "Implement fairness testing procedures that evaluate AI outcomes "
                    "across different demographic groups. Document fairness metrics and "
                    "thresholds, and conduct regular fairness audits. Consider using "
                    "fairness-aware algorithms and establish governance processes for "
                    "reviewing and addressing fairness concerns."
                ),
                references=[
                    "MAS FEAT Principles - Fairness",
                    "MAS Information Paper on FEAT (2018)",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-FEAT-F2",
                name="Bias Detection and Mitigation",
                description=(
                    "Financial institutions must implement measures to detect and mitigate "
                    "biases in AI systems throughout the model lifecycle. This includes "
                    "bias detection during model development, ongoing monitoring for "
                    "emergent biases, and corrective actions when biases are identified. "
                    "Institutions should assess training data for historical biases and "
                    "implement appropriate debiasing techniques where necessary."
                ),
                severity=RiskLevel.HIGH,
                category="fairness",
                remediation=(
                    "Establish bias detection processes including statistical analysis "
                    "of training data and model outputs. Implement bias monitoring "
                    "dashboards that track fairness metrics over time. Document bias "
                    "mitigation strategies and maintain records of debiasing actions "
                    "taken. Conduct periodic bias assessments and reviews."
                ),
                references=[
                    "MAS FEAT Principles - Fairness",
                    "MAS Veritas Framework for Responsible AI",
                ],
            ),
            # ================================================================
            # FEAT Principles - Ethics
            # ================================================================
            ComplianceRule(
                rule_id="MAS-FEAT-E1",
                name="Ethical Use of Data and AI",
                description=(
                    "Financial institutions must ensure that data and AI are used in an "
                    "ethical manner, respecting customer privacy, data protection requirements, "
                    "and legitimate customer expectations. AI systems should not be used "
                    "in ways that manipulate, deceive, or exploit customers. The use of "
                    "alternative data sources must be evaluated for ethical implications "
                    "and potential for unfair discrimination."
                ),
                severity=RiskLevel.HIGH,
                category="ethics",
                remediation=(
                    "Establish an AI ethics review process for new AI use cases. "
                    "Document ethical considerations in AI system design documents. "
                    "Implement data usage policies that ensure ethical data practices. "
                    "Create mechanisms for stakeholders to raise ethical concerns about "
                    "AI systems. Review alternative data sources for ethical implications."
                ),
                references=[
                    "MAS FEAT Principles - Ethics",
                    "MAS Personal Data Protection Guidelines",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-FEAT-E2",
                name="AI Alignment with Firm's Ethical Standards",
                description=(
                    "AI systems must be developed and operated in alignment with the "
                    "financial institution's ethical standards, corporate values, and "
                    "professional codes of conduct. The use of AI should support, not "
                    "undermine, the institution's commitment to treating customers fairly "
                    "and maintaining market integrity."
                ),
                severity=RiskLevel.MEDIUM,
                category="ethics",
                remediation=(
                    "Document how AI systems align with the firm's ethical standards "
                    "and corporate values. Include ethics compliance as part of AI "
                    "system design reviews. Ensure AI development teams are trained "
                    "on the firm's ethical standards. Establish escalation procedures "
                    "for ethical concerns related to AI systems."
                ),
                references=[
                    "MAS FEAT Principles - Ethics",
                    "MAS Guidelines on Fair Dealing",
                ],
            ),
            # ================================================================
            # FEAT Principles - Accountability
            # ================================================================
            ComplianceRule(
                rule_id="MAS-FEAT-A1",
                name="Clear Accountability for AI Decisions",
                description=(
                    "Financial institutions must establish clear accountability structures "
                    "for AI-driven decisions. This includes identifying individuals or "
                    "committees responsible for AI system outcomes, ensuring appropriate "
                    "governance oversight, and maintaining documentation of decision-making "
                    "authority and responsibility. Senior management must be accountable "
                    "for material AI systems and their outcomes."
                ),
                severity=RiskLevel.HIGH,
                category="accountability",
                remediation=(
                    "Define and document clear ownership and accountability for each "
                    "AI system, including business owners, model owners, and technical "
                    "owners. Establish AI governance committees with appropriate "
                    "senior management representation. Create RACI matrices for AI "
                    "decision-making processes. Ensure accountability is traceable "
                    "in audit logs."
                ),
                references=[
                    "MAS FEAT Principles - Accountability",
                    "MAS Guidelines on Individual Accountability and Conduct",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-FEAT-A2",
                name="Human Oversight for Material AI Decisions",
                description=(
                    "Material AI-driven decisions must include appropriate human oversight. "
                    "Financial institutions should implement human-in-the-loop or "
                    "human-on-the-loop mechanisms for AI systems that significantly impact "
                    "customers or business operations. Humans must have the ability to "
                    "intervene, override, or stop AI system operations when necessary."
                ),
                severity=RiskLevel.CRITICAL,
                category="accountability",
                remediation=(
                    "Implement human oversight mechanisms appropriate to the risk level "
                    "of AI decisions. Define criteria for when human review is mandatory. "
                    "Provide tools and interfaces for humans to review, override, and "
                    "intervene in AI decisions. Document human oversight procedures and "
                    "ensure adequate training for personnel involved in oversight roles."
                ),
                references=[
                    "MAS FEAT Principles - Accountability",
                    "MAS Model Risk Management Guidelines",
                ],
            ),
            # ================================================================
            # FEAT Principles - Transparency
            # ================================================================
            ComplianceRule(
                rule_id="MAS-FEAT-T1",
                name="Explainable AI Decisions",
                description=(
                    "Financial institutions should ensure that AI-driven decisions can be "
                    "explained in a manner appropriate to the context and audience. "
                    "Explanations should be provided for material decisions affecting "
                    "customers, and internal stakeholders should have access to more "
                    "detailed technical explanations. The level of explainability should "
                    "be proportionate to the significance of the decision."
                ),
                severity=RiskLevel.HIGH,
                category="transparency",
                remediation=(
                    "Implement explainability mechanisms appropriate to each AI use case. "
                    "Use interpretable models where possible, or implement post-hoc "
                    "explanation techniques for complex models. Document the explanation "
                    "methodology and ensure explanations are understandable by the "
                    "intended audience. Maintain explanation logs for audit purposes."
                ),
                references=[
                    "MAS FEAT Principles - Transparency",
                    "MAS Information Paper on Responsible AI in Finance",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-FEAT-T2",
                name="Customer Notification of AI Use",
                description=(
                    "Customers should be informed when AI is used to make or significantly "
                    "influence decisions that affect them. Financial institutions should "
                    "communicate the role of AI in decision-making processes, the types "
                    "of data used, and how customers can seek recourse or human review "
                    "of AI-driven decisions. Notification should be clear, timely, and "
                    "accessible."
                ),
                severity=RiskLevel.HIGH,
                category="transparency",
                remediation=(
                    "Implement clear notification mechanisms to inform customers when AI "
                    "is involved in decisions affecting them. Include AI disclosure in "
                    "customer communications and terms of service. Establish processes "
                    "for customers to request human review of AI decisions. Maintain "
                    "records of customer notifications for audit purposes."
                ),
                references=[
                    "MAS FEAT Principles - Transparency",
                    "MAS Guidelines on Fair Dealing",
                ],
            ),
            # ================================================================
            # Model Risk Management
            # ================================================================
            ComplianceRule(
                rule_id="MAS-MRM-1",
                name="Model Development Standards",
                description=(
                    "Financial institutions must establish robust standards for AI/ML "
                    "model development. This includes documented development methodologies, "
                    "data quality requirements, feature engineering standards, model "
                    "selection criteria, and performance benchmarks. Development processes "
                    "should ensure models are fit for purpose and align with business "
                    "requirements."
                ),
                severity=RiskLevel.HIGH,
                category="model_risk",
                remediation=(
                    "Establish and document model development standards and methodologies. "
                    "Define data quality requirements for model development. Implement "
                    "version control for models and code. Document model assumptions, "
                    "limitations, and intended use cases. Ensure development processes "
                    "are reviewed and approved by appropriate stakeholders."
                ),
                references=[
                    "MAS Model Risk Management Guidelines",
                    "MAS Technology Risk Management Guidelines",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-MRM-2",
                name="Model Validation Requirements",
                description=(
                    "All material AI/ML models must undergo independent validation before "
                    "deployment and periodically thereafter. Validation should assess "
                    "model conceptual soundness, data quality, model performance, and "
                    "outcome analysis. The validation function should be independent of "
                    "the model development function."
                ),
                severity=RiskLevel.HIGH,
                category="model_risk",
                remediation=(
                    "Establish an independent model validation function. Define validation "
                    "scope, methodology, and frequency based on model materiality. "
                    "Document validation findings and remediation actions. Ensure "
                    "validation coverage includes conceptual soundness, implementation, "
                    "and ongoing performance monitoring. Maintain validation records."
                ),
                references=[
                    "MAS Model Risk Management Guidelines",
                    "MAS Supervisory Expectations on Model Risk",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-MRM-3",
                name="Model Monitoring and Review",
                description=(
                    "Financial institutions must implement ongoing monitoring of AI/ML "
                    "models to detect performance degradation, data drift, concept drift, "
                    "and unexpected behaviors. Models should be subject to periodic review "
                    "and revalidation. Monitoring should include performance metrics, "
                    "stability metrics, and business outcome tracking."
                ),
                severity=RiskLevel.HIGH,
                category="model_risk",
                remediation=(
                    "Implement comprehensive model monitoring frameworks that track "
                    "performance metrics, input data distributions, and output patterns. "
                    "Define alert thresholds and escalation procedures. Establish "
                    "periodic review schedules based on model materiality. Document "
                    "monitoring results and actions taken in response to issues."
                ),
                references=[
                    "MAS Model Risk Management Guidelines",
                    "MAS Technology Risk Management Guidelines",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-MRM-4",
                name="Model Inventory Maintained",
                description=(
                    "Financial institutions must maintain a comprehensive inventory of "
                    "all AI/ML models in use. The inventory should include model metadata, "
                    "risk classifications, ownership information, validation status, and "
                    "deployment details. The inventory enables effective governance and "
                    "risk management of the model portfolio."
                ),
                severity=RiskLevel.MEDIUM,
                category="model_risk",
                remediation=(
                    "Establish and maintain a centralized model inventory. Include "
                    "essential metadata such as model purpose, risk tier, owner, "
                    "validation status, and performance metrics. Implement processes "
                    "to keep the inventory up to date. Use the inventory for portfolio "
                    "risk assessment and resource allocation decisions."
                ),
                references=[
                    "MAS Model Risk Management Guidelines",
                    "MAS Technology Risk Management Guidelines",
                ],
            ),
            # ================================================================
            # Data Governance
            # ================================================================
            ComplianceRule(
                rule_id="MAS-DATA-1",
                name="Data Quality Standards",
                description=(
                    "Financial institutions must establish and maintain data quality "
                    "standards for AI systems. Data used in AI/ML models should be "
                    "accurate, complete, consistent, timely, and relevant. Data quality "
                    "should be assessed and documented, with processes in place to "
                    "address data quality issues."
                ),
                severity=RiskLevel.HIGH,
                category="data_governance",
                remediation=(
                    "Define data quality standards and metrics for AI use cases. "
                    "Implement data quality checks and validation procedures. "
                    "Document data quality assessments and remediation actions. "
                    "Establish data quality monitoring and alerting mechanisms. "
                    "Ensure data quality issues are escalated and resolved promptly."
                ),
                references=[
                    "MAS Data Management Guidelines",
                    "MAS Technology Risk Management Guidelines",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-DATA-2",
                name="Data Lineage Documentation",
                description=(
                    "Financial institutions must maintain documentation of data lineage "
                    "for AI systems. This includes tracking data sources, transformations, "
                    "aggregations, and dependencies throughout the data pipeline. Data "
                    "lineage supports auditability, debugging, and impact analysis."
                ),
                severity=RiskLevel.MEDIUM,
                category="data_governance",
                remediation=(
                    "Implement data lineage tracking for AI data pipelines. Document "
                    "data sources, transformations, and dependencies. Use data lineage "
                    "tools or metadata management systems where appropriate. Ensure "
                    "data lineage is available for audit and investigation purposes. "
                    "Maintain lineage documentation for the data retention period."
                ),
                references=[
                    "MAS Data Management Guidelines",
                    "MAS Technology Risk Management Guidelines",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-DATA-3",
                name="Data Privacy Compliance",
                description=(
                    "AI systems must comply with data privacy requirements including "
                    "Singapore's Personal Data Protection Act (PDPA) and MAS-specific "
                    "data protection requirements. This includes obtaining appropriate "
                    "consent, limiting data use to stated purposes, implementing data "
                    "minimization, and ensuring secure data handling."
                ),
                severity=RiskLevel.CRITICAL,
                category="data_governance",
                remediation=(
                    "Ensure AI systems comply with PDPA and MAS data protection requirements. "
                    "Implement appropriate consent mechanisms for data collection and use. "
                    "Apply data minimization principles - collect and retain only necessary "
                    "data. Implement access controls and encryption for personal data. "
                    "Conduct privacy impact assessments for AI use cases involving personal data."
                ),
                references=[
                    "Singapore Personal Data Protection Act (PDPA)",
                    "MAS Guidelines on Fair Dealing",
                    "MAS Data Management Guidelines",
                ],
            ),
            # ================================================================
            # Operational Resilience
            # ================================================================
            ComplianceRule(
                rule_id="MAS-OPS-1",
                name="AI System Resilience",
                description=(
                    "AI systems must be designed and operated with appropriate resilience "
                    "measures to ensure continued availability and performance. This "
                    "includes redundancy, failover mechanisms, capacity management, and "
                    "graceful degradation capabilities. Systems should be resilient to "
                    "input anomalies and adversarial inputs."
                ),
                severity=RiskLevel.HIGH,
                category="operations",
                remediation=(
                    "Design AI systems with appropriate redundancy and failover "
                    "capabilities. Implement input validation and anomaly detection. "
                    "Test system resilience through chaos engineering and stress testing. "
                    "Define and implement graceful degradation strategies. Document "
                    "resilience requirements and validate compliance during deployment."
                ),
                references=[
                    "MAS Technology Risk Management Guidelines",
                    "MAS Business Continuity Management Guidelines",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-OPS-2",
                name="Incident Management for AI Failures",
                description=(
                    "Financial institutions must have incident management procedures "
                    "specifically addressing AI system failures. This includes detection "
                    "mechanisms, escalation procedures, impact assessment, root cause "
                    "analysis, and communication protocols. AI-related incidents should "
                    "be reported to MAS where required."
                ),
                severity=RiskLevel.HIGH,
                category="operations",
                remediation=(
                    "Establish incident management procedures for AI systems. Define "
                    "AI-specific incident categories and severity classifications. "
                    "Implement monitoring and alerting for AI system failures. "
                    "Document escalation procedures and communication protocols. "
                    "Conduct post-incident reviews and implement lessons learned."
                ),
                references=[
                    "MAS Technology Risk Management Guidelines",
                    "MAS Notice on Cyber Hygiene",
                    "MAS Incident Reporting Requirements",
                ],
            ),
            ComplianceRule(
                rule_id="MAS-OPS-3",
                name="Business Continuity for AI Systems",
                description=(
                    "Financial institutions must include AI systems in their business "
                    "continuity planning. This includes identifying critical AI dependencies, "
                    "establishing recovery procedures, defining backup and fallback options, "
                    "and testing continuity plans. Business continuity plans should address "
                    "scenarios where AI systems are unavailable."
                ),
                severity=RiskLevel.MEDIUM,
                category="operations",
                remediation=(
                    "Include AI systems in business continuity planning and testing. "
                    "Identify critical AI system dependencies and recovery requirements. "
                    "Define fallback procedures for AI system unavailability (e.g., "
                    "manual processing, simplified models). Test business continuity "
                    "plans including AI failure scenarios. Document recovery time "
                    "objectives and recovery point objectives for AI systems."
                ),
                references=[
                    "MAS Technology Risk Management Guidelines",
                    "MAS Business Continuity Management Guidelines",
                ],
            ),
        ]

    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single MAS rule against an audit entry.

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
        if rule.rule_id == "MAS-FEAT-F1":
            return self._check_fair_decisions(entry, rule)
        elif rule.rule_id == "MAS-FEAT-F2":
            return self._check_bias_mitigation(entry, rule)
        elif rule.rule_id == "MAS-FEAT-E1":
            return self._check_ethical_data_use(entry, rule)
        elif rule.rule_id == "MAS-FEAT-E2":
            return self._check_ethical_alignment(entry, rule)
        elif rule.rule_id == "MAS-FEAT-A1":
            return self._check_accountability(entry, rule)
        elif rule.rule_id == "MAS-FEAT-A2":
            return self._check_human_oversight(entry, rule)
        elif rule.rule_id == "MAS-FEAT-T1":
            return self._check_explainability(entry, rule)
        elif rule.rule_id == "MAS-FEAT-T2":
            return self._check_customer_notification(entry, rule)
        elif rule.rule_id == "MAS-MRM-1":
            return self._check_development_standards(entry, rule)
        elif rule.rule_id == "MAS-MRM-2":
            return self._check_model_validation(entry, rule)
        elif rule.rule_id == "MAS-MRM-3":
            return self._check_model_monitoring(entry, rule)
        elif rule.rule_id == "MAS-MRM-4":
            return self._check_model_inventory(entry, rule)
        elif rule.rule_id == "MAS-DATA-1":
            return self._check_data_quality(entry, rule)
        elif rule.rule_id == "MAS-DATA-2":
            return self._check_data_lineage(entry, rule)
        elif rule.rule_id == "MAS-DATA-3":
            return self._check_data_privacy(entry, rule)
        elif rule.rule_id == "MAS-OPS-1":
            return self._check_system_resilience(entry, rule)
        elif rule.rule_id == "MAS-OPS-2":
            return self._check_incident_management(entry, rule)
        elif rule.rule_id == "MAS-OPS-3":
            return self._check_business_continuity(entry, rule)

        return None

    # ========================================================================
    # FEAT Fairness Checks
    # ========================================================================

    def _check_fair_decisions(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-F1: AI-driven decisions must be fair and unbiased.

        Customer-impacting AI decisions should have fairness assessments documented.
        """
        # Customer-impacting decision events
        customer_decision_events = {
            "credit_decision", "underwriting", "pricing", "fraud_detection",
            "risk_assessment", "loan_approval", "insurance_decision",
            "customer_scoring", "eligibility_check"
        }
        if entry.event_type.lower() not in customer_decision_events:
            return None

        has_fairness_assessment = entry.metadata.get("fairness_assessed", False)
        if not has_fairness_assessment:
            return self._create_violation(
                entry,
                rule,
                f"Customer-impacting AI decision (type={entry.event_type}) performed "
                f"without documented fairness assessment",
            )
        return None

    def _check_bias_mitigation(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-F2: Bias detection and mitigation measures in place.

        Model training and deployment should include bias mitigation documentation.
        """
        model_lifecycle_events = {
            "training", "fine_tuning", "deployment", "model_update",
            "model_release", "model_promotion"
        }
        if entry.event_type.lower() not in model_lifecycle_events:
            return None

        has_bias_mitigation = entry.metadata.get("bias_mitigation_documented", False)
        if not has_bias_mitigation:
            return self._create_violation(
                entry,
                rule,
                f"Model lifecycle event (type={entry.event_type}) performed "
                f"without documented bias detection and mitigation measures",
            )
        return None

    # ========================================================================
    # FEAT Ethics Checks
    # ========================================================================

    def _check_ethical_data_use(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-E1: Ethical use of data and AI.

        Data processing and AI operations should comply with ethical data use policies.
        """
        data_use_events = {
            "data_ingestion", "data_processing", "feature_engineering",
            "training", "data_access", "data_export"
        }
        if entry.event_type.lower() not in data_use_events:
            return None

        has_ethics_review = entry.metadata.get("ethics_reviewed", False)
        if not has_ethics_review:
            return self._create_violation(
                entry,
                rule,
                f"Data/AI operation (type={entry.event_type}) performed "
                f"without documented ethical review",
            )
        return None

    def _check_ethical_alignment(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-E2: AI aligns with firm's ethical standards.

        AI deployments should document alignment with firm ethical standards.
        """
        deployment_events = {"deployment", "model_release", "go_live", "production_release"}
        if entry.event_type.lower() not in deployment_events:
            return None

        has_ethics_alignment = entry.metadata.get("ethics_aligned", False)
        if not has_ethics_alignment:
            return self._create_violation(
                entry,
                rule,
                f"AI deployment (type={entry.event_type}) performed "
                f"without documented alignment with firm's ethical standards",
            )
        return None

    # ========================================================================
    # FEAT Accountability Checks
    # ========================================================================

    def _check_accountability(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-A1: Clear accountability for AI decisions.

        AI operations should have documented accountability and ownership.
        """
        # All material AI events should have accountability
        material_events = {
            "inference", "prediction", "decision", "credit_decision",
            "underwriting", "fraud_detection", "risk_assessment",
            "deployment", "model_update"
        }
        if entry.event_type.lower() not in material_events:
            return None

        has_accountability = (
            entry.metadata.get("accountable_owner", "") != "" or
            entry.metadata.get("accountability_documented", False)
        )
        if not has_accountability:
            return self._create_violation(
                entry,
                rule,
                f"Material AI operation (type={entry.event_type}) performed "
                f"without documented accountability structure",
            )
        return None

    def _check_human_oversight(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-A2: Human oversight for material AI decisions.

        High-risk and material AI decisions require human oversight.
        """
        # Only applies to high-risk and critical operations
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        if not entry.human_oversight:
            return self._create_violation(
                entry,
                rule,
                f"Material AI operation (level={entry.risk_level.value}, "
                f"type={entry.event_type}) performed without human oversight",
            )
        return None

    # ========================================================================
    # FEAT Transparency Checks
    # ========================================================================

    def _check_explainability(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-T1: AI decisions are explainable.

        Customer-impacting decisions should have explanations available.
        """
        decision_events = {
            "inference", "prediction", "decision", "credit_decision",
            "underwriting", "pricing", "fraud_detection", "risk_assessment"
        }
        if entry.event_type.lower() not in decision_events:
            return None

        has_explanation = (
            entry.metadata.get("explanation_available", False) or
            entry.metadata.get("explainability_method", "") != ""
        )
        if not has_explanation:
            return self._create_violation(
                entry,
                rule,
                f"AI decision (type={entry.event_type}) performed "
                f"without explainability mechanism documented",
            )
        return None

    def _check_customer_notification(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-FEAT-T2: Customers informed of AI use.

        Customer-facing AI interactions should include notification of AI involvement.
        """
        customer_facing_events = {
            "inference", "chat", "interaction", "response", "recommendation",
            "credit_decision", "underwriting", "customer_service"
        }
        if entry.event_type.lower() not in customer_facing_events:
            return None

        if not entry.user_notified:
            return self._create_violation(
                entry,
                rule,
                f"Customer-facing AI operation (type={entry.event_type}) performed "
                f"without notifying customer of AI involvement",
            )
        return None

    # ========================================================================
    # Model Risk Management Checks
    # ========================================================================

    def _check_development_standards(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-MRM-1: Model development standards.

        Model development activities should follow documented standards.
        """
        development_events = {
            "training", "fine_tuning", "model_development", "feature_engineering",
            "model_selection"
        }
        if entry.event_type.lower() not in development_events:
            return None

        has_development_standards = (
            entry.metadata.get("development_standards_followed", False) or
            entry.documentation_ref is not None
        )
        if not has_development_standards:
            return self._create_violation(
                entry,
                rule,
                f"Model development activity (type={entry.event_type}) performed "
                f"without reference to development standards documentation",
            )
        return None

    def _check_model_validation(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-MRM-2: Model validation requirements.

        Model deployments should have validation documentation.
        """
        deployment_events = {"deployment", "model_release", "go_live", "production_release"}
        if entry.event_type.lower() not in deployment_events:
            return None

        has_validation = entry.metadata.get("validation_completed", False)
        if not has_validation:
            return self._create_violation(
                entry,
                rule,
                f"Model deployment (type={entry.event_type}) performed "
                f"without documented model validation",
            )
        return None

    def _check_model_monitoring(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-MRM-3: Model monitoring and review.

        Inference operations should have monitoring in place.
        """
        inference_events = {"inference", "prediction", "scoring", "decision"}
        if entry.event_type.lower() not in inference_events:
            return None

        has_monitoring = (
            entry.metadata.get("monitoring_enabled", False) or
            entry.metadata.get("performance_tracked", False)
        )
        if not has_monitoring:
            return self._create_violation(
                entry,
                rule,
                f"Model inference (type={entry.event_type}) performed "
                f"without documented monitoring configuration",
            )
        return None

    def _check_model_inventory(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-MRM-4: Model inventory maintained.

        Model operations should reference the model inventory.
        """
        model_events = {
            "deployment", "inference", "training", "model_update",
            "model_release", "model_retirement"
        }
        if entry.event_type.lower() not in model_events:
            return None

        has_inventory_ref = (
            entry.metadata.get("model_inventory_id", "") != "" or
            entry.metadata.get("model_registered", False)
        )
        if not has_inventory_ref:
            return self._create_violation(
                entry,
                rule,
                f"Model operation (type={entry.event_type}) performed "
                f"without reference to model inventory",
            )
        return None

    # ========================================================================
    # Data Governance Checks
    # ========================================================================

    def _check_data_quality(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-DATA-1: Data quality standards.

        Data operations should meet data quality standards.
        """
        data_events = {
            "data_ingestion", "data_processing", "training", "fine_tuning",
            "feature_engineering", "data_preparation"
        }
        if entry.event_type.lower() not in data_events:
            return None

        has_quality_check = entry.metadata.get("data_quality_validated", False)
        if not has_quality_check:
            return self._create_violation(
                entry,
                rule,
                f"Data operation (type={entry.event_type}) performed "
                f"without documented data quality validation",
            )
        return None

    def _check_data_lineage(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-DATA-2: Data lineage documented.

        Data transformations should have lineage documentation.
        """
        data_transformation_events = {
            "data_processing", "feature_engineering", "data_transformation",
            "data_aggregation", "data_preparation"
        }
        if entry.event_type.lower() not in data_transformation_events:
            return None

        has_lineage = (
            entry.metadata.get("lineage_documented", False) or
            entry.metadata.get("data_lineage_id", "") != ""
        )
        if not has_lineage:
            return self._create_violation(
                entry,
                rule,
                f"Data transformation (type={entry.event_type}) performed "
                f"without documented data lineage",
            )
        return None

    def _check_data_privacy(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-DATA-3: Data privacy compliance.

        Operations involving personal data should comply with privacy requirements.
        """
        # Check if personal data is involved
        personal_data_classifications = {"pii", "personal", "customer_data", "sensitive"}
        if entry.data_classification.lower() not in personal_data_classifications:
            return None

        has_privacy_compliance = (
            entry.metadata.get("privacy_compliant", False) or
            entry.metadata.get("consent_obtained", False)
        )
        if not has_privacy_compliance:
            return self._create_violation(
                entry,
                rule,
                f"Operation involving personal data (classification={entry.data_classification}) "
                f"performed without documented privacy compliance",
            )
        return None

    # ========================================================================
    # Operational Resilience Checks
    # ========================================================================

    def _check_system_resilience(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-OPS-1: AI system resilience.

        AI systems should demonstrate resilience measures.
        """
        # Check for error handling on all operations
        if not entry.error_handled:
            return self._create_violation(
                entry,
                rule,
                f"AI operation (type={entry.event_type}) indicates error was not "
                f"handled gracefully, suggesting resilience gap",
            )
        return None

    def _check_incident_management(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-OPS-2: Incident management for AI failures.

        Error events should trigger incident management procedures.
        """
        error_events = {"error", "failure", "exception", "timeout", "degradation"}
        if entry.event_type.lower() not in error_events:
            return None

        has_incident_management = (
            entry.metadata.get("incident_logged", False) or
            entry.metadata.get("incident_id", "") != ""
        )
        if not has_incident_management:
            return self._create_violation(
                entry,
                rule,
                f"AI error event (type={entry.event_type}) occurred "
                f"without documented incident management response",
            )
        return None

    def _check_business_continuity(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check MAS-OPS-3: Business continuity for AI systems.

        Critical AI operations should have business continuity documentation.
        """
        # Only check critical operations
        if entry.risk_level != RiskLevel.CRITICAL:
            return None

        has_bcp = (
            entry.metadata.get("bcp_documented", False) or
            entry.metadata.get("fallback_available", False)
        )
        if not has_bcp:
            return self._create_violation(
                entry,
                rule,
                f"Critical AI operation (type={entry.event_type}) performed "
                f"without documented business continuity provisions",
            )
        return None

    # ========================================================================
    # Helper Methods
    # ========================================================================

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
