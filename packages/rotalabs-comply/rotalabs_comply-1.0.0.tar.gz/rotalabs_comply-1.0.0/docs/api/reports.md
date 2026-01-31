# Reports Module

Report generation and templates for compliance reporting.

---

## ReportGenerator

::: rotalabs_comply.reports.generator.ReportGenerator
    options:
      show_bases: false

Generator for compliance reports from audit data.

### Constructor

```python
ReportGenerator(
    audit_logger: StorageProtocol,
    frameworks: Optional[Dict[str, ComplianceFramework]] = None,
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `audit_logger` | `StorageProtocol` | Storage backend with `list_entries` method |
| `frameworks` | `Optional[Dict]` | Framework name -> implementation mapping |

**Example:**

```python
from rotalabs_comply import ReportGenerator
from rotalabs_comply.audit import MemoryStorage
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.soc2 import SOC2Framework

storage = MemoryStorage()
generator = ReportGenerator(
    audit_logger=storage,
    frameworks={
        "eu_ai_act": EUAIActFramework(),
        "soc2": SOC2Framework(),
    },
)
```

### Methods

#### generate

```python
async def generate(
    period_start: datetime,
    period_end: datetime,
    profile: ComplianceProfile,
    framework: Optional[str] = None,
    format: Literal["markdown", "json", "html"] = "markdown",
) -> ComplianceReport
```

Generate a comprehensive compliance report.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period_start` | `datetime` | Required | Analysis start (inclusive) |
| `period_end` | `datetime` | Required | Analysis end (inclusive) |
| `profile` | `ComplianceProfile` | Required | Evaluation configuration |
| `framework` | `Optional[str]` | `None` | Specific framework (None=all) |
| `format` | `str` | `"markdown"` | Output format hint |

**Returns:** `ComplianceReport`

**Example:**

```python
from datetime import datetime, timedelta

end = datetime.utcnow()
start = end - timedelta(days=30)

report = await generator.generate(
    period_start=start,
    period_end=end,
    profile=profile,
    framework="eu_ai_act",
)
```

#### generate_executive_summary

```python
async def generate_executive_summary(
    period_start: datetime,
    period_end: datetime,
    profile: ComplianceProfile,
) -> ComplianceReport
```

Generate a condensed executive summary report.

**Example:**

```python
report = await generator.generate_executive_summary(
    period_start=start,
    period_end=end,
    profile=profile,
)
```

#### export_markdown

```python
def export_markdown(report: ComplianceReport) -> str
```

Export report to Markdown format.

**Example:**

```python
markdown = generator.export_markdown(report)
with open("report.md", "w") as f:
    f.write(markdown)
```

#### export_json

```python
def export_json(report: ComplianceReport) -> str
```

Export report to JSON format (pretty-printed).

**Example:**

```python
json_str = generator.export_json(report)
```

#### export_html

```python
def export_html(report: ComplianceReport) -> str
```

Export report to standalone HTML format.

**Example:**

```python
html = generator.export_html(report)
with open("report.html", "w") as f:
    f.write(html)
```

---

## ComplianceReport

::: rotalabs_comply.reports.generator.ComplianceReport
    options:
      show_bases: false

A complete compliance report with all sections and metadata.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique report identifier |
| `title` | `str` | Report title |
| `framework` | `Optional[str]` | Framework evaluated (None=multiple) |
| `period_start` | `datetime` | Analysis period start |
| `period_end` | `datetime` | Analysis period end |
| `generated_at` | `datetime` | When report was generated |
| `profile` | `ComplianceProfile` | Profile used for evaluation |
| `summary` | `Dict[str, Any]` | Summary statistics |
| `sections` | `List[ReportSection]` | Report sections |
| `total_entries` | `int` | Entries analyzed |
| `violations_count` | `int` | Violations found |
| `compliance_score` | `float` | Score 0.0-1.0 |
| `status` | `str` | "compliant", "non_compliant", "needs_review" |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Convert to dictionary |

---

## Templates

### ReportSection

::: rotalabs_comply.reports.templates.ReportSection
    options:
      show_bases: false

A section within a compliance report.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | `str` | Section heading |
| `content` | `str` | Main content (text/markdown) |
| `subsections` | `List[ReportSection]` | Nested sections |
| `metadata` | `Dict[str, Any]` | Additional data |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Convert to dictionary |
| `to_markdown(level=2)` | `str` | Render as markdown |

**Example:**

