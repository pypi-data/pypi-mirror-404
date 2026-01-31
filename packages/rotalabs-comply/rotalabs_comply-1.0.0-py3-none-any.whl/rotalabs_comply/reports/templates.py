"""
Report templates and section generators for compliance reports.

This module provides pre-defined templates for common compliance frameworks
and functions to generate standardized report sections from audit data.

Templates define the structure, format, and required sections for compliance
reports. Section generators create ReportSection objects from raw audit data.

Example:
    >>> from rotalabs_comply.reports.templates import (
    ...     EU_AI_ACT_TEMPLATE,
    ...     generate_executive_summary,
    ...     generate_risk_assessment,
    ... )
    >>>
    >>> # Generate sections from data
    >>> stats = {"total_entries": 1000, "violations": 5, "compliance_rate": 99.5}
    >>> summary = generate_executive_summary(stats)
    >>> print(summary.title)
    'Executive Summary'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Sequence

from rotalabs_comply.frameworks.base import (
    ComplianceCheckResult,
    ComplianceViolation,
    RiskLevel,
)


@dataclass
class ReportSection:
    """
    A section within a compliance report.

    Report sections can contain nested subsections to create hierarchical
    report structures. Each section has a title, content, and optional
    metadata for additional context.

    Attributes:
        title: Section heading/title.
        content: Main content of the section (text, markdown, etc.).
        subsections: Nested sections within this section.
        metadata: Additional data about the section (charts, tables, etc.).

    Example:
        >>> section = ReportSection(
        ...     title="Risk Assessment",
        ...     content="This section analyzes identified compliance risks.",
        ...     subsections=[
        ...         ReportSection(
        ...             title="Critical Risks",
        ...             content="No critical risks identified.",
        ...         ),
        ...         ReportSection(
        ...             title="High Risks",
        ...             content="2 high-risk violations require attention.",
        ...         ),
        ...     ],
        ...     metadata={"risk_count": 2, "max_severity": "high"},
        ... )

        >>> # Access nested sections
        >>> for sub in section.subsections:
        ...     print(f"- {sub.title}")
        - Critical Risks
        - High Risks
    """

    title: str
    content: str
    subsections: List["ReportSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert section to dictionary for serialization.

        Returns:
            Dict containing all section data including nested subsections.

        Example:
            >>> section = ReportSection(title="Test", content="Content")
            >>> data = section.to_dict()
            >>> print(data["title"])
            'Test'
        """
        return {
            "title": self.title,
            "content": self.content,
            "subsections": [s.to_dict() for s in self.subsections],
            "metadata": self.metadata,
        }

    def to_markdown(self, level: int = 2) -> str:
        """
        Render section as markdown with appropriate heading levels.

        Args:
            level: Heading level (default 2 = ##). Subsections use level + 1.

        Returns:
            Markdown formatted string of the section.

        Example:
            >>> section = ReportSection(title="Summary", content="All good.")
            >>> print(section.to_markdown())
            ## Summary
            <BLANKLINE>
            All good.
        """
        heading = "#" * level
        lines = [f"{heading} {self.title}", "", self.content]

        for subsection in self.subsections:
            lines.append("")
            lines.append(subsection.to_markdown(level + 1))

        return "\n".join(lines)


# Type alias for framework specification in templates
FrameworkType = Literal[
    "eu_ai_act", "soc2", "hipaa", "gdpr", "nist_ai_rmf", "iso_42001", "any"
]


