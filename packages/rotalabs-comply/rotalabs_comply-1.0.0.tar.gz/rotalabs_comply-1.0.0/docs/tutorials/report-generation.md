# Report Generation Tutorial

This tutorial covers generating and exporting compliance reports from audit data, including customization and scheduling for automated reporting.

## Overview

Compliance reports summarize audit data and compliance check results for stakeholders:

- **Executive summaries** for leadership
- **Risk assessments** for security teams
- **Compliance matrices** for auditors
- **Recommendations** for operations teams

## Basic Report Generation

### Setup

```python
import asyncio
from datetime import datetime, timedelta
from rotalabs_comply import AuditLogger, ReportGenerator
from rotalabs_comply.audit import MemoryStorage
from rotalabs_comply.frameworks.base import ComplianceProfile
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.soc2 import SOC2Framework
from rotalabs_comply.frameworks.hipaa import HIPAAFramework

# Set up storage and logger
storage = MemoryStorage()
logger = AuditLogger(storage)

# Create report generator with frameworks
generator = ReportGenerator(
    audit_logger=storage,
    frameworks={
        "eu_ai_act": EUAIActFramework(),
        "soc2": SOC2Framework(),
        "hipaa": HIPAAFramework(),
    },
)

# Create compliance profile
profile = ComplianceProfile(
    profile_id="production",
    name="Production AI System",
    enabled_frameworks=["eu_ai_act", "soc2"],
)
```

### Generate Full Report

```python
async def main():
    # First, log some entries
    for i in range(100):
        await logger.log(
            input=f"Query {i}",
            output=f"Response {i}",
            provider="openai",
            model="gpt-4",
            safety_passed=i % 10 != 0,  # 10% failure rate
            latency_ms=100 + i,
        )

    # Define reporting period
    end = datetime.utcnow()
    start = end - timedelta(days=30)

    # Generate report
    report = await generator.generate(
        period_start=start,
        period_end=end,
        profile=profile,
    )

    print(f"Report: {report.title}")
    print(f"ID: {report.id}")
    print(f"Period: {report.period_start} to {report.period_end}")
    print(f"Entries analyzed: {report.total_entries}")
    print(f"Violations found: {report.violations_count}")
    print(f"Compliance score: {report.compliance_score:.2%}")
    print(f"Status: {report.status}")

asyncio.run(main())
```

## Export Formats

### Markdown Export

Perfect for documentation systems and README files:

```python
# Export to Markdown
markdown = generator.export_markdown(report)

# Save to file
with open("compliance_report.md", "w") as f:
    f.write(markdown)

# Preview
print(markdown[:1000])
```

Output structure:
```markdown
# Compliance Report - Production AI System

**Report ID:** abc-123-def
**Generated:** 2026-01-29 10:30:00 UTC
**Period:** 2026-01-01 to 2026-01-29
**Framework:** Multiple
**Profile:** Production AI System

---

**Compliance Score:** 95.50%
**Status:** COMPLIANT
**Total Entries:** 10,000
**Violations:** 45

---

## Executive Summary

**Compliance Status: COMPLIANT**
...
```

### JSON Export

For programmatic processing and API integration:

```python
import json

# Export to JSON
json_str = generator.export_json(report)

# Save to file
with open("compliance_report.json", "w") as f:
    f.write(json_str)

# Load and process
data = json.loads(json_str)
print(f"Score: {data['compliance_score']}")
print(f"Sections: {len(data['sections'])}")
```

### HTML Export

Standalone reports for stakeholders:

```python
# Export to HTML
html = generator.export_html(report)

# Save to file
with open("compliance_report.html", "w") as f:
    f.write(html)

# Open in browser (optional)
import webbrowser
webbrowser.open("compliance_report.html")
```

The HTML export includes:
- Embedded CSS styling
- Color-coded status badges
- Responsive layout
- Tables with alternating row colors
- Professional formatting

## Report Sections

### Executive Summary

High-level overview for leadership:

