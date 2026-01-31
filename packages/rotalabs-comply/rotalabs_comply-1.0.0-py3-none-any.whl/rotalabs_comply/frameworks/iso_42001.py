"""
ISO/IEC 42001:2023 AI Management System compliance framework implementation.

ISO/IEC 42001:2023 is the international standard for AI management systems (AIMS).
It provides a framework for organizations to establish, implement, maintain, and
continually improve an AI management system. The standard adopts a process approach
and is compatible with other ISO management system standards.

This framework implements checks based on the standard's key clauses:
- Clause 4: Context of the Organization
- Clause 5: Leadership
- Clause 6: Planning
- Clause 7: Support
- Clause 8: Operation
- Clause 9: Performance Evaluation
- Clause 10: Improvement

Categories:
- context: Rules related to organizational context and scope (Clause 4)
- leadership: Rules for leadership commitment and governance (Clause 5)
- planning: Rules for risk assessment and objectives (Clause 6)
- support: Rules for resources, competence, and documentation (Clause 7)
- operation: Rules for operational planning and AI lifecycle (Clause 8)
- performance: Rules for monitoring, auditing, and review (Clause 9)
- improvement: Rules for nonconformity and continual improvement (Clause 10)

Reference: https://www.iso.org/standard/81230.html
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


class ISO42001Framework(BaseFramework):
    """
    ISO/IEC 42001:2023 AI Management System compliance framework.

    Implements compliance checks based on ISO 42001:2023 requirements for
    establishing, implementing, maintaining, and continually improving an
    AI management system. The framework evaluates audit entries against
    the standard's requirements across seven key areas.

    ISO 42001 is structured around the Plan-Do-Check-Act (PDCA) cycle:
    - Plan: Establish AIMS objectives and processes (Clauses 4-6)
    - Do: Implement the AIMS and its processes (Clauses 7-8)
    - Check: Monitor and evaluate performance (Clause 9)
    - Act: Take actions to improve performance (Clause 10)

    The standard emphasizes:
    - Risk-based thinking throughout the AI lifecycle
    - Responsible AI development and deployment
    - Transparency and accountability
    - Continual improvement

    Example:
        >>> framework = ISO42001Framework()
        >>> result = await framework.check(entry, profile)
        >>> if not result.is_compliant:
        ...     for violation in result.violations:
        ...         print(f"{violation.rule_id}: {violation.description}")
    """

    def __init__(self):
        """Initialize the ISO 42001 framework with all defined rules."""
        rules = self._create_rules()
        super().__init__(name="ISO/IEC 42001", version="2023", rules=rules)

    def _create_rules(self) -> List[ComplianceRule]:
        """
        Create all ISO 42001 compliance rules.

        Returns:
            List of ComplianceRule objects representing ISO 42001 requirements
        """
        return [
            # =================================================================
            # Clause 4: Context of the Organization
            # =================================================================
            ComplianceRule(
                rule_id="ISO42001-4.1",
                name="Understanding Organization and Context",
                description=(
                    "The organization shall determine external and internal issues that "
                    "are relevant to its purpose and that affect its ability to achieve "
                    "the intended outcome(s) of its AI management system. This includes "
                    "understanding the organization's role as an AI provider, deployer, "
                    "or other relevant stakeholder, and the applicable legal, regulatory, "
                    "and contractual requirements. (Clause 4.1)"
                ),
                severity=RiskLevel.HIGH,
                category="context",
                remediation=(
                    "Document the organizational context including: internal factors "
                    "(governance structure, capabilities, culture), external factors "
                    "(legal/regulatory environment, technology trends, stakeholder "
                    "expectations), and the organization's role in the AI value chain."
                ),
                references=["ISO/IEC 42001:2023 Clause 4.1"],
            ),
            ComplianceRule(
                rule_id="ISO42001-4.2",
                name="Understanding Needs of Interested Parties",
                description=(
                    "The organization shall determine the interested parties that are "
                    "relevant to the AI management system, the relevant requirements of "
                    "these interested parties, and which of these requirements will be "
                    "addressed through the AIMS. Interested parties may include customers, "
                    "regulators, employees, AI system users, and affected communities. "
                    "(Clause 4.2)"
                ),
                severity=RiskLevel.HIGH,
                category="context",
                remediation=(
                    "Identify and document all relevant interested parties and their "
                    "requirements. Create a stakeholder register that includes: party "
                    "identification, their needs and expectations, relevance to AIMS, "
                    "and how requirements will be addressed."
                ),
                references=["ISO/IEC 42001:2023 Clause 4.2"],
            ),
            ComplianceRule(
                rule_id="ISO42001-4.3",
                name="Scope of AIMS Determined",
                description=(
                    "The organization shall determine the boundaries and applicability "
                    "of the AI management system to establish its scope. The scope shall "
                    "be available as documented information. When determining the scope, "
                    "the organization shall consider the internal and external issues, "
                    "requirements of interested parties, and interfaces with other "
                    "management systems. (Clause 4.3)"
                ),
                severity=RiskLevel.HIGH,
                category="context",
                remediation=(
                    "Define and document the AIMS scope including: organizational units "
                    "covered, AI systems included, physical locations, processes within "
                    "scope, and any exclusions with justification. Ensure the scope "
                    "statement is available to relevant interested parties."
                ),
                references=["ISO/IEC 42001:2023 Clause 4.3"],
            ),
            # =================================================================
            # Clause 5: Leadership
            # =================================================================
            ComplianceRule(
                rule_id="ISO42001-5.1",
                name="Leadership Commitment Demonstrated",
                description=(
                    "Top management shall demonstrate leadership and commitment to the "
                    "AI management system by ensuring the AI policy and objectives are "
                    "established and compatible with strategic direction, ensuring "
                    "integration into business processes, ensuring resources are available, "
                    "communicating importance of effective AIMS, and promoting continual "
                    "improvement. (Clause 5.1)"
                ),
                severity=RiskLevel.HIGH,
                category="leadership",
                remediation=(
                    "Document evidence of top management commitment including: meeting "
                    "minutes showing AIMS discussions, resource allocation decisions, "
                    "communication materials, and management review participation. "
                    "Leadership must actively champion responsible AI practices."
                ),
                references=["ISO/IEC 42001:2023 Clause 5.1"],
            ),
            ComplianceRule(
                rule_id="ISO42001-5.2",
                name="AI Policy Established",
                description=(
                    "Top management shall establish an AI policy that is appropriate to "
                    "the organization's purpose, provides a framework for setting AI "
                    "objectives, includes a commitment to satisfy applicable requirements, "
                    "includes a commitment to continual improvement, and addresses "
                    "responsible AI principles including transparency, fairness, and "
                    "accountability. (Clause 5.2)"
                ),
                severity=RiskLevel.CRITICAL,
                category="leadership",
                remediation=(
                    "Develop and publish an AI policy that: aligns with organizational "
                    "strategy, establishes responsible AI principles, commits to "
                    "compliance and improvement, is communicated throughout the "
                    "organization, and is available to interested parties as appropriate."
                ),
                references=["ISO/IEC 42001:2023 Clause 5.2"],
            ),
            ComplianceRule(
                rule_id="ISO42001-5.3",
                name="Roles and Responsibilities Assigned",
                description=(
                    "Top management shall ensure that the responsibilities and authorities "
                    "for relevant roles are assigned and communicated within the "
                    "organization. This includes assigning responsibility for ensuring "
                    "AIMS conformance to ISO 42001 and reporting on AIMS performance. "
                    "(Clause 5.3)"
                ),
                severity=RiskLevel.HIGH,
                category="leadership",
                remediation=(
                    "Define and document roles related to AI governance including: AIMS "
                    "owner/manager, AI ethics officer, risk owners, system owners, and "
                    "oversight committees. Create RACI matrices for AI-related processes "
                    "and communicate assignments to all relevant personnel."
                ),
                references=["ISO/IEC 42001:2023 Clause 5.3"],
            ),
            # =================================================================
            # Clause 6: Planning
            # =================================================================
            ComplianceRule(
                rule_id="ISO42001-6.1",
                name="AI Risk Assessment Conducted",
                description=(
                    "The organization shall plan and implement a process to identify, "
                    "analyze, and evaluate AI-related risks. The risk assessment shall "
                    "consider risks to the organization, to individuals, to groups, and "
                    "to society arising from AI system development and use. Risk criteria "
                    "shall be established and maintained. (Clause 6.1)"
                ),
                severity=RiskLevel.CRITICAL,
                category="planning",
                remediation=(
                    "Implement a comprehensive AI risk assessment process that: defines "
                    "risk criteria and acceptance thresholds, identifies AI-specific risks "
                    "(bias, safety, privacy, security), evaluates likelihood and impact, "
                    "documents risk treatment decisions, and maintains a risk register."
                ),
                references=["ISO/IEC 42001:2023 Clause 6.1", "Annex A"],
            ),
            ComplianceRule(
                rule_id="ISO42001-6.2",
                name="AI Objectives Established",
                description=(
                    "The organization shall establish AI objectives at relevant functions, "
                    "levels, and processes. Objectives shall be consistent with the AI "
                    "policy, measurable, take into account applicable requirements, be "
                    "monitored, communicated, and updated as appropriate. Plans to achieve "
                    "objectives shall define what will be done, resources required, "
                    "responsibilities, timelines, and evaluation methods. (Clause 6.2)"
                ),
                severity=RiskLevel.HIGH,
                category="planning",
                remediation=(
                    "Define measurable AI objectives that support the AI policy. For each "
                    "objective, document: target metrics, responsible parties, required "
                    "resources, implementation timeline, and progress monitoring approach. "
                    "Review and update objectives regularly."
                ),
                references=["ISO/IEC 42001:2023 Clause 6.2"],
            ),
            ComplianceRule(
                rule_id="ISO42001-6.3",
                name="AI Impact Assessment Performed",
                description=(
                    "The organization shall perform AI system impact assessments to "
                    "identify and evaluate the potential impacts of AI systems on "
                    "individuals, groups, and society. The assessment shall consider "
                    "impacts throughout the AI system lifecycle including development, "
                    "deployment, use, and decommissioning. (Clause 6.1.4)"
                ),
                severity=RiskLevel.CRITICAL,
                category="planning",
                remediation=(
                    "Conduct impact assessments for AI systems covering: intended use "
                    "cases and users, potential beneficial and harmful impacts, effects "
                    "on fundamental rights and freedoms, environmental considerations, "
                    "and cumulative effects. Document assessment results and mitigation "
                    "measures."
                ),
                references=["ISO/IEC 42001:2023 Clause 6.1.4", "Annex B"],
            ),
            # =================================================================
            # Clause 7: Support
            # =================================================================
            ComplianceRule(
                rule_id="ISO42001-7.1",
                name="Resources Provided",
                description=(
                    "The organization shall determine and provide the resources needed "
                    "for the establishment, implementation, maintenance, and continual "
                    "improvement of the AI management system. This includes human "
                    "resources, infrastructure, technology, and financial resources "
                    "appropriate for the scale and complexity of AI operations. (Clause 7.1)"
                ),
                severity=RiskLevel.HIGH,
                category="support",
                remediation=(
                    "Document resource requirements for AIMS implementation including: "
                    "personnel allocation, training budgets, technology infrastructure, "
                    "tool procurement, and ongoing operational support. Ensure resource "
                    "planning is part of organizational budgeting processes."
                ),
                references=["ISO/IEC 42001:2023 Clause 7.1"],
            ),
            ComplianceRule(
                rule_id="ISO42001-7.2",
                name="Competence Ensured",
                description=(
                    "The organization shall determine the necessary competence of persons "
                    "doing work under its control that affects AI management system "
                    "performance, ensure these persons are competent on the basis of "
                    "appropriate education, training, or experience, take actions to "
                    "acquire the necessary competence, and retain documented evidence "
                    "of competence. (Clause 7.2)"
                ),
                severity=RiskLevel.HIGH,
                category="support",
                remediation=(
                    "Establish competency requirements for AI-related roles covering: "
                    "technical skills, ethical considerations, risk management, and "
                    "regulatory awareness. Implement training programs, maintain competency "
                    "matrices, and retain evidence of qualifications and training completion."
                ),
                references=["ISO/IEC 42001:2023 Clause 7.2"],
            ),
            ComplianceRule(
                rule_id="ISO42001-7.3",
                name="Awareness Maintained",
                description=(
                    "Persons doing work under the organization's control shall be aware "
                    "of the AI policy, their contribution to the AIMS effectiveness, the "
                    "implications of not conforming to AIMS requirements, and the "
                    "importance of responsible AI practices. (Clause 7.3)"
                ),
                severity=RiskLevel.MEDIUM,
                category="support",
                remediation=(
                    "Implement an awareness program that communicates: the AI policy and "
                    "its relevance, individual responsibilities, consequences of non-"
                    "conformance, and channels for raising concerns. Use multiple formats "
                    "including onboarding, regular communications, and refresher training."
                ),
                references=["ISO/IEC 42001:2023 Clause 7.3"],
            ),
            ComplianceRule(
                rule_id="ISO42001-7.4",
                name="Communication Processes Established",
                description=(
                    "The organization shall determine the internal and external "
                    "communications relevant to the AI management system including what "
                    "to communicate, when, with whom, how, and who is responsible. "
                    "Communication shall address both routine and incident-related "
                    "notifications. (Clause 7.4)"
                ),
                severity=RiskLevel.MEDIUM,
                category="support",
                remediation=(
                    "Define communication processes covering: stakeholder identification, "
                    "communication channels, frequency, content requirements, approval "
                    "workflows, and records retention. Include both internal (employees, "
                    "management) and external (regulators, customers, public) communications."
                ),
                references=["ISO/IEC 42001:2023 Clause 7.4"],
            ),
            ComplianceRule(
                rule_id="ISO42001-7.5",
                name="Documented Information Controlled",
                description=(
                    "The AI management system shall include documented information "
                    "required by ISO 42001 and determined by the organization as necessary "
                    "for AIMS effectiveness. Documented information shall be controlled to "
                    "ensure availability, suitability, and adequate protection including "
                    "distribution, access, retrieval, storage, and preservation. (Clause 7.5)"
                ),
                severity=RiskLevel.HIGH,
                category="support",
                remediation=(
                    "Implement document control procedures covering: identification and "
                    "format requirements, review and approval, version control, access "
                    "controls, retention periods, and disposal. Maintain a document register "
                    "and ensure documents are available to those who need them."
                ),
                references=["ISO/IEC 42001:2023 Clause 7.5"],
            ),
            # =================================================================
            # Clause 8: Operation
            # =================================================================
            ComplianceRule(
                rule_id="ISO42001-8.1",
                name="Operational Planning and Control",
                description=(
                    "The organization shall plan, implement, and control the processes "
                    "needed to meet AI management system requirements. This includes "
                    "establishing criteria for processes, implementing control of processes "
                    "in accordance with criteria, maintaining documented information to "
                    "have confidence processes are carried out as planned, and controlling "
                    "planned changes. (Clause 8.1)"
                ),
                severity=RiskLevel.HIGH,
                category="operation",
                remediation=(
                    "Document operational procedures for AI processes including: process "
                    "objectives and criteria, input/output specifications, roles and "
                    "responsibilities, monitoring requirements, and change control "
                    "procedures. Implement controls appropriate to process criticality."
                ),
                references=["ISO/IEC 42001:2023 Clause 8.1"],
            ),
            ComplianceRule(
                rule_id="ISO42001-8.2",
                name="AI System Lifecycle Processes",
                description=(
                    "The organization shall establish, implement, and maintain processes "
                    "for AI system lifecycle management including: design and development, "
                    "verification and validation, deployment, operation and monitoring, "
                    "and retirement/decommissioning. Processes shall address data "
                    "management, model development, and responsible AI considerations "
                    "throughout the lifecycle. (Clause 8.2)"
                ),
                severity=RiskLevel.CRITICAL,
                category="operation",
                remediation=(
                    "Define lifecycle processes covering: requirements analysis, data "
                    "acquisition and preparation, model development and training, testing "
                    "and validation, deployment and release, monitoring and maintenance, "
                    "and decommissioning. Include stage gates and approval requirements."
                ),
                references=["ISO/IEC 42001:2023 Clause 8.2", "Annex A.6"],
            ),
            ComplianceRule(
                rule_id="ISO42001-8.3",
                name="Third-Party Considerations",
                description=(
                    "The organization shall determine and apply criteria for the evaluation, "
                    "selection, monitoring, and re-evaluation of external providers of "
                    "AI-related products and services. The organization shall ensure that "
                    "externally provided processes, products, and services conform to "
                    "AIMS requirements. (Clause 8.3)"
                ),
                severity=RiskLevel.HIGH,
                category="operation",
                remediation=(
                    "Establish third-party management processes including: vendor "
                    "qualification criteria, contractual requirements, due diligence "
                    "procedures, ongoing monitoring, and performance evaluation. Address "
                    "AI-specific considerations such as model provenance and data handling."
                ),
                references=["ISO/IEC 42001:2023 Clause 8.3", "Annex A.8"],
            ),
            ComplianceRule(
                rule_id="ISO42001-8.4",
                name="AI System Impact Assessment",
                description=(
                    "The organization shall perform and document AI system impact "
                    "assessments prior to deployment and periodically during operation. "
                    "The assessment shall evaluate actual and potential impacts on "
                    "stakeholders, identifying both intended benefits and unintended "
                    "consequences. Assessment results shall inform risk treatment and "
                    "system modifications. (Clause 8.4)"
                ),
                severity=RiskLevel.CRITICAL,
                category="operation",
                remediation=(
                    "Conduct operational impact assessments that: identify affected "
                    "stakeholders, evaluate impact severity and likelihood, assess "
                    "cumulative effects, compare actual vs. expected outcomes, and "
                    "trigger reviews when significant changes occur. Document findings "
                    "and resulting actions."
                ),
                references=["ISO/IEC 42001:2023 Clause 8.4", "Annex B"],
            ),
            # =================================================================
            # Clause 9: Performance Evaluation
            # =================================================================
            ComplianceRule(
                rule_id="ISO42001-9.1",
                name="Monitoring and Measurement",
                description=(
                    "The organization shall determine what needs to be monitored and "
                    "measured, the methods for monitoring, measurement, analysis, and "
                    "evaluation, when monitoring and measuring shall be performed, when "
                    "results shall be analyzed and evaluated, and who shall analyze and "
                    "evaluate. The organization shall retain documented evidence of "
                    "monitoring and measurement results. (Clause 9.1)"
                ),
                severity=RiskLevel.HIGH,
                category="performance",
                remediation=(
                    "Define monitoring and measurement program including: key performance "
                    "indicators for AIMS effectiveness, AI system performance metrics, "
                    "measurement methods and tools, frequency of measurement, analysis "
                    "procedures, and reporting requirements. Establish baselines and targets."
                ),
                references=["ISO/IEC 42001:2023 Clause 9.1"],
            ),
            ComplianceRule(
                rule_id="ISO42001-9.2",
                name="Internal Audit Conducted",
                description=(
                    "The organization shall conduct internal audits at planned intervals "
                    "to provide information on whether the AIMS conforms to the "
                    "organization's own requirements and ISO 42001 requirements, and is "
                    "effectively implemented and maintained. The organization shall define "
                    "audit criteria, scope, frequency, and methods, and ensure objectivity "
                    "and impartiality of the audit process. (Clause 9.2)"
                ),
                severity=RiskLevel.HIGH,
                category="performance",
                remediation=(
                    "Establish an internal audit program that: defines audit scope and "
                    "criteria based on ISO 42001, schedules audits considering process "
                    "importance and previous results, ensures auditor competence and "
                    "independence, documents findings and corrective actions, and reports "
                    "results to management."
                ),
                references=["ISO/IEC 42001:2023 Clause 9.2"],
            ),
            ComplianceRule(
                rule_id="ISO42001-9.3",
                name="Management Review",
                description=(
                    "Top management shall review the AI management system at planned "
                    "intervals to ensure its continuing suitability, adequacy, and "
                    "effectiveness. The review shall consider status of actions from "
                    "previous reviews, changes in issues and requirements, AIMS "
                    "performance including nonconformities, monitoring results, audit "
                    "results, and opportunities for improvement. (Clause 9.3)"
                ),
                severity=RiskLevel.HIGH,
                category="performance",
                remediation=(
                    "Conduct management reviews that address: AIMS performance trends, "
                    "audit findings and corrective actions, stakeholder feedback, "
                    "resource adequacy, risk treatment effectiveness, and improvement "
                    "opportunities. Document review inputs, discussions, and decisions "
                    "including required actions."
                ),
                references=["ISO/IEC 42001:2023 Clause 9.3"],
            ),
            # =================================================================
            # Clause 10: Improvement
            # =================================================================
            ComplianceRule(
                rule_id="ISO42001-10.1",
                name="Nonconformity and Corrective Action",
                description=(
                    "When a nonconformity occurs, the organization shall react to the "
                    "nonconformity and take action to control and correct it, evaluate "
                    "the need for action to eliminate causes, implement any action needed, "
                    "review effectiveness of corrective action, and make changes to the "
                    "AIMS if necessary. The organization shall retain documented "
                    "information as evidence. (Clause 10.1)"
                ),
                severity=RiskLevel.HIGH,
                category="improvement",
                remediation=(
                    "Implement a corrective action process that: captures nonconformities "
                    "from multiple sources (audits, incidents, feedback), performs root "
                    "cause analysis, defines and implements corrections, verifies "
                    "effectiveness, and updates processes/documentation as needed. "
                    "Maintain a corrective action log."
                ),
                references=["ISO/IEC 42001:2023 Clause 10.1"],
            ),
            ComplianceRule(
                rule_id="ISO42001-10.2",
                name="Continual Improvement",
                description=(
                    "The organization shall continually improve the suitability, adequacy, "
                    "and effectiveness of the AI management system. This shall include "
                    "consideration of the results of analysis and evaluation, and outputs "
                    "from management review, to determine opportunities for improvement. "
                    "The organization shall take actions to improve AIMS performance and "
                    "responsible AI practices. (Clause 10.2)"
                ),
                severity=RiskLevel.MEDIUM,
                category="improvement",
                remediation=(
                    "Establish improvement mechanisms including: systematic collection "
                    "of improvement opportunities, prioritization based on impact and "
                    "feasibility, implementation planning, and tracking of improvement "
                    "initiatives. Promote a culture of continuous improvement in AI "
                    "governance and responsible AI practices."
                ),
                references=["ISO/IEC 42001:2023 Clause 10.2"],
            ),
        ]

    def _check_rule(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check a single ISO 42001 rule against an audit entry.

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
        if rule.rule_id == "ISO42001-4.1":
            return self._check_organizational_context(entry, rule)
        elif rule.rule_id == "ISO42001-4.2":
            return self._check_interested_parties(entry, rule)
        elif rule.rule_id == "ISO42001-4.3":
            return self._check_aims_scope(entry, rule)
        elif rule.rule_id == "ISO42001-5.1":
            return self._check_leadership_commitment(entry, rule)
        elif rule.rule_id == "ISO42001-5.2":
            return self._check_ai_policy(entry, rule)
        elif rule.rule_id == "ISO42001-5.3":
            return self._check_roles_responsibilities(entry, rule)
        elif rule.rule_id == "ISO42001-6.1":
            return self._check_risk_assessment(entry, rule)
        elif rule.rule_id == "ISO42001-6.2":
            return self._check_ai_objectives(entry, rule)
        elif rule.rule_id == "ISO42001-6.3":
            return self._check_impact_assessment(entry, rule)
        elif rule.rule_id == "ISO42001-7.1":
            return self._check_resources(entry, rule)
        elif rule.rule_id == "ISO42001-7.2":
            return self._check_competence(entry, rule)
        elif rule.rule_id == "ISO42001-7.3":
            return self._check_awareness(entry, rule)
        elif rule.rule_id == "ISO42001-7.4":
            return self._check_communication(entry, rule)
        elif rule.rule_id == "ISO42001-7.5":
            return self._check_documented_information(entry, rule)
        elif rule.rule_id == "ISO42001-8.1":
            return self._check_operational_planning(entry, rule)
        elif rule.rule_id == "ISO42001-8.2":
            return self._check_lifecycle_processes(entry, rule)
        elif rule.rule_id == "ISO42001-8.3":
            return self._check_third_party(entry, rule)
        elif rule.rule_id == "ISO42001-8.4":
            return self._check_system_impact(entry, rule)
        elif rule.rule_id == "ISO42001-9.1":
            return self._check_monitoring(entry, rule)
        elif rule.rule_id == "ISO42001-9.2":
            return self._check_internal_audit(entry, rule)
        elif rule.rule_id == "ISO42001-9.3":
            return self._check_management_review(entry, rule)
        elif rule.rule_id == "ISO42001-10.1":
            return self._check_corrective_action(entry, rule)
        elif rule.rule_id == "ISO42001-10.2":
            return self._check_continual_improvement(entry, rule)

        return None

    # =========================================================================
    # Clause 4: Context of the Organization
    # =========================================================================

    def _check_organizational_context(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-4.1: Organizational context must be documented.

        For system-level operations, verify that organizational context
        documentation exists.
        """
        system_events = {"system_registration", "deployment", "system_update", "configuration"}
        if entry.event_type.lower() not in system_events:
            return None

        has_context_documented = entry.metadata.get("organizational_context_documented", False)
        if not has_context_documented:
            return self._create_violation(
                entry,
                rule,
                f"System operation (type={entry.event_type}) performed without "
                f"documented organizational context",
            )
        return None

    def _check_interested_parties(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-4.2: Interested parties must be identified.

        For deployment and external-facing operations, verify stakeholder
        identification.
        """
        stakeholder_relevant_events = {"deployment", "release", "public_api", "data_sharing"}
        if entry.event_type.lower() not in stakeholder_relevant_events:
            return None

        has_stakeholders_identified = entry.metadata.get("stakeholders_identified", False)
        if not has_stakeholders_identified:
            return self._create_violation(
                entry,
                rule,
                f"External-facing operation (type={entry.event_type}) performed "
                f"without documented stakeholder identification",
            )
        return None

    def _check_aims_scope(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-4.3: AIMS scope must be defined.

        For system operations, verify that the system is within defined
        AIMS scope.
        """
        scope_relevant_events = {"system_registration", "deployment", "new_system", "expansion"}
        if entry.event_type.lower() not in scope_relevant_events:
            return None

        has_scope_defined = entry.metadata.get("aims_scope_defined", False)
        in_scope = entry.metadata.get("within_aims_scope", False)

        if not has_scope_defined or not in_scope:
            return self._create_violation(
                entry,
                rule,
                f"System operation (type={entry.event_type}) performed for system "
                f"without verified AIMS scope coverage",
            )
        return None

    # =========================================================================
    # Clause 5: Leadership
    # =========================================================================

    def _check_leadership_commitment(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-5.1: Leadership commitment must be demonstrated.

        For significant decisions and resource allocations, verify
        management approval.
        """
        leadership_events = {
            "policy_change", "resource_allocation", "strategic_decision",
            "deployment", "system_decommission"
        }
        if entry.event_type.lower() not in leadership_events:
            return None

        has_leadership_approval = entry.metadata.get("leadership_approved", False)
        if not has_leadership_approval:
            return self._create_violation(
                entry,
                rule,
                f"Significant operation (type={entry.event_type}) performed "
                f"without documented leadership approval",
            )
        return None

    def _check_ai_policy(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-5.2: AI policy must be established.

        All AI operations should reference compliance with the AI policy.
        """
        ai_events = {
            "inference", "training", "deployment", "model_update",
            "data_processing", "prediction"
        }
        if entry.event_type.lower() not in ai_events:
            return None

        has_policy_reference = entry.metadata.get("ai_policy_compliant", False)
        if not has_policy_reference:
            return self._create_violation(
                entry,
                rule,
                f"AI operation (type={entry.event_type}) performed without "
                f"verified AI policy compliance",
            )
        return None

    def _check_roles_responsibilities(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-5.3: Roles and responsibilities must be assigned.

        Verify that actors performing operations have defined roles.
        """
        # For critical operations, verify role assignment
        critical_events = {
            "deployment", "training", "model_update", "access_grant",
            "configuration_change", "incident_response"
        }
        if entry.event_type.lower() not in critical_events:
            return None

        has_role_defined = entry.metadata.get("role_defined", False)
        has_authorization = entry.metadata.get("authorized_role", False)

        if not (has_role_defined and has_authorization):
            return self._create_violation(
                entry,
                rule,
                f"Critical operation (type={entry.event_type}) performed by actor "
                f"without defined/authorized role: {entry.actor}",
            )
        return None

    # =========================================================================
    # Clause 6: Planning
    # =========================================================================

    def _check_risk_assessment(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-6.1: AI risk assessment must be conducted.

        High-risk operations must have documented risk assessments.
        """
        if entry.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return None

        has_risk_assessment = entry.metadata.get("risk_assessment_documented", False)
        if not has_risk_assessment:
            return self._create_violation(
                entry,
                rule,
                f"High-risk operation (level={entry.risk_level.value}) performed "
                f"without documented AI risk assessment",
            )
        return None

    def _check_ai_objectives(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-6.2: AI objectives must be established.

        Strategic and planning operations should align with AI objectives.
        """
        objective_relevant_events = {
            "project_initiation", "planning", "deployment",
            "system_design", "milestone_review"
        }
        if entry.event_type.lower() not in objective_relevant_events:
            return None

        has_objectives_alignment = entry.metadata.get("ai_objectives_aligned", False)
        if not has_objectives_alignment:
            return self._create_violation(
                entry,
                rule,
                f"Planning operation (type={entry.event_type}) performed without "
                f"documented alignment to AI objectives",
            )
        return None

    def _check_impact_assessment(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-6.3: AI impact assessment must be performed.

        Deployment and high-impact operations require impact assessments.
        """
        impact_events = {
            "deployment", "release", "model_update", "expansion",
            "new_use_case", "user_facing_change"
        }
        if entry.event_type.lower() not in impact_events:
            return None

        has_impact_assessment = entry.metadata.get("impact_assessment_documented", False)
        if not has_impact_assessment:
            return self._create_violation(
                entry,
                rule,
                f"Impact-relevant operation (type={entry.event_type}) performed "
                f"without documented AI impact assessment",
            )
        return None

    # =========================================================================
    # Clause 7: Support
    # =========================================================================

    def _check_resources(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-7.1: Resources must be provided.

        Resource-intensive operations should have resource allocation documented.
        """
        resource_events = {
            "training", "deployment", "infrastructure_change",
            "capacity_expansion", "project_initiation"
        }
        if entry.event_type.lower() not in resource_events:
            return None

        has_resources_allocated = entry.metadata.get("resources_allocated", False)
        if not has_resources_allocated:
            return self._create_violation(
                entry,
                rule,
                f"Resource-intensive operation (type={entry.event_type}) performed "
                f"without documented resource allocation",
            )
        return None

    def _check_competence(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-7.2: Competence must be ensured.

        Technical operations should be performed by competent personnel.
        """
        competence_required_events = {
            "training", "model_development", "deployment", "incident_response",
            "security_assessment", "audit"
        }
        if entry.event_type.lower() not in competence_required_events:
            return None

        has_competence_verified = entry.metadata.get("competence_verified", False)
        if not has_competence_verified:
            return self._create_violation(
                entry,
                rule,
                f"Technical operation (type={entry.event_type}) performed by actor "
                f"without verified competence: {entry.actor}",
            )
        return None

    def _check_awareness(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-7.3: Awareness must be maintained.

        User-initiated operations should have awareness acknowledgment.
        """
        awareness_events = {
            "user_onboarding", "access_grant", "training_completion",
            "policy_acknowledgment"
        }
        if entry.event_type.lower() not in awareness_events:
            return None

        has_awareness_confirmed = entry.metadata.get("awareness_confirmed", False)
        if not has_awareness_confirmed:
            return self._create_violation(
                entry,
                rule,
                f"Awareness-related operation (type={entry.event_type}) completed "
                f"without confirmed awareness acknowledgment",
            )
        return None

    def _check_communication(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-7.4: Communication processes must be established.

        External and stakeholder communications should follow defined processes.
        """
        communication_events = {
            "external_communication", "stakeholder_notification",
            "incident_notification", "regulatory_report", "public_disclosure"
        }
        if entry.event_type.lower() not in communication_events:
            return None

        has_communication_process = entry.metadata.get("communication_process_followed", False)
        if not has_communication_process:
            return self._create_violation(
                entry,
                rule,
                f"Communication operation (type={entry.event_type}) performed "
                f"without following established communication processes",
            )
        return None

    def _check_documented_information(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-7.5: Documented information must be controlled.

        Document-related operations should follow document control procedures.
        """
        document_events = {
            "document_creation", "document_update", "policy_change",
            "procedure_change", "record_creation"
        }
        if entry.event_type.lower() not in document_events:
            return None

        has_document_control = entry.metadata.get("document_control_applied", False)
        if not has_document_control:
            return self._create_violation(
                entry,
                rule,
                f"Document operation (type={entry.event_type}) performed without "
                f"following document control procedures",
            )
        return None

    # =========================================================================
    # Clause 8: Operation
    # =========================================================================

    def _check_operational_planning(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-8.1: Operational planning and control required.

        Significant operations should have documented planning.
        """
        operational_events = {
            "deployment", "release", "migration", "integration",
            "process_change", "configuration_change"
        }
        if entry.event_type.lower() not in operational_events:
            return None

        has_operational_plan = entry.metadata.get("operational_plan_documented", False)
        if not has_operational_plan:
            return self._create_violation(
                entry,
                rule,
                f"Operational activity (type={entry.event_type}) performed "
                f"without documented operational planning",
            )
        return None

    def _check_lifecycle_processes(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-8.2: AI system lifecycle processes required.

        Lifecycle events should follow defined processes.
        """
        lifecycle_events = {
            "design", "development", "training", "validation", "testing",
            "deployment", "monitoring", "maintenance", "decommission"
        }
        if entry.event_type.lower() not in lifecycle_events:
            return None

        has_lifecycle_process = entry.metadata.get("lifecycle_process_followed", False)
        if not has_lifecycle_process:
            return self._create_violation(
                entry,
                rule,
                f"Lifecycle operation (type={entry.event_type}) performed "
                f"without following defined lifecycle processes",
            )
        return None

    def _check_third_party(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-8.3: Third-party considerations required.

        Operations involving external parties should have due diligence.
        """
        third_party_events = {
            "vendor_engagement", "external_api_call", "model_import",
            "data_acquisition", "outsourcing", "third_party_integration"
        }
        if entry.event_type.lower() not in third_party_events:
            return None

        has_third_party_eval = entry.metadata.get("third_party_evaluated", False)
        if not has_third_party_eval:
            return self._create_violation(
                entry,
                rule,
                f"Third-party operation (type={entry.event_type}) performed "
                f"without documented third-party evaluation",
            )
        return None

    def _check_system_impact(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-8.4: AI system impact assessment required.

        Deployment and significant changes require impact assessment.
        """
        impact_events = {
            "deployment", "major_update", "user_expansion",
            "new_market", "feature_release"
        }
        if entry.event_type.lower() not in impact_events:
            return None

        has_system_impact_assessment = entry.metadata.get(
            "system_impact_assessment_documented", False
        )
        if not has_system_impact_assessment:
            return self._create_violation(
                entry,
                rule,
                f"System change (type={entry.event_type}) deployed without "
                f"documented system impact assessment",
            )
        return None

    # =========================================================================
    # Clause 9: Performance Evaluation
    # =========================================================================

    def _check_monitoring(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-9.1: Monitoring and measurement required.

        Production systems should have monitoring in place.
        """
        monitoring_events = {"inference", "prediction", "production_operation"}
        if entry.event_type.lower() not in monitoring_events:
            return None

        has_monitoring = entry.metadata.get("monitoring_enabled", False)
        if not has_monitoring:
            return self._create_violation(
                entry,
                rule,
                f"Production operation (type={entry.event_type}) performed "
                f"without enabled monitoring and measurement",
            )
        return None

    def _check_internal_audit(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-9.2: Internal audit must be conducted.

        Audit-related operations should follow audit procedures.
        """
        audit_events = {"audit", "audit_finding", "compliance_check"}
        if entry.event_type.lower() not in audit_events:
            return None

        has_audit_procedure = entry.metadata.get("audit_procedure_followed", False)
        if not has_audit_procedure:
            return self._create_violation(
                entry,
                rule,
                f"Audit operation (type={entry.event_type}) performed "
                f"without following internal audit procedures",
            )
        return None

    def _check_management_review(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-9.3: Management review required.

        Management review operations should be documented.
        """
        review_events = {"management_review", "executive_briefing", "governance_meeting"}
        if entry.event_type.lower() not in review_events:
            return None

        has_review_documentation = entry.metadata.get("review_documented", False)
        if not has_review_documentation:
            return self._create_violation(
                entry,
                rule,
                f"Management review (type={entry.event_type}) conducted "
                f"without proper documentation of inputs and outputs",
            )
        return None

    # =========================================================================
    # Clause 10: Improvement
    # =========================================================================

    def _check_corrective_action(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-10.1: Nonconformity and corrective action required.

        Nonconformities should have corrective actions documented.
        """
        nonconformity_events = {
            "nonconformity", "incident", "audit_finding",
            "complaint", "failure", "error"
        }
        if entry.event_type.lower() not in nonconformity_events:
            return None

        has_corrective_action = entry.metadata.get("corrective_action_documented", False)
        if not has_corrective_action:
            return self._create_violation(
                entry,
                rule,
                f"Nonconformity (type={entry.event_type}) identified without "
                f"documented corrective action plan",
            )
        return None

    def _check_continual_improvement(
        self, entry: AuditEntry, rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Check ISO42001-10.2: Continual improvement required.

        Improvement opportunities should be captured and tracked.
        """
        improvement_events = {
            "improvement_opportunity", "lessons_learned",
            "process_optimization", "enhancement_request"
        }
        if entry.event_type.lower() not in improvement_events:
            return None

        has_improvement_tracking = entry.metadata.get("improvement_tracked", False)
        if not has_improvement_tracking:
            return self._create_violation(
                entry,
                rule,
                f"Improvement opportunity (type={entry.event_type}) identified "
                f"without being tracked in improvement register",
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