@dataclass
class ReportTemplate:
    """
    Template defining the structure and format of a compliance report.

    Templates specify which framework the report covers, its title,
    which sections to include, and the output format.

    Attributes:
        framework: The compliance framework this template is for.
        title: Default title for reports using this template.
        sections: List of section names to include in the report.
        format: Output format for the report (markdown, json, or html).

    Example:
        >>> template = ReportTemplate(
        ...     framework="eu_ai_act",
        ...     title="EU AI Act Compliance Report",
        ...     sections=[
        ...         "executive_summary",
        ...         "risk_assessment",
        ...         "compliance_matrix",
        ...         "recommendations",
        ...     ],
        ...     format="markdown",
        ... )

        >>> # Check what sections will be included
        >>> "risk_assessment" in template.sections
        True
    """

    framework: FrameworkType
    title: str
    sections: List[str]
    format: Literal["markdown", "json", "html"] = "markdown"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert template to dictionary.

        Returns:
            Dict containing template configuration.
        """
        return {
            "framework": self.framework,
            "title": self.title,
            "sections": self.sections,
            "format": self.format,
        }


# =============================================================================
# Pre-defined Templates
# =============================================================================

EU_AI_ACT_TEMPLATE = ReportTemplate(
    framework="eu_ai_act",
    title="EU AI Act Compliance Report",
    sections=[
        "executive_summary",
        "risk_classification",
        "risk_assessment",
        "transparency_obligations",
        "human_oversight",
        "compliance_matrix",
        "data_governance",
        "technical_documentation",
        "recommendations",
        "audit_summary",
    ],
    format="markdown",
)
"""
Template for EU AI Act compliance reports.

Includes sections required for demonstrating compliance with the European
Union's Artificial Intelligence Act, focusing on risk classification,
transparency, and human oversight requirements.

Example:
    >>> from rotalabs_comply.reports.templates import EU_AI_ACT_TEMPLATE
    >>> print(EU_AI_ACT_TEMPLATE.title)
    'EU AI Act Compliance Report'
"""

SOC2_TEMPLATE = ReportTemplate(
    framework="soc2",
    title="SOC2 Type II Compliance Report",
    sections=[
        "executive_summary",
        "system_overview",
        "risk_assessment",
        "security_controls",
        "availability_controls",
        "processing_integrity",
        "confidentiality_controls",
        "privacy_controls",
        "compliance_matrix",
        "recommendations",
        "audit_summary",
    ],
    format="markdown",
)
"""
Template for SOC2 Type II compliance reports.

Covers the five Trust Service Criteria: Security, Availability,
Processing Integrity, Confidentiality, and Privacy.

Example:
    >>> from rotalabs_comply.reports.templates import SOC2_TEMPLATE
    >>> "security_controls" in SOC2_TEMPLATE.sections
    True
"""

HIPAA_TEMPLATE = ReportTemplate(
    framework="hipaa",
    title="HIPAA Compliance Report",
    sections=[
        "executive_summary",
        "risk_assessment",
        "administrative_safeguards",
        "physical_safeguards",
        "technical_safeguards",
        "breach_notification",
        "phi_handling",
        "compliance_matrix",
        "recommendations",
        "audit_summary",
    ],
    format="markdown",
)
"""
Template for HIPAA compliance reports.

Covers the Security Rule requirements including Administrative, Physical,
and Technical Safeguards for Protected Health Information (PHI).

Example:
    >>> from rotalabs_comply.reports.templates import HIPAA_TEMPLATE
    >>> "phi_handling" in HIPAA_TEMPLATE.sections
    True
"""

EXECUTIVE_SUMMARY_TEMPLATE = ReportTemplate(
    framework="any",
    title="Compliance Executive Summary",
    sections=[
        "executive_summary",
        "key_metrics",
        "risk_assessment",
        "critical_findings",
        "recommendations",
    ],
    format="markdown",
)
"""
Template for high-level executive summary reports.

Designed for executive audiences, focusing on key metrics, critical
findings, and high-priority recommendations without technical details.

Example:
    >>> from rotalabs_comply.reports.templates import EXECUTIVE_SUMMARY_TEMPLATE
    >>> len(EXECUTIVE_SUMMARY_TEMPLATE.sections)
    5