```python
# Access executive summary section
for section in report.sections:
    if section.title == "Executive Summary":
        print(section.content)
        print(f"Status: {section.metadata.get('status')}")
        print(f"Rate: {section.metadata.get('compliance_rate')}%")
```

Content includes:
- Overall compliance status
- Key metrics table
- Frameworks evaluated
- Summary interpretation

### Risk Assessment

Security-focused analysis:

```python
for section in report.sections:
    if section.title == "Risk Assessment":
        print(f"Overall risk: {section.metadata.get('overall_risk')}")
        print(f"Severity counts: {section.metadata.get('severity_counts')}")
```

Content includes:
- Overall risk level
- Severity distribution table
- Findings by category
- Priority findings list
- Risk-based recommendations

### Compliance Matrix

Auditor-friendly rule-by-rule breakdown:

```python
for section in report.sections:
    if section.title == "Compliance Matrix":
        print(f"Frameworks: {section.metadata.get('frameworks')}")
        print(f"Total checks: {section.metadata.get('total_checks')}")
        print(f"Overall rate: {section.metadata.get('compliance_rate')}%")
```

Content includes:
- Framework summary table
- Pass/fail counts per framework
- Detailed violation list
- Overall statistics

### Metrics Summary

Performance and safety metrics:

```python
for section in report.sections:
    if section.title == "Metrics Summary":
        print(f"Safety rate: {section.metadata.get('safety_rate')}%")
        print(f"Avg latency: {section.metadata.get('avg_latency')}ms")
        print(f"P95 latency: {section.metadata.get('p95_latency')}ms")
```

Content includes:
- Volume metrics
- Safety pass rates
- Latency percentiles (P50, P95, P99)
- Provider distribution

### Recommendations

Prioritized action items:

```python
for section in report.sections:
    if section.title == "Recommendations":
        print(f"Total: {section.metadata.get('recommendation_count')}")
        print(f"Immediate: {section.metadata.get('immediate_count')}")
        print(f"Short-term: {section.metadata.get('short_term_count')}")
```

Content includes:
- Immediate actions (24-48 hours)
- Short-term actions (1-2 weeks)
- Long-term improvements
- General best practices

### Audit Summary

Volume and activity analysis:

```python
for section in report.sections:
    if section.title == "Audit Summary":
        print(f"Period: {section.metadata.get('period')}")
        print(f"Daily average: {section.metadata.get('avg_daily')}")
        print(f"Peak volume: {section.metadata.get('peak_daily')}")
```

Content includes:
- Volume summary
- Peak activity days
- Failure patterns
- Retention notes

## Framework-Specific Reports

### EU AI Act Report

```python
report = await generator.generate(
    period_start=start,
    period_end=end,
    profile=profile,
    framework="eu_ai_act",
)

print(report.title)  # "EU AI Act Compliance Report"
```

Template includes sections for:
- Risk classification
- Transparency obligations
- Human oversight
- Data governance
- Technical documentation

### SOC2 Report

```python
report = await generator.generate(
    period_start=start,
    period_end=end,
    profile=profile,
    framework="soc2",
)

print(report.title)  # "SOC2 Type II Compliance Report"
```

Template includes sections for:
- System overview
- Security controls (CC)
- Availability controls (A)
- Processing integrity (PI)
- Confidentiality controls (C)
- Privacy controls (P)

### HIPAA Report

```python
report = await generator.generate(
    period_start=start,
    period_end=end,
    profile=profile,
    framework="hipaa",
)

print(report.title)  # "HIPAA Compliance Report"
```

Template includes sections for:
- Administrative safeguards
- Physical safeguards
- Technical safeguards
- Breach notification
- PHI handling

## Executive Summary Report

Generate a condensed report for executives:

```python
report = await generator.generate_executive_summary(
    period_start=start,
    period_end=end,
    profile=profile,
)

print(f"Title: {report.title}")  # "Executive Summary - Production AI System"
print(f"Sections: {len(report.sections)}")  # Fewer sections
```

