# Core Concepts

This page explains the fundamental concepts behind `rotalabs-comply` and how the different components work together.

---

## Compliance Pipeline

Every compliance workflow in `rotalabs-comply` follows a four-stage pipeline:

```
Audit Logging --> Compliance Checking --> Report Generation --> Remediation
```

1. **Audit Logging** -- Capture all AI system interactions with comprehensive metadata including inputs, outputs, safety checks, and performance metrics.

2. **Compliance Checking** -- Evaluate audit entries against one or more regulatory frameworks to identify violations and risks.

3. **Report Generation** -- Generate structured compliance reports with executive summaries, risk assessments, and prioritized recommendations.

4. **Remediation** -- Address identified violations using the provided remediation guidance and update compliance posture.

---

## Audit Logging

### AuditEntry

An `AuditEntry` captures a single AI system interaction with all relevant compliance metadata:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (UUID) |
| `timestamp` | When the interaction occurred |
| `provider` | AI provider (e.g., "openai", "anthropic") |
| `model` | Model identifier (e.g., "gpt-4", "claude-3-opus") |
| `input_hash` | SHA-256 hash of input content |
| `output_hash` | SHA-256 hash of output content |
| `input_content` | Actual input (if `store_content=True`, may be encrypted) |
| `output_content` | Actual output (if `store_content=True`, may be encrypted) |
| `safety_passed` | Whether all safety checks passed |
| `detectors_triggered` | List of safety detectors that flagged content |
| `latency_ms` | Response time in milliseconds |
| `metadata` | Custom key-value metadata |

### Privacy Modes

`rotalabs-comply` offers three privacy modes to balance audit completeness with data protection:

```
Hash-Only Mode (Default)
├── Stores SHA-256 hashes only
├── Content can be verified but not recovered
└── Maximum privacy protection

Encrypted Mode
├── Stores Fernet-encrypted content
├── Content recoverable with encryption key
└── Balance of auditability and protection

Plaintext Mode
├── Stores content as-is
├── No encryption overhead
└── Development/testing only
```

### Content Hashing

When `store_content=False` (default), only SHA-256 hashes are stored:

```python
from rotalabs_comply.audit import hash_content

# Compute hash
content = "What is 2+2?"
content_hash = hash_content(content)
# Returns: "a0c2..."

# Later, verify content matches
if hash_content(provided_content) == stored_hash:
    print("Content verified")
```

This allows verification that logged content matches original content without storing the actual data.

### Encryption

When encryption is enabled, content is protected using Fernet symmetric encryption:

```python
from rotalabs_comply.audit import EncryptionManager, generate_key

# Auto-generate key
manager = EncryptionManager()

# Or use existing key
key = generate_key()
manager = EncryptionManager(key)

# Encrypt/decrypt
encrypted = manager.encrypt("sensitive data")
decrypted = manager.decrypt(encrypted)

# Important: Save the key securely!
key = manager.get_key()  # Store in secrets manager
```

!!! warning "Key Management"
    The encryption key is the only way to recover encrypted content. Store it securely (e.g., AWS Secrets Manager, HashiCorp Vault) and never commit it to version control.

---

## Storage Backends

### StorageBackend Protocol

All storage backends implement the `StorageBackend` protocol:

```python
class StorageBackend(Protocol):
    async def write(self, entry: AuditEntry) -> str: ...
    async def read(self, entry_id: str) -> AuditEntry | None: ...
    async def list_entries(self, start: datetime, end: datetime) -> List[AuditEntry]: ...
    async def delete(self, entry_id: str) -> bool: ...
    async def count(self) -> int: ...
```

### FileStorage

Local file storage using JSONL format with automatic rotation:

- **File naming**: `audit_YYYYMMDD.jsonl`
- **Rotation**: When file exceeds `rotation_size_mb` (default: 100MB)
- **Indexing**: In-memory index for fast lookups