"""


# =============================================================================
# Section Generator Functions
# =============================================================================

def generate_executive_summary(stats: Dict[str, Any]) -> ReportSection:
    """
    Generate an executive summary section from statistics.

    Creates a high-level overview of compliance status suitable for
    executive audiences, including key metrics and overall status.

    Args:
        stats: Dictionary containing compliance statistics with keys:
            - total_entries: Total number of audit entries analyzed
            - violations_count: Number of violations found
            - compliance_rate: Percentage of compliant entries (0-100)
            - critical_violations: Number of critical severity violations
            - high_violations: Number of high severity violations
            - period_start: Start of the analysis period (ISO format)
            - period_end: End of the analysis period (ISO format)
            - frameworks: List of frameworks evaluated

    Returns:
        ReportSection with executive summary content.

    Example:
        >>> stats = {
        ...     "total_entries": 10000,
        ...     "violations_count": 15,
        ...     "compliance_rate": 99.85,
        ...     "critical_violations": 0,
        ...     "high_violations": 2,
        ...     "period_start": "2026-01-01",
        ...     "period_end": "2026-01-31",
        ...     "frameworks": ["EU AI Act", "SOC2"],
        ... }
        >>> section = generate_executive_summary(stats)
        >>> print(section.title)
        'Executive Summary'
        >>> "99.85%" in section.content
        True
    """
    total = stats.get("total_entries", 0)
    violations = stats.get("violations_count", 0)
    rate = stats.get("compliance_rate", 100.0)
    critical = stats.get("critical_violations", 0)
    high = stats.get("high_violations", 0)
    period_start = stats.get("period_start", "N/A")
    period_end = stats.get("period_end", "N/A")
    frameworks = stats.get("frameworks", [])

    # Determine overall status
    if critical > 0:
        status = "NON-COMPLIANT"
        status_desc = "Critical violations require immediate attention."
    elif high > 0:
        status = "NEEDS REVIEW"
        status_desc = "High-severity violations should be addressed promptly."
    elif violations > 0:
        status = "PARTIALLY COMPLIANT"
        status_desc = "Minor violations detected; remediation recommended."
    else:
        status = "COMPLIANT"
        status_desc = "All compliance requirements satisfied."

    frameworks_str = ", ".join(frameworks) if frameworks else "All applicable frameworks"

    content = f"""**Compliance Status: {status}**

{status_desc}

### Key Metrics

| Metric | Value |
|--------|-------|
| Analysis Period | {period_start} to {period_end} |
| Total Entries Analyzed | {total:,} |
| Violations Found | {violations:,} |
| Compliance Rate | {rate:.2f}% |
| Critical Violations | {critical} |
| High-Severity Violations | {high} |

### Frameworks Evaluated

{frameworks_str}

### Summary

During the reporting period, {total:,} audit entries were analyzed across the selected compliance frameworks. \
{'No violations were detected, indicating strong compliance posture.' if violations == 0 else f'A total of {violations:,} violations were identified, representing a {100-rate:.2f}% non-compliance rate.'}

{'Immediate action is required to address critical findings.' if critical > 0 else 'Continue monitoring and maintain current compliance practices.' if violations == 0 else 'Review and remediate identified violations according to priority.'}"""

    return ReportSection(
        title="Executive Summary",
        content=content,
        metadata={
            "status": status,
            "compliance_rate": rate,
            "total_entries": total,
            "violations_count": violations,
        },
    )


def generate_risk_assessment(violations: Sequence[ComplianceViolation]) -> ReportSection:
    """
    Generate a risk assessment section from violation data.

    Analyzes violations by severity and category to provide a comprehensive
    risk assessment with prioritized findings.

    Args:
        violations: List of ComplianceViolation objects to analyze.

    Returns:
        ReportSection with risk assessment content and severity breakdown.

    Example:
        >>> from rotalabs_comply.frameworks.base import ComplianceViolation, RiskLevel
        >>> violations = [
        ...     ComplianceViolation(
        ...         rule_id="RULE-001",
        ...         rule_name="Data Encryption",
        ...         severity=RiskLevel.HIGH,
        ...         description="Unencrypted data transmission detected",
        ...         evidence="Request ID: abc123",
        ...         remediation="Enable TLS for all data transmissions",
        ...         entry_id="entry-001",
        ...         category="security",
        ...         framework="SOC2",
        ...     ),
        ... ]
        >>> section = generate_risk_assessment(violations)
        >>> "HIGH" in section.content
        True
    """
    if not violations:
        return ReportSection(
            title="Risk Assessment",
            content="No compliance risks identified during the analysis period. "
            "All audit entries passed compliance checks successfully.",
            metadata={"risk_level": "none", "violation_count": 0},
        )

    # Count violations by severity
    severity_counts: Dict[str, int] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    for v in violations:
        severity = v.severity.value.lower() if hasattr(v.severity, "value") else str(v.severity).lower()
        if severity in severity_counts:
            severity_counts[severity] += 1

    # Count violations by category
    category_counts: Dict[str, int] = {}
    for v in violations:
        category = v.category
        category_counts[category] = category_counts.get(category, 0) + 1

    # Determine overall risk level
    if severity_counts["critical"] > 0:
        overall_risk = "CRITICAL"
        risk_description = "Critical risks require immediate executive attention and remediation."
    elif severity_counts["high"] > 0:
        overall_risk = "HIGH"
        risk_description = "High-severity risks should be addressed within 24-48 hours."
    elif severity_counts["medium"] > 0:
        overall_risk = "MEDIUM"
        risk_description = "Medium-severity risks should be addressed within 1-2 weeks."
    else:
        overall_risk = "LOW"
        risk_description = "Low-severity risks can be addressed during regular review cycles."

    # Build severity breakdown table
    severity_table = """| Severity | Count |
