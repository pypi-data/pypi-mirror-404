"""
Report generation module for rotalabs-comply.

This module provides comprehensive compliance report generation capabilities,
including customizable templates, multiple output formats, and executive summaries.

Classes:
    ReportSection: A section within a compliance report.
    ReportTemplate: Template defining report structure and format.
    ComplianceReport: Complete compliance report with all data.
    ReportGenerator: Main class for generating compliance reports.

Pre-defined Templates:
    EU_AI_ACT_TEMPLATE: Template for EU AI Act compliance reports.
    SOC2_TEMPLATE: Template for SOC2 compliance reports.
    HIPAA_TEMPLATE: Template for HIPAA compliance reports.
    EXECUTIVE_SUMMARY_TEMPLATE: Template for executive summary reports.

Example:
    >>> from rotalabs_comply.reports import ReportGenerator, ComplianceReport
    >>> from rotalabs_comply.audit.storage import MemoryStorage
    >>> from datetime import datetime, timedelta
    >>>
    >>> # Create a report generator with a storage backend
    >>> storage = MemoryStorage()
    >>> generator = ReportGenerator(storage)
    >>>
    >>> # Generate a compliance report for the last 30 days
    >>> end = datetime.utcnow()
    >>> start = end - timedelta(days=30)
    >>> report = await generator.generate(
    ...     period_start=start,
    ...     period_end=end,
    ...     profile=profile,
    ... )
    >>>
    >>> # Export to markdown
    >>> markdown = generator.export_markdown(report)
"""

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
from rotalabs_comply.reports.generator import (
    ComplianceReport,
    ReportGenerator,
)

__all__ = [
    # Data classes
    "ReportSection",
    "ReportTemplate",
    "ComplianceReport",
    # Generator
    "ReportGenerator",
    # Pre-defined templates
    "EU_AI_ACT_TEMPLATE",
    "SOC2_TEMPLATE",
    "HIPAA_TEMPLATE",
    "EXECUTIVE_SUMMARY_TEMPLATE",
    # Section generators
    "generate_executive_summary",
    "generate_risk_assessment",
    "generate_compliance_matrix",
    "generate_recommendations",
    "generate_metrics_summary",
    "generate_audit_summary",
]
