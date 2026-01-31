# Core Types

Core data models, enumerations, configuration classes, and exceptions for rotalabs-comply.

---

## Enumerations

### RiskLevel

::: rotalabs_comply.core.types.RiskLevel
    options:
      show_bases: false
      members:
        - LOW
        - MEDIUM
        - HIGH
        - CRITICAL

Risk severity levels for compliance classification.

| Level | Value | Description |
|-------|-------|-------------|
| `LOW` | `"low"` | Minor risk with minimal compliance impact |
| `MEDIUM` | `"medium"` | Moderate risk requiring attention |
| `HIGH` | `"high"` | Significant risk requiring immediate action |
| `CRITICAL` | `"critical"` | Severe risk with potential regulatory consequences |

**Example:**

```python
from rotalabs_comply import RiskLevel

level = RiskLevel.HIGH
print(level.value)  # "high"
```

---

### Framework

::: rotalabs_comply.core.types.Framework
    options:
      show_bases: false

Supported regulatory compliance frameworks.

| Framework | Value | Description |
|-----------|-------|-------------|
| `EU_AI_ACT` | `"eu_ai_act"` | European Union AI Act requirements |
| `SOC2` | `"soc2"` | Service Organization Control 2 standards |
| `HIPAA` | `"hipaa"` | Health Insurance Portability and Accountability Act |
| `GDPR` | `"gdpr"` | General Data Protection Regulation |
| `NIST_AI_RMF` | `"nist_ai_rmf"` | NIST AI Risk Management Framework |
| `ISO_42001` | `"iso_42001"` | ISO/IEC 42001 AI Management System |

**Example:**

```python
from rotalabs_comply import Framework

frameworks = [Framework.EU_AI_ACT, Framework.HIPAA]
```

---

## Data Models

### AuditEntry

::: rotalabs_comply.core.types.AuditEntry
    options:
      show_bases: false

A single audit log entry capturing an AI system interaction.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier (UUID, auto-generated) |
| `timestamp` | `datetime` | When the interaction occurred |
| `provider` | `Optional[str]` | AI provider name (e.g., "openai") |
| `model` | `Optional[str]` | Model identifier (e.g., "gpt-4") |
| `conversation_id` | `Optional[str]` | ID linking related interactions |
| `input_hash` | `str` | SHA-256 hash of input content |
| `output_hash` | `str` | SHA-256 hash of output content |
| `input_content` | `Optional[str]` | Actual input (if stored, may be encrypted) |
| `output_content` | `Optional[str]` | Actual output (if stored, may be encrypted) |
| `safety_passed` | `bool` | Whether all safety checks passed |
| `detectors_triggered` | `List[str]` | Safety detectors that flagged content |
| `block_reason` | `Optional[str]` | Reason if interaction was blocked |
| `alerts` | `List[str]` | Alert messages generated |
| `latency_ms` | `float` | Response time in milliseconds |
| `input_tokens` | `Optional[int]` | Number of input tokens |
| `output_tokens` | `Optional[int]` | Number of output tokens |
| `metadata` | `Dict[str, Any]` | Additional custom metadata |

**Example:**

```python
from rotalabs_comply import AuditEntry

entry = AuditEntry(
    provider="openai",
    model="gpt-4",
    input_hash="abc123...",
    output_hash="def456...",
    safety_passed=True,
    latency_ms=245.5,
)
```

---

### ComplianceProfile

::: rotalabs_comply.core.types.ComplianceProfile
    options:
      show_bases: false

Configuration profile defining compliance requirements.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `frameworks` | `List[Framework]` | `[]` | Regulatory frameworks to comply with |
| `risk_level` | `RiskLevel` | `MEDIUM` | Maximum acceptable risk level |
| `required_documentation` | `bool` | `True` | Whether comprehensive docs required |
| `data_retention_days` | `int` | `365` | Days to retain audit data |
| `encrypt_audit_logs` | `bool` | `True` | Whether to encrypt stored logs |
| `store_content` | `bool` | `False` | Store content vs just hashes |
| `custom_policies` | `Dict[str, Any]` | `{}` | Custom policy configurations |

**Example:**

```python
from rotalabs_comply import ComplianceProfile, Framework, RiskLevel

profile = ComplianceProfile(
    frameworks=[Framework.GDPR, Framework.EU_AI_ACT],
    risk_level=RiskLevel.MEDIUM,
    data_retention_days=365,
    store_content=False,
)
```

---

### ComplianceViolation

::: rotalabs_comply.core.types.ComplianceViolation
    options:
      show_bases: false

A single compliance violation detected during checking.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `framework` | `Framework` | The framework that was violated |
| `rule_id` | `str` | Identifier of the violated rule |
| `severity` | `RiskLevel` | Severity of the violation |
| `description` | `str` | Human-readable description |
| `evidence` | `Dict[str, Any]` | Data supporting the finding |
| `remediation` | `str` | Recommended fix steps |
| `timestamp` | `datetime` | When violation was detected |

**Example:**

```python
from rotalabs_comply import ComplianceViolation, Framework, RiskLevel

violation = ComplianceViolation(
    framework=Framework.GDPR,
    rule_id="GDPR-ART13-1",
    severity=RiskLevel.HIGH,
    description="Personal data processed without consent record",
    evidence={"field": "user_email"},
    remediation="Implement consent tracking mechanism",
)
```