|----------|-------|
"""
    for level in ["critical", "high", "medium", "low", "info"]:
        count = severity_counts[level]
        if count > 0:
            severity_table += f"| {level.upper()} | {count} |\n"

    # Build category breakdown
    category_lines = []
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        category_lines.append(f"- **{category}**: {count} violation{'s' if count != 1 else ''}")
    category_breakdown = "\n".join(category_lines) if category_lines else "No categories identified."

    # Build critical/high findings detail
    critical_findings = []
    for v in violations:
        severity = v.severity.value.lower() if hasattr(v.severity, "value") else str(v.severity).lower()
        if severity in ("critical", "high"):
            critical_findings.append(
                f"- **[{severity.upper()}]** {v.rule_name}: {v.description}"
            )

    findings_section = ""
    if critical_findings:
        findings_section = f"""
### Priority Findings

The following high-priority issues require immediate attention:

{chr(10).join(critical_findings[:10])}
{'...' if len(critical_findings) > 10 else ''}
"""

    content = f"""**Overall Risk Level: {overall_risk}**

{risk_description}

### Severity Distribution

{severity_table}

### Findings by Category

{category_breakdown}
{findings_section}
### Recommendations

1. Address all critical and high-severity findings immediately
2. Implement preventive controls to avoid recurrence
3. Schedule review of medium and low-severity findings
4. Update compliance policies based on findings"""

    return ReportSection(
        title="Risk Assessment",
        content=content,
        metadata={
            "overall_risk": overall_risk,
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "violation_count": len(violations),
        },
    )


def generate_compliance_matrix(results: Sequence[ComplianceCheckResult]) -> ReportSection:
    """
    Generate a compliance matrix showing rule-by-rule compliance status.

    Creates a comprehensive matrix showing which rules passed, failed,
    or were not applicable, organized by framework and category.

    Args:
        results: List of ComplianceCheckResult objects from framework checks.

    Returns:
        ReportSection with compliance matrix content.

    Example:
        >>> from rotalabs_comply.frameworks.base import ComplianceCheckResult
        >>> from datetime import datetime
        >>> results = [
        ...     ComplianceCheckResult(
        ...         entry_id="entry-001",
        ...         framework="EU AI Act",
        ...         framework_version="2024",
        ...         timestamp=datetime.utcnow(),
        ...         rules_checked=10,
        ...         rules_passed=9,
        ...         violations=[],
        ...     ),
        ... ]
        >>> section = generate_compliance_matrix(results)
        >>> "EU AI Act" in section.content
        True
    """
    if not results:
        return ReportSection(
            title="Compliance Matrix",
            content="No compliance check results available for this period.",
            metadata={"frameworks": [], "total_checks": 0},
        )

    # Aggregate results by framework
    framework_stats: Dict[str, Dict[str, int]] = {}
    total_checked = 0
    total_passed = 0
    total_violations = 0

    for result in results:
        fw = result.framework
        if fw not in framework_stats:
            framework_stats[fw] = {
                "checked": 0,
                "passed": 0,
                "violations": 0,
            }
        framework_stats[fw]["checked"] += result.rules_checked
        framework_stats[fw]["passed"] += result.rules_passed
        framework_stats[fw]["violations"] += len(result.violations)

        total_checked += result.rules_checked
        total_passed += result.rules_passed
        total_violations += len(result.violations)

    # Build framework summary table
    fw_table = """| Framework | Rules Checked | Passed | Failed | Compliance % |
