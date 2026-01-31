"""
NIST AI Risk Management Framework (AI RMF) compliance implementation.

The NIST AI Risk Management Framework (AI RMF 1.0, January 2023) provides a
voluntary framework for managing AI risks throughout the AI system lifecycle.
It is designed to address risks to individuals, organizations, and society.

The framework is organized around four core functions:
- GOVERN: Establishes and maintains organizational AI risk management culture
- MAP: Identifies AI system context, capabilities, and risks
- MEASURE: Analyzes, assesses, and tracks AI risks
- MANAGE: Prioritizes, responds to, and monitors AI risks

Each function contains categories and subcategories that provide specific
outcomes and suggested actions for organizations to consider.

Categories in this implementation:
- governance: Organizational AI governance structures and accountability
- context: AI system context, intended use, and stakeholder analysis
- risk_identification: Identification of risks from AI systems and components
- measurement: Metrics, evaluation, and tracking of AI characteristics
- risk_treatment: Risk prioritization, response, and post-deployment monitoring

Reference: https://www.nist.gov/itl/ai-risk-management-framework
Publication: NIST AI 100-1 (January 2023)
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


class NISTAIRMFFramework(BaseFramework):
    """
    NIST AI Risk Management Framework compliance framework.

    Implements compliance checks based on the NIST AI RMF 1.0 (January 2023)
    requirements for managing AI system risks. The framework evaluates audit
    entries against requirements for governance, context mapping, risk
    measurement, and risk management.

    The NIST AI RMF is built on four core functions:

    1. GOVERN: Cross-cutting function that infuses the AI risk management
       culture into the organization. Establishes accountability structures,
       policies, and processes for AI risk management.

    2. MAP: Establishes the context for framing risks related to an AI system.
       Identifies and documents AI system characteristics, intended purposes,
       and potential impacts.

    3. MEASURE: Employs quantitative and qualitative methods to analyze,
       assess, and track AI risks and their impacts. Includes identification
       of appropriate metrics and evaluation methods.

    4. MANAGE: Allocates risk resources and implements responses to mapped
       and measured risks. Includes deployment decisions, post-deployment
       monitoring, and incident response.

    The framework emphasizes trustworthy AI characteristics:
    - Valid and Reliable
    - Safe
    - Secure and Resilient
    - Accountable and Transparent
    - Explainable and Interpretable
    - Privacy-Enhanced
    - Fair with Harmful Bias Managed

    Example:
        >>> framework = NISTAIRMFFramework()
        >>> result = await framework.check(entry, profile)
        >>> if not result.is_compliant:
        ...     for violation in result.violations:
        ...         print(f"{violation.rule_id}: {violation.description}")
    """

    def __init__(self):
        """Initialize the NIST AI RMF framework with all defined rules."""
        rules = self._create_rules()
        super().__init__(name="NIST AI RMF", version="1.0", rules=rules)

    def _create_rules(self) -> List[ComplianceRule]:
        """
        Create all NIST AI RMF compliance rules.

        Returns:
            List of ComplianceRule objects representing NIST AI RMF requirements
        """
        return [
            # ================================================================
            # GOVERN Function - Organizational Governance
            # ================================================================
            ComplianceRule(
                rule_id="NIST-GOV-1",
                name="AI Risk Management Governance Structure",
                description=(
                    "Organizations should establish and maintain AI risk management "
                    "governance structures that define clear accountability, roles, "
                    "and decision-making processes. Governance includes policies, "
                    "processes, and procedures to manage AI risks and opportunities "
                    "throughout the AI lifecycle. Senior leadership should demonstrate "
                    "commitment to AI risk management through resource allocation and "
                    "organizational culture. (GOVERN 1.1, 1.2, 1.3)"
                ),
                severity=RiskLevel.HIGH,
                category="governance",
                remediation=(
                    "Establish an AI governance committee or designate responsible "
                    "leadership. Document AI governance policies and procedures. "
                    "Ensure governance structures are integrated with enterprise "
                    "risk management. Define escalation paths for AI-related decisions."
                ),
                references=[
                    "NIST AI RMF GOVERN 1.1",
                    "NIST AI RMF GOVERN 1.2",
                    "NIST AI RMF GOVERN 1.3",
                    "NIST AI 100-1 Section 3",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-GOV-2",
                name="Organizational AI Principles and Values",
                description=(
                    "Organizations should document and communicate AI principles and "
                    "values that guide AI development and deployment decisions. These "
                    "principles should address trustworthy AI characteristics including "
                    "fairness, accountability, transparency, privacy, safety, and "
                    "security. Principles should be operationalized through specific "
                    "policies and integrated into organizational processes. "
                    "(GOVERN 1.4, 1.5)"
                ),
                severity=RiskLevel.MEDIUM,
                category="governance",
                remediation=(
                    "Develop and document organizational AI principles aligned with "
                    "trustworthy AI characteristics. Communicate principles to all "
                    "stakeholders. Create mechanisms to operationalize principles in "
                    "AI development and deployment processes. Regularly review and "
                    "update principles based on evolving standards and learnings."
                ),
                references=[
                    "NIST AI RMF GOVERN 1.4",
                    "NIST AI RMF GOVERN 1.5",
                    "NIST AI 100-1 Appendix A",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-GOV-3",
                name="Roles and Responsibilities Defined",
                description=(
                    "Organizations should clearly define and document roles and "
                    "responsibilities for AI risk management across the AI lifecycle. "
                    "This includes designating individuals or teams responsible for "
                    "AI governance, risk assessment, monitoring, and incident response. "
                    "Responsibilities should span development, deployment, and "
                    "decommissioning phases. (GOVERN 2.1, 2.2)"
                ),
                severity=RiskLevel.HIGH,
                category="governance",
                remediation=(
                    "Document specific roles and responsibilities for AI risk management. "
                    "Assign accountability for each phase of the AI lifecycle. Ensure "
                    "cross-functional representation in AI governance. Define clear "
                    "escalation procedures and decision authority. Provide training "
                    "appropriate to assigned responsibilities."
                ),
                references=[
                    "NIST AI RMF GOVERN 2.1",
                    "NIST AI RMF GOVERN 2.2",
                    "NIST AI 100-1 Section 3",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-GOV-4",
                name="Third-Party AI Risk Management",
                description=(
                    "Organizations should establish processes to assess and manage "
                    "risks from third-party AI components, including AI services, "
                    "models, data, and infrastructure. Due diligence should be "
                    "conducted on third-party AI providers. Contracts should address "
                    "AI risk management requirements, and third-party risks should be "
                    "monitored throughout the relationship. (GOVERN 6.1, 6.2)"
                ),
                severity=RiskLevel.HIGH,
                category="governance",
                remediation=(
                    "Implement third-party AI risk assessment processes. Include AI "
                    "risk requirements in vendor contracts and SLAs. Conduct due "
                    "diligence on AI providers including model provenance and data "
                    "practices. Establish ongoing monitoring of third-party AI "
                    "performance and compliance. Maintain inventory of third-party "
                    "AI dependencies."
                ),
                references=[
                    "NIST AI RMF GOVERN 6.1",
                    "NIST AI RMF GOVERN 6.2",
                    "NIST AI 100-1 Section 3",
                ],
            ),
            # ================================================================
            # MAP Function - Context and Risk Identification
            # ================================================================
            ComplianceRule(
                rule_id="NIST-MAP-1",
                name="AI System Context Established",
                description=(
                    "Organizations should establish and document the context for "
                    "AI systems including the operating environment, stakeholders, "
                    "and potential impacts. Context includes organizational goals, "
                    "intended users, deployment environment, and societal context. "
                    "Understanding context is essential for identifying and assessing "
                    "AI risks appropriately. (MAP 1.1, 1.2, 1.3)"
                ),
                severity=RiskLevel.MEDIUM,
                category="context",
                remediation=(
                    "Document the AI system's intended operating environment and "
                    "deployment context. Identify all stakeholders including direct "
                    "users, affected individuals, and oversight bodies. Analyze "
                    "organizational, technical, and societal context factors. "
                    "Assess how context may change over the system lifecycle."
                ),
                references=[
                    "NIST AI RMF MAP 1.1",
                    "NIST AI RMF MAP 1.2",
                    "NIST AI RMF MAP 1.3",
                    "NIST AI 100-1 Section 4",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MAP-2",
                name="AI Categorization and Intended Use Documented",
                description=(
                    "Organizations should categorize AI systems and document their "
                    "intended use, including the specific tasks the AI is designed "
                    "to perform, the target users, and the decision-making contexts. "
                    "Documentation should address potential misuse scenarios and "
                    "out-of-scope applications. Limitations and constraints should "
                    "be clearly specified. (MAP 2.1, 2.2, 2.3)"
                ),
                severity=RiskLevel.HIGH,
                category="context",
                remediation=(
                    "Create comprehensive documentation of AI system purpose and "
                    "intended use cases. Categorize the AI system based on risk "
                    "factors and application domain. Document known limitations, "
                    "constraints, and out-of-scope uses. Specify conditions under "
                    "which the AI should and should not be used."
                ),
                references=[
                    "NIST AI RMF MAP 2.1",
                    "NIST AI RMF MAP 2.2",
                    "NIST AI RMF MAP 2.3",
                    "NIST AI 100-1 Section 4",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MAP-3",
                name="AI Benefits and Costs Assessed",
                description=(
                    "Organizations should assess and document the benefits and costs "
                    "of AI systems, including potential positive and negative impacts "
                    "on individuals, organizations, communities, and society. Assessment "
                    "should consider both intended outcomes and unintended consequences. "
                    "Trade-offs between benefits and risks should be analyzed and "
                    "documented. (MAP 3.1, 3.2)"
                ),
                severity=RiskLevel.MEDIUM,
                category="context",
                remediation=(
                    "Conduct benefit-cost analysis for AI systems including tangible "
                    "and intangible impacts. Document potential positive outcomes and "
                    "risks to different stakeholder groups. Analyze trade-offs and "
                    "document decision rationale. Consider long-term and systemic "
                    "effects. Re-evaluate periodically as context changes."
                ),
                references=[
                    "NIST AI RMF MAP 3.1",
                    "NIST AI RMF MAP 3.2",
                    "NIST AI 100-1 Section 4",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MAP-4",
                name="Risks from Third-Party Components Mapped",
                description=(
                    "Organizations should identify and map risks arising from "
                    "third-party AI components including pre-trained models, datasets, "
                    "APIs, and cloud services. Risk mapping should address model "
                    "provenance, data quality, supply chain integrity, and dependency "
                    "risks. Organizations should understand how third-party components "
                    "affect overall system trustworthiness. (MAP 4.1, 4.2)"
                ),
                severity=RiskLevel.HIGH,
                category="risk_identification",
                remediation=(
                    "Maintain inventory of all third-party AI components and data "
                    "sources. Assess risks associated with each third-party dependency "
                    "including provenance, quality, and support continuity. Document "
                    "how third-party components affect system behavior and risk profile. "
                    "Establish processes for evaluating new third-party AI components."
                ),
                references=[
                    "NIST AI RMF MAP 4.1",
                    "NIST AI RMF MAP 4.2",
                    "NIST AI 100-1 Section 4",
                ],
            ),
            # ================================================================
            # MEASURE Function - Risk Analysis
            # ================================================================
            ComplianceRule(
                rule_id="NIST-MEAS-1",
                name="Appropriate Metrics Identified",
                description=(
                    "Organizations should identify and implement appropriate metrics "
                    "for measuring AI system performance, trustworthiness characteristics, "
                    "and risks. Metrics should be relevant to the AI system context, "
                    "measurable, and aligned with organizational goals. Measurement "
                    "approaches should be documented and validated for reliability. "
                    "(MEASURE 1.1, 1.2, 1.3)"
                ),
                severity=RiskLevel.MEDIUM,
                category="measurement",
                remediation=(
                    "Define metrics for each trustworthy AI characteristic relevant "
                    "to the system. Establish baselines and thresholds for acceptable "
                    "performance. Document measurement methodologies and their "
                    "limitations. Validate metrics are meaningful for the intended "
                    "context. Review and update metrics as system context evolves."
                ),
                references=[
                    "NIST AI RMF MEASURE 1.1",
                    "NIST AI RMF MEASURE 1.2",
                    "NIST AI RMF MEASURE 1.3",
                    "NIST AI 100-1 Section 5",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MEAS-2",
                name="AI Systems Evaluated for Trustworthy Characteristics",
                description=(
                    "Organizations should evaluate AI systems against trustworthy AI "
                    "characteristics including validity, reliability, safety, security, "
                    "resilience, accountability, transparency, explainability, "
                    "interpretability, privacy protection, and fairness. Evaluations "
                    "should be conducted throughout the AI lifecycle using appropriate "
                    "testing and assessment methods. (MEASURE 2.1, 2.2, 2.3)"
                ),
                severity=RiskLevel.HIGH,
                category="measurement",
                remediation=(
                    "Implement evaluation processes for trustworthy AI characteristics. "
                    "Conduct testing for accuracy, robustness, fairness, and other "
                    "relevant characteristics. Document evaluation results and track "
                    "trends over time. Use multiple evaluation methods appropriate to "
                    "each characteristic. Address identified gaps through system "
                    "improvements or risk mitigations."
                ),
                references=[
                    "NIST AI RMF MEASURE 2.1",
                    "NIST AI RMF MEASURE 2.2",
                    "NIST AI RMF MEASURE 2.3",
                    "NIST AI 100-1 Section 5",
                    "NIST AI 100-1 Appendix B",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MEAS-3",
                name="Mechanisms for Tracking Identified Risks",
                description=(
                    "Organizations should establish mechanisms for tracking identified "
                    "AI risks throughout the system lifecycle. Risk tracking should "
                    "include monitoring of risk indicators, documentation of risk "
                    "status changes, and communication of risk information to relevant "
                    "stakeholders. Risk tracking should be integrated with broader "
                    "organizational risk management processes. (MEASURE 3.1, 3.2, 3.3)"
                ),
                severity=RiskLevel.MEDIUM,
                category="measurement",
                remediation=(
                    "Implement risk tracking systems or integrate with existing risk "
                    "management tools. Define risk indicators and monitoring processes. "
                    "Establish regular risk review cadence. Document risk status and "
                    "changes over time. Create communication processes for risk "
                    "information sharing with relevant stakeholders."
                ),
                references=[
                    "NIST AI RMF MEASURE 3.1",
                    "NIST AI RMF MEASURE 3.2",
                    "NIST AI RMF MEASURE 3.3",
                    "NIST AI 100-1 Section 5",
                ],
            ),
            # ================================================================
            # MANAGE Function - Risk Treatment
            # ================================================================
            ComplianceRule(
                rule_id="NIST-MAN-1",
                name="AI Risks Prioritized and Responded To",
                description=(
                    "Organizations should prioritize AI risks based on their likelihood "
                    "and potential impact, and develop appropriate risk responses. "
                    "Risk responses may include risk avoidance, mitigation, transfer, "
                    "or acceptance. Resource allocation for risk treatment should align "
                    "with risk priorities. Risk response decisions should be documented "
                    "and communicated. (MANAGE 1.1, 1.2, 1.3)"
                ),
                severity=RiskLevel.HIGH,
                category="risk_treatment",
                remediation=(
                    "Establish risk prioritization criteria and processes. Document "
                    "risk response decisions including rationale. Allocate resources "
                    "proportionate to risk priority. Implement risk mitigation measures "
                    "and track effectiveness. Review and adjust risk responses based "
                    "on changing conditions and new information."
                ),
                references=[
                    "NIST AI RMF MANAGE 1.1",
                    "NIST AI RMF MANAGE 1.2",
                    "NIST AI RMF MANAGE 1.3",
                    "NIST AI 100-1 Section 6",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MAN-2",
                name="AI System Deployment Decisions Documented",
                description=(
                    "Organizations should document deployment decisions for AI systems "
                    "including the criteria used, risks considered, and approval process. "
                    "Deployment decisions should consider whether risks have been "
                    "adequately addressed and whether appropriate safeguards are in "
                    "place. Staged deployment approaches should be considered for "
                    "high-risk systems. (MANAGE 2.1, 2.2)"
                ),
                severity=RiskLevel.HIGH,
                category="risk_treatment",
                remediation=(
                    "Establish deployment decision criteria and approval processes. "
                    "Document risk assessment results informing deployment decisions. "
                    "Implement staged deployment approaches where appropriate. Define "
                    "conditions for full deployment, limited deployment, or non-deployment. "
                    "Document deployment decisions and supporting rationale."
                ),
                references=[
                    "NIST AI RMF MANAGE 2.1",
                    "NIST AI RMF MANAGE 2.2",
                    "NIST AI 100-1 Section 6",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MAN-3",
                name="Post-Deployment Monitoring in Place",
                description=(
                    "Organizations should implement post-deployment monitoring for "
                    "AI systems to detect performance degradation, emerging risks, "
                    "and unintended impacts. Monitoring should cover system performance, "
                    "user feedback, and environmental changes that may affect risk. "
                    "Monitoring findings should trigger appropriate review and response "
                    "processes. (MANAGE 3.1, 3.2)"
                ),
                severity=RiskLevel.HIGH,
                category="risk_treatment",
                remediation=(
                    "Implement monitoring systems for deployed AI applications. Define "
                    "metrics and thresholds for detecting performance issues. Establish "
                    "processes for collecting and analyzing user feedback. Monitor for "
                    "data drift, concept drift, and environmental changes. Create "
                    "escalation procedures for monitoring alerts."
                ),
                references=[
                    "NIST AI RMF MANAGE 3.1",
                    "NIST AI RMF MANAGE 3.2",
                    "NIST AI 100-1 Section 6",
                ],
            ),
            ComplianceRule(
                rule_id="NIST-MAN-4",
                name="Incident Response and Recovery Procedures",
                description=(
                    "Organizations should establish incident response and recovery "
                    "procedures for AI-related incidents including system failures, "
                    "security breaches, safety incidents, and harmful outputs. Procedures "
                    "should address incident detection, containment, investigation, "
                    "remediation, and communication. Lessons learned should inform "
                    "system improvements and risk management updates. (MANAGE 4.1, 4.2, 4.3)"
                ),
                severity=RiskLevel.CRITICAL,
                category="risk_treatment",
                remediation=(
                    "Develop AI-specific incident response procedures. Define incident "
                    "severity levels and response protocols. Establish incident "
                    "communication plans for internal and external stakeholders. "
                    "Implement procedures for system rollback or shutdown when needed. "
                    "Conduct post-incident reviews and update risk management based "
                    "on lessons learned."
                ),
                references=[
                    "NIST AI RMF MANAGE 4.1",
                    "NIST AI RMF MANAGE 4.2",
                    "NIST AI RMF MANAGE 4.3",
                    "NIST AI 100-1 Section 6",
                ],
            ),
        ]

    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single NIST AI RMF rule against an audit entry.

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
        if rule.rule_id == "NIST-GOV-1":
            return self._check_governance_structure(entry, rule)
        elif rule.rule_id == "NIST-GOV-2":
            return self._check_ai_principles(entry, rule)
        elif rule.rule_id == "NIST-GOV-3":
            return self._check_roles_responsibilities(entry, rule)
        elif rule.rule_id == "NIST-GOV-4":
            return self._check_third_party_governance(entry, rule)
        elif rule.rule_id == "NIST-MAP-1":
            return self._check_system_context(entry, rule)
        elif rule.rule_id == "NIST-MAP-2":
            return self._check_categorization_documented(entry, rule)
        elif rule.rule_id == "NIST-MAP-3":
            return self._check_benefits_costs_assessed(entry, rule)
        elif rule.rule_id == "NIST-MAP-4":
            return self._check_third_party_risks_mapped(entry, rule)
        elif rule.rule_id == "NIST-MEAS-1":
            return self._check_metrics_identified(entry, rule)
        elif rule.rule_id == "NIST-MEAS-2":
            return self._check_trustworthy_evaluation(entry, rule)
        elif rule.rule_id == "NIST-MEAS-3":
            return self._check_risk_tracking(entry, rule)
        elif rule.rule_id == "NIST-MAN-1":
            return self._check_risk_prioritization(entry, rule)
        elif rule.rule_id == "NIST-MAN-2":
            return self._check_deployment_decisions(entry, rule)
        elif rule.rule_id == "NIST-MAN-3":
            return self._check_post_deployment_monitoring(entry, rule)
        elif rule.rule_id == "NIST-MAN-4":
            return self._check_incident_response(entry, rule)

        return None

    # ========================================================================
    # GOVERN Function Checks
    # ========================================================================

    def _check_governance_structure(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-GOV-1: AI risk management governance structure required.

        High-risk AI operations must have documented governance oversight.
        This is evaluated based on the risk_level and governance metadata.
        """
        # Only applies to high-risk operations
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        has_governance = entry.metadata.get("governance_documented", False)
        has_approval = entry.metadata.get("governance_approval", False)

        if not (has_governance or has_approval):
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (level={entry.risk_level.value}) performed "
                f"without documented AI governance structure or approval",
            )
        return None

    def _check_ai_principles(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-GOV-2: Organizational AI principles and values documented.

        Operations involving significant AI decisions should reference
        organizational AI principles.
        """
        # Check for significant decision-making operations
        decision_events = {"deployment", "model_selection", "training", "policy_update"}
        if entry.event_type.lower() not in decision_events:
            return None

        has_principles_ref = entry.metadata.get("ai_principles_aligned", False)
        if not has_principles_ref:
            return self._create_violation(
                entry,
                rule,
                f"AI decision operation (type={entry.event_type}) performed "
                f"without reference to organizational AI principles",
            )
        return None

    def _check_roles_responsibilities(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-GOV-3: Roles and responsibilities defined.

        High-risk operations must have clear accountability documented.
        """
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        has_owner = bool(entry.actor and entry.actor != "system")
        has_accountability = entry.metadata.get("accountability_documented", False)

        if not (has_owner or has_accountability):
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (level={entry.risk_level.value}) performed "
                f"without clear accountability or responsible party documented",
            )
        return None

    def _check_third_party_governance(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-GOV-4: Third-party AI risk management.

        Operations involving third-party AI components must have
        appropriate risk governance.
        """
        # Check if this involves third-party components
        third_party_events = {
            "api_call", "external_model", "third_party_inference",
            "vendor_integration", "model_import"
        }
        if entry.event_type.lower() not in third_party_events:
            return None

        has_third_party_assessment = entry.metadata.get("third_party_assessed", False)
        has_vendor_agreement = entry.metadata.get("vendor_agreement_documented", False)

        if not (has_third_party_assessment or has_vendor_agreement):
            return self._create_violation(
                entry,
                rule,
                f"Third-party AI operation (type={entry.event_type}) performed "
                f"without documented third-party risk assessment",
            )
        return None

    # ========================================================================
    # MAP Function Checks
    # ========================================================================

    def _check_system_context(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAP-1: AI system context established.

        New deployments and significant system changes must have
        documented context.
        """
        context_events = {"deployment", "system_change", "environment_update"}
        if entry.event_type.lower() not in context_events:
            return None

        has_context = entry.metadata.get("system_context_documented", False)
        if not has_context:
            return self._create_violation(
                entry,
                rule,
                f"System operation (type={entry.event_type}) performed "
                f"without documented AI system context",
            )
        return None

    def _check_categorization_documented(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAP-2: AI categorization and intended use documented.

        Deployment and training operations must have categorization
        and intended use documentation.
        """
        significant_events = {"deployment", "training", "fine_tuning", "model_release"}
        if entry.event_type.lower() not in significant_events:
            return None

        has_categorization = entry.metadata.get("ai_categorization_documented", False)
        has_intended_use = entry.metadata.get("intended_use_documented", False)

        if not (has_categorization or has_intended_use or entry.documentation_ref):
            return self._create_violation(
                entry,
                rule,
                f"Significant operation (type={entry.event_type}) performed "
                f"without documented AI categorization or intended use",
            )
        return None

    def _check_benefits_costs_assessed(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAP-3: AI benefits and costs assessed.

        Deployment decisions should include benefit-cost assessment.
        """
        # Only check deployment-related events
        if entry.event_type.lower() != "deployment":
            return None

        has_assessment = entry.metadata.get("benefit_cost_assessed", False)
        has_impact_analysis = entry.metadata.get("impact_analysis_documented", False)

        if not (has_assessment or has_impact_analysis):
            return self._create_violation(
                entry,
                rule,
                f"Deployment operation performed without documented "
                f"benefit-cost or impact assessment",
            )
        return None

    def _check_third_party_risks_mapped(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAP-4: Risks from third-party components mapped.

        Operations using third-party AI must have risks identified.
        """
        third_party_events = {
            "api_call", "external_model", "third_party_inference",
            "vendor_integration", "model_import", "data_import"
        }
        if entry.event_type.lower() not in third_party_events:
            return None

        has_risk_mapping = entry.metadata.get("third_party_risks_mapped", False)
        has_component_inventory = entry.metadata.get("component_inventory_updated", False)

        if not (has_risk_mapping or has_component_inventory):
            return self._create_violation(
                entry,
                rule,
                f"Third-party operation (type={entry.event_type}) performed "
                f"without documented risk mapping for third-party components",
            )
        return None

    # ========================================================================
    # MEASURE Function Checks
    # ========================================================================

    def _check_metrics_identified(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MEAS-1: Appropriate metrics identified.

        Performance and risk-related operations should reference
        defined metrics.
        """
        metric_events = {
            "inference", "evaluation", "testing", "monitoring",
            "performance_review"
        }
        if entry.event_type.lower() not in metric_events:
            return None

        has_metrics = entry.metadata.get("metrics_documented", False)
        has_baseline = entry.metadata.get("baseline_established", False)

        if not (has_metrics or has_baseline):
            return self._create_violation(
                entry,
                rule,
                f"Measurement operation (type={entry.event_type}) performed "
                f"without reference to documented metrics",
            )
        return None

    def _check_trustworthy_evaluation(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MEAS-2: AI systems evaluated for trustworthy characteristics.

        Significant operations should include trustworthiness evaluation.
        """
        # Only applies to high-risk operations and significant events
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        evaluation_events = {
            "deployment", "inference", "training", "evaluation",
            "model_update", "testing"
        }
        if entry.event_type.lower() not in evaluation_events:
            return None

        has_trustworthy_eval = entry.metadata.get("trustworthiness_evaluated", False)
        has_fairness_check = entry.metadata.get("fairness_assessed", False)
        has_safety_check = entry.metadata.get("safety_evaluated", False)

        if not (has_trustworthy_eval or has_fairness_check or has_safety_check):
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (type={entry.event_type}) performed "
                f"without trustworthy AI characteristics evaluation",
            )
        return None

    def _check_risk_tracking(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MEAS-3: Mechanisms for tracking identified risks.

        High-risk operations should have risk tracking in place.
        """
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        has_risk_tracking = entry.metadata.get("risk_tracked", False)
        has_risk_registry = entry.metadata.get("risk_registry_updated", False)

        if not (has_risk_tracking or has_risk_registry):
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (level={entry.risk_level.value}) performed "
                f"without documented risk tracking mechanism",
            )
        return None

    # ========================================================================
    # MANAGE Function Checks
    # ========================================================================

    def _check_risk_prioritization(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAN-1: AI risks prioritized and responded to.

        High-risk operations should have prioritized risk response.
        """
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        has_risk_response = entry.metadata.get("risk_response_documented", False)
        has_prioritization = entry.metadata.get("risk_prioritized", False)
        has_risk_assessment = entry.metadata.get("risk_assessment_documented", False)

        if not (has_risk_response or has_prioritization or has_risk_assessment):
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (level={entry.risk_level.value}) performed "
                f"without documented risk prioritization or response",
            )
        return None

    def _check_deployment_decisions(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAN-2: AI system deployment decisions documented.

        Deployment operations must have documented decision rationale.
        """
        if entry.event_type.lower() != "deployment":
            return None

        has_decision_doc = entry.metadata.get("deployment_decision_documented", False)
        has_approval = entry.metadata.get("deployment_approved", False)

        if not (has_decision_doc or has_approval or entry.documentation_ref):
            return self._create_violation(
                entry,
                rule,
                f"Deployment operation performed without documented "
                f"deployment decision or approval",
            )
        return None

    def _check_post_deployment_monitoring(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAN-3: Post-deployment monitoring in place.

        Production operations should have monitoring documented.
        """
        production_events = {
            "inference", "prediction", "completion", "production_query",
            "user_interaction"
        }
        if entry.event_type.lower() not in production_events:
            return None

        # Only check for operations that should be monitored
        has_monitoring = entry.metadata.get("monitoring_enabled", False)
        has_performance_tracking = entry.metadata.get("performance_tracked", False)

        if not (has_monitoring or has_performance_tracking):
            return self._create_violation(
                entry,
                rule,
                f"Production operation (type={entry.event_type}) performed "
                f"without documented post-deployment monitoring",
            )
        return None

    def _check_incident_response(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check NIST-MAN-4: Incident response and recovery procedures.

        Error and incident events must have response procedures.
        """
        incident_events = {
            "incident", "error", "failure", "security_event",
            "safety_incident", "model_failure", "system_error"
        }
        if entry.event_type.lower() not in incident_events:
            return None

        has_incident_response = entry.metadata.get("incident_response_followed", False)
        has_recovery_plan = entry.metadata.get("recovery_plan_executed", False)
        has_incident_documented = entry.metadata.get("incident_documented", False)

        if not (has_incident_response or has_recovery_plan or has_incident_documented):
            return self._create_violation(
                entry,
                rule,
                f"Incident event (type={entry.event_type}) without documented "
                f"incident response or recovery procedure",
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
