"""
Compliance report generator for rotalabs-comply.

This module provides the main ReportGenerator class for creating comprehensive
compliance reports from audit data. Reports can be exported in multiple formats
including Markdown, JSON, and HTML.

Example:
    >>> from rotalabs_comply.reports.generator import ReportGenerator, ComplianceReport
    >>> from rotalabs_comply.audit.storage import MemoryStorage
    >>> from rotalabs_comply.frameworks.base import ComplianceProfile
    >>> from datetime import datetime, timedelta
    >>>
    >>> # Setup
    >>> storage = MemoryStorage()
    >>> profile = ComplianceProfile(
    ...     profile_id="prod",
    ...     name="Production",
    ...     enabled_frameworks=["EU AI Act", "SOC2"],
    ... )
    >>> generator = ReportGenerator(storage)
    >>>
    >>> # Generate report
    >>> end = datetime.utcnow()
    >>> start = end - timedelta(days=30)
    >>> report = await generator.generate(
    ...     period_start=start,
    ...     period_end=end,
    ...     profile=profile,
    ... )
    >>>
    >>> # Export
    >>> print(generator.export_markdown(report))
"""

from __future__ import annotations

import html
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Protocol, Sequence, runtime_checkable

from rotalabs_comply.frameworks.base import (
    AuditEntry,
    ComplianceCheckResult,
    ComplianceFramework,
    ComplianceProfile,
    ComplianceViolation,
    RiskLevel,
)
from rotalabs_comply.reports.templates import (
    EU_AI_ACT_TEMPLATE,
    EXECUTIVE_SUMMARY_TEMPLATE,
    HIPAA_TEMPLATE,
    ReportSection,
    ReportTemplate,
    SOC2_TEMPLATE,
    generate_audit_summary,
    generate_compliance_matrix,
    generate_executive_summary,
    generate_metrics_summary,
    generate_recommendations,
    generate_risk_assessment,
)


# Type alias for framework names
FrameworkName = Literal[
    "eu_ai_act", "soc2", "hipaa", "gdpr", "nist_ai_rmf", "iso_42001"
]


@runtime_checkable
class StorageProtocol(Protocol):
    """Protocol for audit storage backends."""

    async def list_entries(
        self, start: datetime, end: datetime
    ) -> List[Any]:
        """List entries within a time range."""
        ...