|-----------|---------------|--------|--------|--------------|
"""
    for fw, stats in sorted(framework_stats.items()):
        checked = stats["checked"]
        passed = stats["passed"]
        failed = checked - passed
        rate = (passed / checked * 100) if checked > 0 else 100.0
        fw_table += f"| {fw} | {checked} | {passed} | {failed} | {rate:.1f}% |\n"

    # Add totals row
    total_failed = total_checked - total_passed
    overall_rate = (total_passed / total_checked * 100) if total_checked > 0 else 100.0
    fw_table += f"| **Total** | **{total_checked}** | **{total_passed}** | **{total_failed}** | **{overall_rate:.1f}%** |\n"

    # Collect all violations for detail section
    all_violations: List[ComplianceViolation] = []
    for result in results:
        all_violations.extend(result.violations)

    # Build violation details (limited to top 20)
    violation_details = ""
    if all_violations:
        violation_lines = []
        for v in all_violations[:20]:
            severity = v.severity.value if hasattr(v.severity, "value") else str(v.severity)
            violation_lines.append(
                f"| {v.framework} | {v.rule_id} | {v.rule_name[:30]}{'...' if len(v.rule_name) > 30 else ''} | {severity.upper()} |"
            )

        violation_details = f"""
### Detailed Violations

| Framework | Rule ID | Rule Name | Severity |
|-----------|---------|-----------|----------|
{chr(10).join(violation_lines)}
{'*Showing first 20 of ' + str(len(all_violations)) + ' violations*' if len(all_violations) > 20 else ''}
"""

    content = f"""### Framework Compliance Summary

{fw_table}

### Overall Statistics

- **Total Rules Evaluated**: {total_checked:,}
- **Rules Passed**: {total_passed:,}
- **Rules Failed**: {total_failed:,}
- **Total Violations**: {total_violations:,}
- **Overall Compliance Rate**: {overall_rate:.2f}%
{violation_details}
### Interpretation

{'All compliance rules passed successfully.' if total_failed == 0 else f'{total_failed} rules failed compliance checks. Review the violations above and implement recommended remediations.'}"""

    return ReportSection(
        title="Compliance Matrix",
        content=content,
        metadata={
            "frameworks": list(framework_stats.keys()),
            "total_checks": total_checked,
            "total_passed": total_passed,
            "total_violations": total_violations,
            "compliance_rate": overall_rate,
        },
    )


def generate_recommendations(violations: Sequence[ComplianceViolation]) -> ReportSection:
    """
    Generate recommendations section based on violations found.

    Analyzes violations to produce prioritized, actionable recommendations
    for improving compliance posture.

    Args:
        violations: List of ComplianceViolation objects to analyze.

    Returns:
        ReportSection with prioritized recommendations.

    Example:
        >>> from rotalabs_comply.frameworks.base import ComplianceViolation, RiskLevel
        >>> violations = [
        ...     ComplianceViolation(
        ...         rule_id="RULE-001",
        ...         rule_name="Audit Logging",
        ...         severity=RiskLevel.HIGH,
        ...         description="Incomplete audit trail",
        ...         evidence="Missing fields in logs",
        ...         remediation="Enable comprehensive audit logging",
        ...         entry_id="entry-001",
        ...         category="logging",
        ...         framework="SOC2",
        ...     ),
        ... ]
        >>> section = generate_recommendations(violations)
        >>> "Priority" in section.content
        True
    """
    if not violations:
        return ReportSection(
            title="Recommendations",
            content="""### Current Status