```python
from rotalabs_comply.audit import FileStorage

storage = FileStorage(
    path="/var/log/ai-audit",
    rotation_size_mb=100,
)
```

### S3Storage

AWS S3 storage for cloud-native deployments:

- **Key structure**: `{prefix}{YYYY-MM-DD}/{entry_id}.json`
- **Lifecycle**: Use S3 lifecycle policies for retention
- **Pagination**: Handles large result sets automatically

```python
from rotalabs_comply.audit import S3Storage

storage = S3Storage(
    bucket="my-audit-bucket",
    prefix="prod/audit/",
    region="us-west-2",
)
```

### MemoryStorage

In-memory storage for testing and development:

- **LRU eviction**: Optional `max_entries` limit
- **No persistence**: Data lost when process ends
- **Fast operations**: No I/O overhead

```python
from rotalabs_comply.audit import MemoryStorage

storage = MemoryStorage(max_entries=10000)
```

---

## Compliance Frameworks

### Framework Architecture

Each compliance framework consists of:

1. **Rules** -- Individual compliance requirements with severity, category, and check logic
2. **Check Function** -- Evaluates audit entries against rules
3. **Remediation Guidance** -- Recommendations for addressing violations

```
Framework
├── Rules
│   ├── Rule 1 (severity, category, check_fn, remediation)
│   ├── Rule 2
│   └── ...
├── check(entry, profile) -> ComplianceCheckResult
└── get_rule(rule_id) -> ComplianceRule
```

### ComplianceProfile

A `ComplianceProfile` configures how compliance checks are performed:

| Field | Description |
|-------|-------------|
| `profile_id` | Unique identifier |
| `name` | Human-readable name |
| `enabled_frameworks` | List of frameworks to evaluate |
| `enabled_categories` | Rule categories to include (empty = all) |
| `min_severity` | Minimum severity to report |
| `excluded_rules` | Specific rules to skip |
| `system_classification` | Classification of the AI system |

```python
from rotalabs_comply.frameworks.base import ComplianceProfile, RiskLevel

profile = ComplianceProfile(
    profile_id="healthcare-ai",
    name="Healthcare AI System",
    enabled_frameworks=["HIPAA", "SOC2"],
    min_severity=RiskLevel.MEDIUM,
    system_classification="high_risk",
)
```

### RiskLevel

Violations are classified by severity:

| Level | Weight | Response Time |
|-------|--------|---------------|
| `CRITICAL` | 10 | Immediate action required |
| `HIGH` | 5 | Address within 24-48 hours |
| `MEDIUM` | 2 | Address within 1-2 weeks |
| `LOW` | 1 | Address during regular reviews |
| `INFO` | 0.5 | Informational, no action required |

### Built-in Frameworks

#### EU AI Act

The European Union AI Act (2024) framework includes checks for:

- **Transparency** -- Users informed of AI interaction
- **Human Oversight** -- Documented oversight for high-risk operations
- **Risk Management** -- Risk assessment documentation
- **Technical Documentation** -- Documentation references
- **Data Governance** -- Training data documentation
- **Robustness** -- Error handling
- **Accuracy Monitoring** -- Performance monitoring
- **Cybersecurity** -- Security validation

#### SOC2 Type II

AICPA Trust Service Criteria implementation:

- **Security (CC)** -- Access controls, monitoring, incident response
- **Availability (A)** -- SLA monitoring, recovery objectives
- **Processing Integrity (PI)** -- Input validation
- **Confidentiality (C)** -- Data classification
- **Privacy (P)** -- Privacy notices for personal data

#### HIPAA

Health Insurance Portability and Accountability Act:

- **Access Control** -- Unique user identification, encryption
- **Audit Controls** -- Comprehensive logging
- **Integrity Controls** -- Data integrity verification
- **Authentication** -- Strong authentication, MFA for high-risk
- **Transmission Security** -- Encrypted transmission
- **Privacy** -- Minimum necessary, de-identification

---

## Compliance Check Results