---

### ComplianceCheckResult

::: rotalabs_comply.core.types.ComplianceCheckResult
    options:
      show_bases: false

Result of a compliance check against a regulatory framework.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `passed` | `bool` | Whether check passed (no critical violations) |
| `framework` | `Framework` | Framework checked against |
| `violations` | `List[ComplianceViolation]` | Violations found |
| `warnings` | `List[str]` | Non-critical issues |
| `recommendations` | `List[str]` | Improvement suggestions |
| `checked_at` | `datetime` | When check was performed |

**Example:**

```python
from rotalabs_comply import ComplianceCheckResult, Framework

result = ComplianceCheckResult(
    passed=False,
    framework=Framework.SOC2,
    violations=[violation],
    warnings=["Audit log rotation not configured"],
    recommendations=["Enable encryption for audit logs"],
)
```

---

## Configuration Classes

### AuditConfig

::: rotalabs_comply.core.config.AuditConfig
    options:
      show_bases: false

Configuration for audit logging behavior.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `destination` | `str` | Required | File path or S3 URL for logs |
| `encryption_enabled` | `bool` | `True` | Encrypt data at rest |
| `encryption_key` | `Optional[str]` | Auto-gen | Base64-encoded encryption key |
| `retention_days` | `int` | `365` | Days before deletion (1-3650) |
| `max_file_size_mb` | `int` | `100` | Max file size before rotation |
| `rotation_enabled` | `bool` | `True` | Enable automatic rotation |
| `compression_enabled` | `bool` | `False` | Compress audit files |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_s3_destination` | `bool` | Whether destination is S3 URL |
| `s3_bucket` | `Optional[str]` | S3 bucket name if applicable |
| `s3_prefix` | `Optional[str]` | S3 key prefix if applicable |

**Example:**

```python
from rotalabs_comply import AuditConfig

# File storage
config = AuditConfig(
    destination="/var/log/ai-audit/",
    encryption_enabled=True,
    retention_days=365,
)

# S3 storage
s3_config = AuditConfig(
    destination="s3://my-bucket/audit-logs/",
    encryption_enabled=True,
    compression_enabled=True,
)
```

---

### StorageConfig

::: rotalabs_comply.core.config.StorageConfig
    options:
      show_bases: false

Configuration for storage backend selection.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `Literal["file", "s3", "memory"]` | `"file"` | Storage backend type |
| `path` | `Optional[str]` | `None` | Local path for file backend |
| `bucket` | `Optional[str]` | `None` | S3 bucket for S3 backend |
| `prefix` | `Optional[str]` | `None` | S3 key prefix |
| `region` | `Optional[str]` | `None` | AWS region for S3 |

**Example:**

```python
from rotalabs_comply import StorageConfig

# File storage
file_config = StorageConfig(
    backend="file",
    path="/var/log/ai-audit/",
)

# S3 storage
s3_config = StorageConfig(
    backend="s3",
    bucket="my-audit-bucket",
    prefix="prod/audit-logs/",
    region="us-west-2",
)

# Memory storage (testing)
memory_config = StorageConfig(backend="memory")
```

---

## Exceptions

### ComplianceError

::: rotalabs_comply.core.exceptions.ComplianceError
    options:
      show_bases: false

Base exception for all compliance-related errors.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Human-readable error description |
| `details` | `Dict[str, Any]` | Additional error context |

**Example:**

```python
from rotalabs_comply import ComplianceError

try:
    # ... compliance operation
    pass
except ComplianceError as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
```

---

### AuditError

::: rotalabs_comply.core.exceptions.AuditError
    options:
      show_bases: false

Exception for audit logging failures.

Raised when:
- Writing audit entries fails
- Reading audit logs fails
- Audit log rotation fails
- Audit data validation fails

---

### StorageError

::: rotalabs_comply.core.exceptions.StorageError
    options:
      show_bases: false

Exception for storage backend failures.

Raised when:
- Storage backend connection fails
- Reading/writing data fails
- Storage configuration is invalid
- Permission issues occur

---

### EncryptionError

::: rotalabs_comply.core.exceptions.EncryptionError
    options:
      show_bases: false

Exception for encryption/decryption failures.

Raised when:
- Encrypting audit data fails
- Decrypting stored data fails
- Key management issues occur
- Invalid encryption configuration

---

### ValidationError

::: rotalabs_comply.core.exceptions.ValidationError
    options:
      show_bases: false

Exception for data validation failures.

**Additional Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `field` | `Optional[str]` | Field that failed validation |
| `value` | `Optional[Any]` | Value that caused failure |

**Example:**

```python
from rotalabs_comply import ValidationError

try:
    # ... validation
    pass
except ValidationError as e:
    print(f"Field: {e.field}")
    print(f"Value: {e.value}")
```

---

### FrameworkError

::: rotalabs_comply.core.exceptions.FrameworkError
    options:
      show_bases: false

Exception for framework-related failures.

**Additional Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `framework` | `Optional[str]` | Framework that caused the error |

Raised when:
- Unsupported framework operations
- Framework rule validation fails
- Framework configuration errors
- Incompatible framework combinations