No compliance violations were detected during the analysis period. Your AI system demonstrates strong compliance with all evaluated frameworks.

### Maintenance Recommendations

1. **Continue Regular Monitoring**: Maintain current audit logging and compliance checking practices
2. **Stay Updated**: Monitor regulatory changes and update compliance profiles accordingly
3. **Periodic Reviews**: Schedule quarterly compliance reviews to ensure continued adherence
4. **Documentation**: Keep compliance documentation current and accessible
5. **Training**: Ensure team members remain informed about compliance requirements""",
            metadata={"recommendation_count": 5, "priority": "maintenance"},
        )

    # Group violations by remediation to avoid duplicate recommendations
    remediation_map: Dict[str, Dict[str, Any]] = {}
    for v in violations:
        key = v.remediation.lower().strip()
        if key not in remediation_map:
            severity = v.severity.value if hasattr(v.severity, "value") else str(v.severity)
            remediation_map[key] = {
                "text": v.remediation,
                "severity": severity,
                "count": 0,
                "rules": [],
                "framework": v.framework,
            }
        remediation_map[key]["count"] += 1
        if v.rule_id not in remediation_map[key]["rules"]:
            remediation_map[key]["rules"].append(v.rule_id)

    # Sort by severity and count
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_remediations = sorted(
        remediation_map.values(),
        key=lambda x: (severity_order.get(x["severity"].lower(), 5), -x["count"]),
    )

    # Build recommendations sections by priority
    immediate_actions = []
    short_term_actions = []
    long_term_actions = []

    for i, rem in enumerate(sorted_remediations[:15], 1):
        severity = rem["severity"].lower()
        action = f"{i}. **{rem['text']}**\n   - Severity: {severity.upper()}\n   - Affected Rules: {', '.join(rem['rules'][:5])}{'...' if len(rem['rules']) > 5 else ''}\n   - Occurrences: {rem['count']}"

        if severity in ("critical", "high"):
            immediate_actions.append(action)
        elif severity == "medium":
            short_term_actions.append(action)
        else:
            long_term_actions.append(action)

    content = "### Prioritized Recommendations\n\n"

    if immediate_actions:
        content += """#### Immediate Actions (24-48 hours)

The following issues require immediate attention due to their critical or high severity:

"""
        content += "\n\n".join(immediate_actions)
        content += "\n\n"

    if short_term_actions:
        content += """#### Short-Term Actions (1-2 weeks)

Address these medium-severity issues in your next sprint:

"""
        content += "\n\n".join(short_term_actions)
        content += "\n\n"

    if long_term_actions:
        content += """#### Long-Term Improvements

These lower-priority items should be scheduled for future improvement:

"""
        content += "\n\n".join(long_term_actions)
        content += "\n\n"

    content += """### General Best Practices