@dataclass
class ComplianceReport:
    """
    A complete compliance report with all sections and metadata.

    ComplianceReport contains the full results of a compliance evaluation,
    including all sections, summary statistics, and compliance scoring.

    Attributes:
        id: Unique identifier for this report.
        title: Report title.
        framework: Framework evaluated (None for multi-framework reports).
        period_start: Start of the analysis period.
        period_end: End of the analysis period.
        generated_at: When the report was generated.
        profile: ComplianceProfile used for evaluation.
        summary: Summary statistics dictionary.
        sections: List of report sections.
        total_entries: Total audit entries analyzed.
        violations_count: Number of violations found.
        compliance_score: Overall compliance score (0.0 to 1.0).
        status: Overall compliance status.

    Example:
        >>> report = ComplianceReport(
        ...     id="rpt-001",
        ...     title="Q1 2026 Compliance Report",
        ...     framework=None,  # Multi-framework
        ...     period_start=datetime(2026, 1, 1),
        ...     period_end=datetime(2026, 3, 31),
        ...     generated_at=datetime.utcnow(),
        ...     profile=profile,
        ...     summary={"total": 10000, "violations": 5},
        ...     sections=[executive_summary, risk_assessment],
        ...     total_entries=10000,
        ...     violations_count=5,
        ...     compliance_score=0.9995,
        ...     status="compliant",
        ... )
        >>> print(f"Compliance: {report.compliance_score:.2%}")
        Compliance: 99.95%
    """

    id: str
    title: str
    framework: Optional[FrameworkName]
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    profile: ComplianceProfile
    summary: Dict[str, Any]
    sections: List[ReportSection]
    total_entries: int
    violations_count: int
    compliance_score: float
    status: Literal["compliant", "non_compliant", "needs_review"]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report to dictionary for serialization.

        Returns:
            Dict containing all report data.

        Example:
            >>> data = report.to_dict()
            >>> print(data["status"])
            'compliant'
        """
        return {
            "id": self.id,
            "title": self.title,
            "framework": self.framework,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "generated_at": self.generated_at.isoformat(),
            "profile": {
                "profile_id": self.profile.profile_id,
                "name": self.profile.name,
                "enabled_frameworks": self.profile.enabled_frameworks,
            },
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections],
            "total_entries": self.total_entries,
            "violations_count": self.violations_count,
            "compliance_score": self.compliance_score,
            "status": self.status,
        }


class ReportGenerator:
    """
    Generator for compliance reports from audit data.

    ReportGenerator retrieves audit entries from storage, runs compliance
    checks against configured frameworks, and produces comprehensive reports.

    Attributes:
        storage: Storage backend for retrieving audit entries.
        frameworks: Dictionary mapping framework names to implementations.

    Example:
        >>> from rotalabs_comply.audit.storage import MemoryStorage
        >>> from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
        >>>
        >>> storage = MemoryStorage()
        >>> frameworks = {
        ...     "eu_ai_act": EUAIActFramework(),
        ... }
        >>> generator = ReportGenerator(storage, frameworks)
        >>>
        >>> # Generate a report
        >>> report = await generator.generate(
        ...     period_start=datetime(2026, 1, 1),
        ...     period_end=datetime(2026, 1, 31),
        ...     profile=profile,
        ...     framework="eu_ai_act",
        ... )
    """

    def __init__(
        self,
        audit_logger: StorageProtocol,
        frameworks: Optional[Dict[FrameworkName, ComplianceFramework]] = None,
    ) -> None:
        """
        Initialize the report generator.

        Args:
            audit_logger: Storage backend implementing list_entries method.
            frameworks: Optional dict mapping framework names to implementations.
                If not provided, compliance checks will be skipped.

        Example:
            >>> generator = ReportGenerator(storage)
            >>> generator = ReportGenerator(storage, {"soc2": SOC2Framework()})
        """
        self.storage = audit_logger
        self.frameworks = frameworks or {}

    async def generate(
        self,
        period_start: datetime,
        period_end: datetime,
        profile: ComplianceProfile,
        framework: Optional[FrameworkName] = None,
        format: Literal["markdown", "json", "html"] = "markdown",
    ) -> ComplianceReport:
        """
        Generate a comprehensive compliance report.

        Retrieves audit entries for the specified period, runs compliance
        checks, and generates a full report with all standard sections.

        Args:
            period_start: Start of the analysis period (inclusive).
            period_end: End of the analysis period (inclusive).
            profile: ComplianceProfile defining evaluation parameters.
            framework: Specific framework to report on (None = all in profile).
            format: Output format hint (used for template selection).

        Returns:
            ComplianceReport with all sections populated.

        Example:
            >>> report = await generator.generate(
            ...     period_start=datetime(2026, 1, 1),
            ...     period_end=datetime(2026, 1, 31),
            ...     profile=profile,
            ...     format="markdown",
            ... )
            >>> print(f"Generated: {report.title}")
            >>> print(f"Entries: {report.total_entries}")
            >>> print(f"Score: {report.compliance_score:.2%}")
        """
        # Retrieve audit entries
        entries = await self.storage.list_entries(period_start, period_end)
        total_entries = len(entries)

        # Determine which frameworks to evaluate
        frameworks_to_check = []
        if framework:
            frameworks_to_check = [framework]
        elif profile.enabled_frameworks:
            frameworks_to_check = profile.enabled_frameworks
        else:
            frameworks_to_check = list(self.frameworks.keys())

        # Run compliance checks
        all_results: List[ComplianceCheckResult] = []
        all_violations: List[ComplianceViolation] = []

        for fw_name in frameworks_to_check:
            if fw_name in self.frameworks:
                fw_impl = self.frameworks[fw_name]
                for entry in entries:
                    # Convert storage entry to AuditEntry if needed
                    audit_entry = self._convert_to_audit_entry(entry)
                    result = await fw_impl.check(audit_entry, profile)
                    all_results.append(result)
                    all_violations.extend(result.violations)

        # Calculate compliance metrics
        total_checks = sum(r.rules_checked for r in all_results)
        violations_count = len(all_violations)
        critical_violations = sum(
            1 for v in all_violations
            if (v.severity.value if hasattr(v.severity, "value") else str(v.severity)).lower() == "critical"
        )
        high_violations = sum(
            1 for v in all_violations
            if (v.severity.value if hasattr(v.severity, "value") else str(v.severity)).lower() == "high"
        )

        compliance_score = self._calculate_compliance_score(all_violations, total_checks)
        status = self._determine_status(compliance_score, critical_violations)

        # Prepare statistics for section generators
        stats = {
            "total_entries": total_entries,
            "violations_count": violations_count,
            "compliance_rate": compliance_score * 100,
            "critical_violations": critical_violations,
            "high_violations": high_violations,
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "frameworks": frameworks_to_check,
        }

        # Generate sections
        sections = [
            generate_executive_summary(stats),
            generate_risk_assessment(all_violations),
            generate_compliance_matrix(all_results),
            generate_metrics_summary(entries),
            generate_recommendations(all_violations),
            generate_audit_summary(
                entries,
                f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            ),
        ]

        # Select template based on framework
        if framework == "eu_ai_act":
            template = EU_AI_ACT_TEMPLATE
        elif framework == "soc2":
            template = SOC2_TEMPLATE
        elif framework == "hipaa":
            template = HIPAA_TEMPLATE
        else:
            template = EXECUTIVE_SUMMARY_TEMPLATE

        title = template.title if framework else f"Compliance Report - {profile.name}"

        return ComplianceReport(
            id=str(uuid.uuid4()),
            title=title,
            framework=framework,
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.utcnow(),
            profile=profile,
            summary=stats,
            sections=sections,
            total_entries=total_entries,
            violations_count=violations_count,
            compliance_score=compliance_score,
            status=status,
        )

    async def generate_executive_summary(
        self,
        period_start: datetime,
        period_end: datetime,
        profile: ComplianceProfile,
    ) -> ComplianceReport:
        """
        Generate a high-level executive summary report.

        Creates a condensed report suitable for executive audiences,
        focusing on key metrics and critical findings without technical details.

        Args:
            period_start: Start of the analysis period.
            period_end: End of the analysis period.
            profile: ComplianceProfile defining evaluation parameters.

        Returns:
            ComplianceReport with executive-focused sections.

        Example:
            >>> report = await generator.generate_executive_summary(
            ...     period_start=datetime(2026, 1, 1),
            ...     period_end=datetime(2026, 3, 31),
            ...     profile=profile,
            ... )
            >>> print(f"Status: {report.status}")
            >>> print(f"Score: {report.compliance_score:.2%}")
        """
        # Retrieve audit entries
        entries = await self.storage.list_entries(period_start, period_end)
        total_entries = len(entries)

        # Run compliance checks for all frameworks in profile
        frameworks_to_check = profile.enabled_frameworks or list(self.frameworks.keys())
        all_violations: List[ComplianceViolation] = []
        all_results: List[ComplianceCheckResult] = []

        for fw_name in frameworks_to_check:
            if fw_name in self.frameworks:
                fw_impl = self.frameworks[fw_name]
                for entry in entries:
                    audit_entry = self._convert_to_audit_entry(entry)
                    result = await fw_impl.check(audit_entry, profile)
                    all_results.append(result)
                    all_violations.extend(result.violations)

        # Calculate metrics
        total_checks = sum(r.rules_checked for r in all_results)
        violations_count = len(all_violations)
        critical_violations = sum(
            1 for v in all_violations
            if (v.severity.value if hasattr(v.severity, "value") else str(v.severity)).lower() == "critical"
        )
        high_violations = sum(
            1 for v in all_violations
            if (v.severity.value if hasattr(v.severity, "value") else str(v.severity)).lower() == "high"
        )

        compliance_score = self._calculate_compliance_score(all_violations, total_checks)
        status = self._determine_status(compliance_score, critical_violations)

        # Prepare statistics
        stats = {
            "total_entries": total_entries,
            "violations_count": violations_count,
            "compliance_rate": compliance_score * 100,
            "critical_violations": critical_violations,
            "high_violations": high_violations,
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "frameworks": frameworks_to_check,
        }

        # Generate executive-focused sections only
        sections = [
            generate_executive_summary(stats),
            generate_risk_assessment(all_violations),
            generate_recommendations(all_violations),
        ]

        return ComplianceReport(
            id=str(uuid.uuid4()),
            title=f"Executive Summary - {profile.name}",
            framework=None,
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.utcnow(),
            profile=profile,
            summary=stats,
            sections=sections,
            total_entries=total_entries,
            violations_count=violations_count,
            compliance_score=compliance_score,
            status=status,
        )

    def _calculate_compliance_score(
        self,
        violations: List[ComplianceViolation],
        total_checks: int,
    ) -> float:
        """
        Calculate overall compliance score from violations.

        Uses a weighted scoring system where higher-severity violations
        have a greater impact on the score.

        Args:
            violations: List of compliance violations.
            total_checks: Total number of compliance checks performed.

        Returns:
            Compliance score from 0.0 (worst) to 1.0 (best).

        Example:
            >>> score = generator._calculate_compliance_score(violations, 100)
            >>> print(f"{score:.2%}")
            95.00%
        """
        if total_checks == 0:
            return 1.0  # No checks = assume compliant

        if not violations:
            return 1.0  # No violations = fully compliant

        # Weighted penalty per violation by severity
        severity_weights = {
            "critical": 10.0,
            "high": 5.0,
            "medium": 2.0,
            "low": 1.0,
            "info": 0.5,
        }

        total_penalty = 0.0
        for v in violations:
            severity = (
                v.severity.value if hasattr(v.severity, "value") else str(v.severity)
            ).lower()
            weight = severity_weights.get(severity, 1.0)
            total_penalty += weight

        # Calculate score (penalty capped at total checks)
        max_penalty = total_checks * 10.0  # Max if all were critical
        penalty_ratio = min(total_penalty / max_penalty, 1.0)
        score = 1.0 - penalty_ratio

        return max(0.0, min(1.0, score))

    def _determine_status(
        self,
        score: float,
        critical_violations: int,
    ) -> Literal["compliant", "non_compliant", "needs_review"]:
        """
        Determine overall compliance status from score and violations.

        Args:
            score: Compliance score (0.0 to 1.0).
            critical_violations: Number of critical-severity violations.

        Returns:
            Status string: "compliant", "non_compliant", or "needs_review".

        Example:
            >>> status = generator._determine_status(0.95, 0)
            >>> print(status)
            'compliant'
        """
        if critical_violations > 0:
            return "non_compliant"
        if score >= 0.95:
            return "compliant"
        if score >= 0.80:
            return "needs_review"
        return "non_compliant"

    def _convert_to_audit_entry(self, entry: Any) -> AuditEntry:
        """
        Convert a storage entry to the AuditEntry type expected by frameworks.

        Handles both dictionary entries and dataclass/object entries.

        Args:
            entry: Entry from storage (dict or object).

        Returns:
            AuditEntry instance.
        """
        if isinstance(entry, AuditEntry):
            return entry

        if isinstance(entry, dict):
            return AuditEntry(
                entry_id=entry.get("id", str(uuid.uuid4())),
                timestamp=datetime.fromisoformat(entry["timestamp"])
                if isinstance(entry.get("timestamp"), str)
                else entry.get("timestamp", datetime.utcnow()),
                event_type=entry.get("event_type", "unknown"),
                actor=entry.get("actor", entry.get("provider", "unknown")),
                action=entry.get("action", "AI interaction"),
                resource=entry.get("resource", ""),
                metadata=entry.get("metadata", {}),
                risk_level=RiskLevel.LOW,
                system_id=entry.get("system_id", ""),
                data_classification=entry.get("data_classification", "unclassified"),
                user_notified=entry.get("user_notified", False),
                human_oversight=entry.get("human_oversight", False),
                error_handled=entry.get("error_handled", True),
                documentation_ref=entry.get("documentation_ref"),
            )

        # Handle dataclass or object
        return AuditEntry(
            entry_id=getattr(entry, "id", str(uuid.uuid4())),
            timestamp=getattr(entry, "timestamp", datetime.utcnow())
            if isinstance(getattr(entry, "timestamp", None), datetime)
            else datetime.fromisoformat(getattr(entry, "timestamp", datetime.utcnow().isoformat())),
            event_type=getattr(entry, "event_type", "unknown"),
            actor=getattr(entry, "actor", getattr(entry, "provider", "unknown")) or "unknown",
            action=getattr(entry, "action", "AI interaction"),
            resource=getattr(entry, "resource", ""),
            metadata=getattr(entry, "metadata", {}),
            risk_level=RiskLevel.LOW,
            system_id=getattr(entry, "system_id", ""),
            data_classification=getattr(entry, "data_classification", "unclassified"),
            user_notified=getattr(entry, "user_notified", False),
            human_oversight=getattr(entry, "human_oversight", False),
            error_handled=getattr(entry, "error_handled", True),
            documentation_ref=getattr(entry, "documentation_ref", None),
        )

    def export_markdown(self, report: ComplianceReport) -> str:
        """
        Export report to Markdown format.

        Creates a well-formatted Markdown document with proper headings,
        tables, and structure suitable for documentation or rendering.

        Args:
            report: ComplianceReport to export.

        Returns:
            Markdown formatted string.

        Example:
            >>> md = generator.export_markdown(report)
            >>> with open("report.md", "w") as f:
            ...     f.write(md)
        """
        lines = [
            f"# {report.title}",
            "",
            f"**Report ID:** {report.id}",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Period:** {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}",
            f"**Framework:** {report.framework or 'Multiple'}",
            f"**Profile:** {report.profile.name}",
            "",
            "---",
            "",
            f"**Compliance Score:** {report.compliance_score:.2%}",
            f"**Status:** {report.status.upper().replace('_', ' ')}",
            f"**Total Entries:** {report.total_entries:,}",
            f"**Violations:** {report.violations_count:,}",
            "",
            "---",
            "",
        ]

        # Add each section
        for section in report.sections:
            lines.append(section.to_markdown(level=2))
            lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            "*This report was generated by rotalabs-comply.*",
        ])

        return "\n".join(lines)

    def export_json(self, report: ComplianceReport) -> str:
        """
        Export report to JSON format.

        Creates a JSON document with all report data, suitable for
        programmatic processing or API responses.

        Args:
            report: ComplianceReport to export.

        Returns:
            JSON formatted string (pretty-printed).

        Example:
            >>> json_str = generator.export_json(report)
            >>> data = json.loads(json_str)
            >>> print(data["compliance_score"])
        """
        return json.dumps(
            report.to_dict(),
            indent=2,
            default=self._json_serializer,
        )

    def export_html(self, report: ComplianceReport) -> str:
        """
        Export report to HTML format.

        Creates a standalone HTML document with embedded styles,
        suitable for viewing in a browser or embedding in web applications.

        Args:
            report: ComplianceReport to export.

        Returns:
            HTML formatted string.

        Example:
            >>> html = generator.export_html(report)
            >>> with open("report.html", "w") as f:
            ...     f.write(html)
        """
        # Determine status color
        status_colors = {
            "compliant": "#28a745",
            "needs_review": "#ffc107",
            "non_compliant": "#dc3545",
        }
        status_color = status_colors.get(report.status, "#6c757d")

        # Convert sections to HTML
        sections_html = []
        for section in report.sections:
            section_html = self._section_to_html(section)
            sections_html.append(section_html)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(report.title)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .metadata {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .metadata p {{
            margin: 5px 0;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            background-color: {status_color};
        }}
        .score {{
            font-size: 2em;
            font-weight: bold;
            color: {status_color};
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e4e8;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>{html.escape(report.title)}</h1>

    <div class="metadata">
        <p><strong>Report ID:</strong> {html.escape(report.id)}</p>
        <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Period:</strong> {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}</p>
        <p><strong>Framework:</strong> {html.escape(report.framework or 'Multiple')}</p>
        <p><strong>Profile:</strong> {html.escape(report.profile.name)}</p>
    </div>

    <div class="metadata" style="text-align: center;">
        <p><span class="score">{report.compliance_score:.1%}</span></p>
        <p><span class="status-badge">{report.status.upper().replace('_', ' ')}</span></p>
        <p style="margin-top: 15px;">
            <strong>Entries Analyzed:</strong> {report.total_entries:,} |
            <strong>Violations:</strong> {report.violations_count:,}
        </p>
    </div>

    {''.join(sections_html)}

    <div class="footer">
        <p>This report was generated by rotalabs-comply</p>
    </div>
</body>
</html>"""

        return html_content

    def _section_to_html(self, section: ReportSection, level: int = 2) -> str:
        """
        Convert a report section to HTML.

        Args:
            section: ReportSection to convert.
            level: Heading level (default 2).

        Returns:
            HTML string for the section.
        """
        # Convert markdown-style content to basic HTML
        content = html.escape(section.content)

        # Convert markdown tables to HTML tables
        lines = content.split("\n")
        in_table = False
        html_lines = []

        for line in lines:
            if line.strip().startswith("|") and "|" in line[1:]:
                if not in_table:
                    html_lines.append("<table>")
                    in_table = True
                    # Check if this is a header separator
                    if "---" in line:
                        continue
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if html_lines[-1] == "<table>":
                    # First row is header
                    html_lines.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
                else:
                    html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            else:
                if in_table:
                    html_lines.append("</table>")
                    in_table = False

                # Convert markdown formatting
                line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
                while "**" in line:
                    line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)

                # Convert headers
                if line.startswith("### "):
                    line = f"<h4>{line[4:]}</h4>"
                elif line.startswith("#### "):
                    line = f"<h5>{line[5:]}</h5>"
                elif line.startswith("- "):
                    line = f"<li>{line[2:]}</li>"
                elif line.strip():
                    line = f"<p>{line}</p>"

                html_lines.append(line)

        if in_table:
            html_lines.append("</table>")

        content_html = "\n".join(html_lines)

        # Build subsections
        subsections_html = ""
        for subsection in section.subsections:
            subsections_html += self._section_to_html(subsection, level + 1)

        return f"""
    <div class="section">
        <h{level}>{html.escape(section.title)}</h{level}>
        {content_html}
        {subsections_html}
    </div>
"""

    def _json_serializer(self, obj: Any) -> Any:
        """
        Custom JSON serializer for non-standard types.

        Args:
            obj: Object to serialize.

        Returns:
            JSON-serializable representation.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "value"):  # Enum
            return obj.value
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)