### ComplianceCheckResult

The result of evaluating an audit entry against a framework:

| Field | Description |
|-------|-------------|
| `entry_id` | ID of the checked entry |
| `framework` | Framework name |
| `framework_version` | Framework version |
| `timestamp` | When check was performed |
| `violations` | List of `ComplianceViolation` objects |
| `rules_checked` | Total rules evaluated |
| `rules_passed` | Rules that passed |
| `is_compliant` | True if no violations |

### ComplianceViolation

Details about a specific rule violation:

| Field | Description |
|-------|-------------|
| `rule_id` | Rule identifier |
| `rule_name` | Human-readable name |
| `severity` | `RiskLevel` of violation |
| `description` | What the rule requires |
| `evidence` | Specific evidence from the entry |
| `remediation` | How to fix the violation |
| `entry_id` | Entry that triggered violation |
| `category` | Rule category |
| `framework` | Framework name |

---

## Report Generation

### ComplianceReport

A complete compliance report with all sections:

| Field | Description |
|-------|-------------|
| `id` | Unique report identifier |
| `title` | Report title |
| `framework` | Framework (or "Multiple") |
| `period_start` / `period_end` | Analysis period |
| `generated_at` | Generation timestamp |
| `profile` | `ComplianceProfile` used |
| `sections` | List of `ReportSection` objects |
| `total_entries` | Entries analyzed |
| `violations_count` | Violations found |
| `compliance_score` | Score from 0.0 to 1.0 |
| `status` | "compliant", "non_compliant", or "needs_review" |

### Compliance Scoring

The compliance score is calculated using weighted penalties:

```
Score = 1.0 - (Total Penalty / Max Possible Penalty)

Where:
- Critical violation: 10 points penalty
- High violation: 5 points penalty
- Medium violation: 2 points penalty
- Low violation: 1 point penalty
- Info violation: 0.5 points penalty
```

### Status Determination

| Score | Critical Violations | Status |
|-------|---------------------|--------|
| Any | > 0 | `non_compliant` |
| >= 95% | 0 | `compliant` |
| >= 80% | 0 | `needs_review` |
| < 80% | 0 | `non_compliant` |

### Report Sections

Standard sections generated for each report:

1. **Executive Summary** -- Key metrics, overall status, period overview
2. **Risk Assessment** -- Severity distribution, category breakdown, priority findings
3. **Compliance Matrix** -- Rule-by-rule pass/fail summary per framework
4. **Metrics Summary** -- Volume, safety rates, latency percentiles
5. **Recommendations** -- Prioritized actions (immediate, short-term, long-term)
6. **Audit Summary** -- Daily volumes, peak activity, failure patterns

### Export Formats

| Format | Method | Use Case |
|--------|--------|----------|
| Markdown | `export_markdown()` | Documentation, README files |
| JSON | `export_json()` | API responses, data integration |
| HTML | `export_html()` | Standalone reports, stakeholder sharing |

---

## Custom Frameworks

Extend `BaseFramework` to create custom compliance frameworks:

```python
from rotalabs_comply.frameworks.base import (
    BaseFramework,
    ComplianceRule,
    ComplianceViolation,
    RiskLevel,
)

class MyCustomFramework(BaseFramework):
    def __init__(self):
        rules = [
            ComplianceRule(
                rule_id="CUSTOM-001",
                name="Custom Requirement",
                description="Description of the requirement",
                severity=RiskLevel.MEDIUM,
                category="custom",
                remediation="How to fix violations",
            ),
        ]
        super().__init__(
            name="My Custom Framework",
            version="1.0",
            rules=rules,
        )

    def _check_rule(self, entry, rule):
        # Implement rule checking logic
        if rule.rule_id == "CUSTOM-001":
            if not entry.metadata.get("custom_field"):
                return self._create_violation(
                    entry, rule, "custom_field not set"
                )
        return None

    def _create_violation(self, entry, rule, evidence):
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
```