1. Implement automated compliance monitoring to catch issues early
2. Establish clear ownership for compliance remediation tasks
3. Document all compliance-related changes for audit purposes
4. Conduct regular compliance training for development teams
5. Review and update compliance policies quarterly"""

    return ReportSection(
        title="Recommendations",
        content=content,
        metadata={
            "recommendation_count": len(sorted_remediations),
            "immediate_count": len(immediate_actions),
            "short_term_count": len(short_term_actions),
            "long_term_count": len(long_term_actions),
        },
    )


def generate_metrics_summary(entries: Sequence[Any]) -> ReportSection:
    """
    Generate a metrics summary section from audit entries.

    Provides statistical analysis of audit data including volume trends,
    safety check results, and performance metrics.

    Args:
        entries: List of audit entry objects (any type with standard attributes).
            Expected attributes: timestamp, safety_passed, latency_ms,
            detectors_triggered, provider, model.

    Returns:
        ReportSection with metrics summary content.

    Example:
        >>> entries = [
        ...     {"timestamp": "2026-01-15T10:00:00", "safety_passed": True, "latency_ms": 150.0},
        ...     {"timestamp": "2026-01-15T11:00:00", "safety_passed": True, "latency_ms": 200.0},
        ...     {"timestamp": "2026-01-15T12:00:00", "safety_passed": False, "latency_ms": 175.0},
        ... ]
        >>> section = generate_metrics_summary(entries)
        >>> "Metrics" in section.title
        True
    """
    if not entries:
        return ReportSection(
            title="Metrics Summary",
            content="No audit entries available for metrics analysis.",
            metadata={"entry_count": 0},
        )

    total_entries = len(entries)

    # Calculate safety metrics
    safety_passed = 0
    total_latency = 0.0
    latencies: List[float] = []
    detectors_triggered: Dict[str, int] = {}
    providers: Dict[str, int] = {}
    models: Dict[str, int] = {}

    for entry in entries:
        # Handle both dict and object access
        if isinstance(entry, dict):
            passed = entry.get("safety_passed", True)
            latency = entry.get("latency_ms", 0.0)
            triggered = entry.get("detectors_triggered", [])
            provider = entry.get("provider", "unknown")
            model = entry.get("model", "unknown")
        else:
            passed = getattr(entry, "safety_passed", True)
            latency = getattr(entry, "latency_ms", 0.0)
            triggered = getattr(entry, "detectors_triggered", [])
            provider = getattr(entry, "provider", "unknown") or "unknown"
            model = getattr(entry, "model", "unknown") or "unknown"

        if passed:
            safety_passed += 1
        total_latency += latency
        latencies.append(latency)

        for detector in triggered:
            detectors_triggered[detector] = detectors_triggered.get(detector, 0) + 1

        providers[provider] = providers.get(provider, 0) + 1
        models[model] = models.get(model, 0) + 1

    safety_rate = (safety_passed / total_entries * 100) if total_entries > 0 else 100.0
    avg_latency = total_latency / total_entries if total_entries > 0 else 0.0

    # Calculate latency percentiles
    sorted_latencies = sorted(latencies) if latencies else [0.0]
    p50_idx = int(len(sorted_latencies) * 0.5)
    p95_idx = int(len(sorted_latencies) * 0.95)
    p99_idx = int(len(sorted_latencies) * 0.99)
    p50 = sorted_latencies[p50_idx] if sorted_latencies else 0.0
    p95 = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)] if sorted_latencies else 0.0
    p99 = sorted_latencies[min(p99_idx, len(sorted_latencies) - 1)] if sorted_latencies else 0.0

    # Build provider table
    provider_table = """| Provider | Count | Percentage |
|----------|-------|------------|
"""
    for provider, count in sorted(providers.items(), key=lambda x: -x[1])[:10]:
        pct = count / total_entries * 100
        provider_table += f"| {provider} | {count:,} | {pct:.1f}% |\n"

    # Build detector table
    detector_section = ""
    if detectors_triggered:
        detector_table = """| Detector | Triggers |
|----------|----------|
"""
        for detector, count in sorted(detectors_triggered.items(), key=lambda x: -x[1])[:10]:
            detector_table += f"| {detector} | {count:,} |\n"
        detector_section = f"""
### Safety Detector Activity

{detector_table}
"""

    content = f"""### Volume Metrics

| Metric | Value |
|--------|-------|
| Total Entries | {total_entries:,} |
| Safety Checks Passed | {safety_passed:,} |
| Safety Checks Failed | {total_entries - safety_passed:,} |
| Safety Pass Rate | {safety_rate:.2f}% |

### Performance Metrics

| Metric | Value |
|--------|-------|
| Average Latency | {avg_latency:.2f} ms |
| Median Latency (P50) | {p50:.2f} ms |
| P95 Latency | {p95:.2f} ms |
| P99 Latency | {p99:.2f} ms |

### Provider Distribution

{provider_table}
{detector_section}
### Analysis