```python
from rotalabs_comply.reports.templates import ReportSection

section = ReportSection(
    title="Risk Assessment",
    content="Analysis of identified risks...",
    subsections=[
        ReportSection(title="Critical Risks", content="None found."),
        ReportSection(title="High Risks", content="2 issues identified."),
    ],
    metadata={"risk_count": 2},
)

print(section.to_markdown())
```

---

### ReportTemplate

::: rotalabs_comply.reports.templates.ReportTemplate
    options:
      show_bases: false

Template defining report structure and format.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `framework` | `str` | Target framework |
| `title` | `str` | Default title |
| `sections` | `List[str]` | Section names to include |
| `format` | `str` | Output format |

### Pre-defined Templates

#### EU_AI_ACT_TEMPLATE

::: rotalabs_comply.reports.templates.EU_AI_ACT_TEMPLATE

Template for EU AI Act compliance reports.

**Sections:**
- executive_summary
- risk_classification
- risk_assessment
- transparency_obligations
- human_oversight
- compliance_matrix
- data_governance
- technical_documentation
- recommendations
- audit_summary

#### SOC2_TEMPLATE

::: rotalabs_comply.reports.templates.SOC2_TEMPLATE

Template for SOC2 Type II compliance reports.

**Sections:**
- executive_summary
- system_overview
- risk_assessment
- security_controls
- availability_controls
- processing_integrity
- confidentiality_controls
- privacy_controls
- compliance_matrix
- recommendations
- audit_summary

#### HIPAA_TEMPLATE

::: rotalabs_comply.reports.templates.HIPAA_TEMPLATE

Template for HIPAA compliance reports.

**Sections:**
- executive_summary
- risk_assessment
- administrative_safeguards
- physical_safeguards
- technical_safeguards
- breach_notification
- phi_handling
- compliance_matrix
- recommendations
- audit_summary

#### EXECUTIVE_SUMMARY_TEMPLATE

::: rotalabs_comply.reports.templates.EXECUTIVE_SUMMARY_TEMPLATE

Template for executive summary reports.

**Sections:**
- executive_summary
- key_metrics
- risk_assessment
- critical_findings
- recommendations

---

## Section Generators

### generate_executive_summary

```python
def generate_executive_summary(stats: Dict[str, Any]) -> ReportSection
```

Generate executive summary from statistics.

**Expected stats keys:**
- `total_entries`: int
- `violations_count`: int
- `compliance_rate`: float (0-100)
- `critical_violations`: int
- `high_violations`: int
- `period_start`: str
- `period_end`: str
- `frameworks`: List[str]

**Example:**

```python
from rotalabs_comply.reports.templates import generate_executive_summary

stats = {
    "total_entries": 10000,
    "violations_count": 15,
    "compliance_rate": 99.85,
    "critical_violations": 0,
    "high_violations": 2,
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "frameworks": ["EU AI Act", "SOC2"],
}

section = generate_executive_summary(stats)
print(section.metadata["status"])  # "NEEDS REVIEW"
```

---

### generate_risk_assessment

```python
def generate_risk_assessment(violations: Sequence[ComplianceViolation]) -> ReportSection
```

Generate risk assessment from violations.

**Returns section with metadata:**
- `overall_risk`: str
- `severity_counts`: Dict[str, int]
- `category_counts`: Dict[str, int]
- `violation_count`: int

---

### generate_compliance_matrix

```python
def generate_compliance_matrix(results: Sequence[ComplianceCheckResult]) -> ReportSection
```

Generate compliance matrix from check results.

**Returns section with metadata:**
- `frameworks`: List[str]
- `total_checks`: int
- `total_passed`: int
- `total_violations`: int
- `compliance_rate`: float

---

### generate_recommendations

```python
def generate_recommendations(violations: Sequence[ComplianceViolation]) -> ReportSection
```

Generate prioritized recommendations from violations.

**Returns section with metadata:**
- `recommendation_count`: int
- `immediate_count`: int
- `short_term_count`: int
- `long_term_count`: int

---

### generate_metrics_summary

```python
def generate_metrics_summary(entries: Sequence[Any]) -> ReportSection
```

Generate metrics summary from audit entries.

**Returns section with metadata:**
- `entry_count`: int
- `safety_rate`: float
- `avg_latency`: float
- `p50_latency`: float
- `p95_latency`: float
- `p99_latency`: float

---

### generate_audit_summary

```python
def generate_audit_summary(entries: Sequence[Any], period: str) -> ReportSection
```

Generate audit summary for a period.

**Returns section with metadata:**
- `period`: str
- `entry_count`: int
- `days_active`: int
- `avg_daily`: float
- `peak_daily`: int