Executive summary includes only:
- Executive summary
- Risk assessment
- Recommendations

## Scheduled Reporting

### Daily Reports

```python
import asyncio
from datetime import datetime, timedelta

async def generate_daily_report():
    end = datetime.utcnow().replace(hour=0, minute=0, second=0)
    start = end - timedelta(days=1)

    report = await generator.generate(
        period_start=start,
        period_end=end,
        profile=profile,
    )

    # Save reports
    date_str = start.strftime("%Y%m%d")
    generator.export_markdown(report)
    with open(f"reports/daily_{date_str}.md", "w") as f:
        f.write(generator.export_markdown(report))

    return report

async def daily_report_scheduler():
    while True:
        now = datetime.now()
        # Run at 6 AM
        next_run = now.replace(hour=6, minute=0, second=0)
        if next_run <= now:
            next_run += timedelta(days=1)

        await asyncio.sleep((next_run - now).total_seconds())

        try:
            report = await generate_daily_report()
            print(f"[{datetime.now()}] Generated daily report: {report.status}")
        except Exception as e:
            print(f"[{datetime.now()}] Report generation failed: {e}")
```

### Weekly Reports

```python
async def generate_weekly_report():
    end = datetime.utcnow()
    start = end - timedelta(days=7)

    report = await generator.generate(
        period_start=start,
        period_end=end,
        profile=profile,
    )

    # Generate all formats
    week_str = start.strftime("%Y-W%V")

    with open(f"reports/weekly_{week_str}.md", "w") as f:
        f.write(generator.export_markdown(report))

    with open(f"reports/weekly_{week_str}.html", "w") as f:
        f.write(generator.export_html(report))

    with open(f"reports/weekly_{week_str}.json", "w") as f:
        f.write(generator.export_json(report))

    return report
```

### Monthly Reports

```python
import calendar

async def generate_monthly_report(year: int, month: int):
    # Calculate month boundaries
    _, last_day = calendar.monthrange(year, month)
    start = datetime(year, month, 1)
    end = datetime(year, month, last_day, 23, 59, 59)

    report = await generator.generate(
        period_start=start,
        period_end=end,
        profile=profile,
    )

    month_str = start.strftime("%Y-%m")

    with open(f"reports/monthly_{month_str}.html", "w") as f:
        f.write(generator.export_html(report))

    return report
```

### Quarterly Reports

```python
async def generate_quarterly_report(year: int, quarter: int):
    # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2
    _, last_day = calendar.monthrange(year, end_month)

    start = datetime(year, start_month, 1)
    end = datetime(year, end_month, last_day, 23, 59, 59)

    report = await generator.generate(
        period_start=start,
        period_end=end,
        profile=profile,
    )

    quarter_str = f"{year}-Q{quarter}"

    with open(f"reports/quarterly_{quarter_str}.html", "w") as f:
        f.write(generator.export_html(report))

    return report
```

## Email Distribution

### Send Report via Email

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

async def send_compliance_report(report, recipients):
    # Generate HTML report
    html_content = generator.export_html(report)

    # Create email
    msg = MIMEMultipart()
    msg["Subject"] = f"Compliance Report: {report.title} - {report.status.upper()}"
    msg["From"] = "compliance@company.com"
    msg["To"] = ", ".join(recipients)

    # Add summary in body
    body = f"""
    Compliance Report Summary
    ========================
    Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}
    Status: {report.status.upper()}
    Compliance Score: {report.compliance_score:.2%}
    Entries Analyzed: {report.total_entries:,}
    Violations Found: {report.violations_count:,}

    Full report attached.
    """
    msg.attach(MIMEText(body, "plain"))

    # Attach HTML report
    attachment = MIMEApplication(html_content.encode(), Name="compliance_report.html")
    attachment["Content-Disposition"] = 'attachment; filename="compliance_report.html"'
    msg.attach(attachment)

    # Send
    with smtplib.SMTP("smtp.company.com", 587) as server:
        server.starttls()
        server.login("compliance@company.com", "password")
        server.send_message(msg)

    print(f"Report sent to {recipients}")