{'The system demonstrates excellent safety compliance with a {:.2f}% pass rate.'.format(safety_rate) if safety_rate >= 99 else 'Safety pass rate of {:.2f}% indicates room for improvement.'.format(safety_rate)} \
Average response latency of {avg_latency:.2f}ms is {'within acceptable ranges.' if avg_latency < 500 else 'higher than recommended; consider optimization.'}"""

    return ReportSection(
        title="Metrics Summary",
        content=content,
        metadata={
            "entry_count": total_entries,
            "safety_rate": safety_rate,
            "avg_latency": avg_latency,
            "p50_latency": p50,
            "p95_latency": p95,
            "p99_latency": p99,
        },
    )


def generate_audit_summary(entries: Sequence[Any], period: str) -> ReportSection:
    """
    Generate an audit summary section for a specific period.

    Provides a chronological summary of audit activity including daily
    volumes and notable events.

    Args:
        entries: List of audit entry objects.
        period: Description of the analysis period (e.g., "2026-Q1", "January 2026").

    Returns:
        ReportSection with audit summary content.

    Example:
        >>> entries = [{"timestamp": "2026-01-15T10:00:00", "safety_passed": True}]
        >>> section = generate_audit_summary(entries, "January 2026")
        >>> "January 2026" in section.content
        True
    """
    if not entries:
        return ReportSection(
            title="Audit Summary",
            content=f"No audit entries recorded during {period}.",
            metadata={"period": period, "entry_count": 0},
        )

    total_entries = len(entries)

    # Group entries by date
    daily_counts: Dict[str, int] = {}
    daily_failures: Dict[str, int] = {}

    for entry in entries:
        # Extract date from timestamp
        if isinstance(entry, dict):
            timestamp = entry.get("timestamp", "")
            passed = entry.get("safety_passed", True)
        else:
            timestamp = getattr(entry, "timestamp", "")
            passed = getattr(entry, "safety_passed", True)

        # Handle datetime objects vs strings
        if hasattr(timestamp, "strftime"):
            date_str = timestamp.strftime("%Y-%m-%d")
        elif isinstance(timestamp, str):
            date_str = timestamp[:10] if len(timestamp) >= 10 else "unknown"
        else:
            date_str = "unknown"

        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
        if not passed:
            daily_failures[date_str] = daily_failures.get(date_str, 0) + 1

    # Calculate daily statistics
    daily_values = list(daily_counts.values())
    avg_daily = sum(daily_values) / len(daily_values) if daily_values else 0
    max_daily = max(daily_values) if daily_values else 0
    min_daily = min(daily_values) if daily_values else 0

    # Find peak days
    sorted_days = sorted(daily_counts.items(), key=lambda x: -x[1])
    peak_days = sorted_days[:5]

    # Find days with most failures
    failure_days = sorted(daily_failures.items(), key=lambda x: -x[1])[:5]

    # Build daily activity summary
    peak_table = """| Date | Entries |
|------|---------|
"""
    for date, count in peak_days:
        peak_table += f"| {date} | {count:,} |\n"

    failure_section = ""
    if failure_days:
        failure_table = """| Date | Failures |
|------|----------|
"""
        for date, count in failure_days:
            failure_table += f"| {date} | {count:,} |\n"
        failure_section = f"""
### Days with Most Safety Failures

{failure_table}
"""

    content = f"""### Period: {period}

### Volume Summary

| Metric | Value |
|--------|-------|
| Total Audit Entries | {total_entries:,} |
| Days with Activity | {len(daily_counts)} |
| Average Daily Volume | {avg_daily:,.1f} |
| Peak Daily Volume | {max_daily:,} |
| Minimum Daily Volume | {min_daily:,} |

### Peak Activity Days

{peak_table}
{failure_section}
### Observations

- Average of {avg_daily:,.1f} audit entries recorded per day
- {'Peak volumes were ' + str(int(max_daily / avg_daily)) + 'x the daily average' if avg_daily > 0 and max_daily > avg_daily else 'Activity levels remained consistent'}
- {'Safety failures were concentrated on specific days; review these periods for patterns' if failure_days else 'No significant safety failure patterns detected'}

### Retention Notes

Audit logs for this period should be retained according to your data retention policy. \
Ensure compliance with applicable regulations regarding log storage and access controls."""

    return ReportSection(
        title="Audit Summary",
        content=content,
        metadata={
            "period": period,
            "entry_count": total_entries,
            "days_active": len(daily_counts),
            "avg_daily": avg_daily,
            "peak_daily": max_daily,
        },
    )