```

## Slack Integration

### Post Report Summary

```python
import httpx

async def post_to_slack(report, webhook_url):
    # Determine emoji based on status
    emoji = {
        "compliant": ":white_check_mark:",
        "needs_review": ":warning:",
        "non_compliant": ":x:",
    }.get(report.status, ":question:")

    # Create message
    message = {
        "text": f"{emoji} Compliance Report Generated",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {report.title}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{report.status.upper()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Score:*\n{report.compliance_score:.2%}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Entries:*\n{report.total_entries:,}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Violations:*\n{report.violations_count:,}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}",
                },
            },
        ],
    }

    # Send to Slack
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=message)
        response.raise_for_status()
```

## Custom Report Templates

### Using Pre-defined Templates

```python
from rotalabs_comply.reports.templates import (
    EU_AI_ACT_TEMPLATE,
    SOC2_TEMPLATE,
    HIPAA_TEMPLATE,
    EXECUTIVE_SUMMARY_TEMPLATE,
)

print(EU_AI_ACT_TEMPLATE.title)     # "EU AI Act Compliance Report"
print(EU_AI_ACT_TEMPLATE.sections)  # List of section names
print(EU_AI_ACT_TEMPLATE.format)    # "markdown"
```

### Creating Custom Templates

```python
from rotalabs_comply.reports.templates import ReportTemplate

custom_template = ReportTemplate(
    framework="custom",
    title="Custom Compliance Report",
    sections=[
        "executive_summary",
        "risk_assessment",
        "custom_section",
        "recommendations",
    ],
    format="html",
)
```

## Best Practices

### 1. Archive Reports

```python
import os
from datetime import datetime

def archive_report(report, base_path="/var/reports"):
    # Create archive structure
    year = report.period_end.strftime("%Y")
    month = report.period_end.strftime("%m")
    archive_dir = os.path.join(base_path, year, month)
    os.makedirs(archive_dir, exist_ok=True)

    # Save in all formats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"compliance_{timestamp}"

    with open(os.path.join(archive_dir, f"{base_name}.md"), "w") as f:
        f.write(generator.export_markdown(report))

    with open(os.path.join(archive_dir, f"{base_name}.html"), "w") as f:
        f.write(generator.export_html(report))

    with open(os.path.join(archive_dir, f"{base_name}.json"), "w") as f:
        f.write(generator.export_json(report))

    return archive_dir
```

### 2. Track Report Metrics

```python
report_metrics = []

async def generate_and_track(period_start, period_end, profile):
    report = await generator.generate(
        period_start=period_start,
        period_end=period_end,
        profile=profile,
    )

    # Track metrics over time
    report_metrics.append({
        "generated_at": datetime.now().isoformat(),
        "period": f"{period_start.date()} to {period_end.date()}",
        "score": report.compliance_score,
        "status": report.status,
        "violations": report.violations_count,
        "entries": report.total_entries,
    })

    return report

# Analyze trends
import pandas as pd
df = pd.DataFrame(report_metrics)
print(df.describe())
```

### 3. Alert on Critical Status

```python
async def generate_with_alerts(period_start, period_end, profile):
    report = await generator.generate(
        period_start=period_start,
        period_end=period_end,
        profile=profile,
    )

    # Alert on non-compliant status
    if report.status == "non_compliant":
        # Send immediate alert
        await send_alert(
            level="critical",
            message=f"Non-compliant report generated: {report.violations_count} violations",
            report_id=report.id,
        )

    # Alert on score drops
    previous_score = get_previous_score()
    if previous_score and report.compliance_score < previous_score - 0.05:
        await send_alert(
            level="warning",
            message=f"Compliance score dropped from {previous_score:.2%} to {report.compliance_score:.2%}",
            report_id=report.id,
        )

    return report
```
