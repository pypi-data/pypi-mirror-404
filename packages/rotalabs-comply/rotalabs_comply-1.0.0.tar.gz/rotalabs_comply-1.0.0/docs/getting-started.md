# Getting Started

## Installation

### Basic Installation

```bash
pip install rotalabs-comply
```

### With Optional Dependencies

```bash
# AWS S3 storage backend
pip install rotalabs-comply[s3]

# All optional dependencies
pip install rotalabs-comply[all]

# Development dependencies
pip install rotalabs-comply[dev]
```

## Core Dependencies

The base package requires:

- `pydantic>=2.0.0` - Data validation and settings management
- `cryptography>=41.0.0` - Fernet encryption for audit logs
- `aiofiles>=23.0.0` - Async file operations

Optional dependencies:

- `boto3>=1.26.0` - AWS S3 storage backend (with `[s3]` extra)

## Basic Usage

### 1. Set Up Audit Logging

```python
import asyncio
from rotalabs_comply import AuditLogger, EncryptionManager

async def main():
    # Create an encrypted audit logger
    encryption = EncryptionManager()
    logger = AuditLogger(
        storage="/var/log/ai-audit",
        encryption=encryption,
        store_content=True,  # Store encrypted content
        retention_days=365,
    )

    # Log an AI interaction
    entry_id = await logger.log(
        input="What is the capital of France?",
        output="The capital of France is Paris.",
        provider="openai",
        model="gpt-4",
        safety_passed=True,
        latency_ms=245.5,
        input_tokens=8,
        output_tokens=7,
        metadata={"session_id": "abc123"},
    )

    print(f"Logged entry: {entry_id}")

    # Retrieve the entry
    entry = await logger.get_entry(entry_id)
    if entry and entry.input_content:
        # Decrypt content if needed
        original_input = logger.decrypt_content(entry.input_content)
        print(f"Original input: {original_input}")

asyncio.run(main())
```

### 2. Check Compliance Against Frameworks

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework

async def main():
    # Create an audit entry to check
    entry = AuditEntry(
        entry_id="test-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="user@example.com",
        action="AI response generation",
        risk_level=RiskLevel.HIGH,
        user_notified=True,  # Required for EU AI Act transparency
        human_oversight=True,  # Required for high-risk operations
        metadata={
            "risk_assessment_documented": True,
            "accuracy_monitored": True,
            "security_validated": True,
        },
    )

    # Create a compliance profile
    profile = ComplianceProfile(
        profile_id="prod-profile",
        name="Production AI System",
        enabled_frameworks=["EU AI Act"],
        min_severity=RiskLevel.LOW,
    )

    # Check compliance
    framework = EUAIActFramework()
    result = await framework.check(entry, profile)

    print(f"Compliant: {result.is_compliant}")
    print(f"Rules checked: {result.rules_checked}")
    print(f"Rules passed: {result.rules_passed}")

    if result.violations:
        print("\nViolations found:")
        for violation in result.violations:
            print(f"  - [{violation.severity.value.upper()}] {violation.rule_name}")
            print(f"    Evidence: {violation.evidence}")
            print(f"    Remediation: {violation.remediation}")

asyncio.run(main())
```

### 3. Generate Compliance Reports

```python
import asyncio
from datetime import datetime, timedelta
from rotalabs_comply import AuditLogger, ReportGenerator
from rotalabs_comply.audit import MemoryStorage
from rotalabs_comply.frameworks.base import ComplianceProfile
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.soc2 import SOC2Framework

async def main():
    # Set up storage and logger
    storage = MemoryStorage()
    logger = AuditLogger(storage)

    # Log some test entries
    for i in range(10):
        await logger.log(
            input=f"Test input {i}",
            output=f"Test output {i}",
            provider="openai",
            model="gpt-4",
            safety_passed=True,
            latency_ms=100 + i * 10,
        )

    # Create report generator with frameworks
    generator = ReportGenerator(
        audit_logger=storage,
        frameworks={
            "eu_ai_act": EUAIActFramework(),
            "soc2": SOC2Framework(),
        },
    )

    # Create compliance profile
    profile = ComplianceProfile(
        profile_id="test",
        name="Test Environment",
        enabled_frameworks=["eu_ai_act", "soc2"],
    )

    # Generate report
    end = datetime.utcnow()
    start = end - timedelta(days=30)

    report = await generator.generate(
        period_start=start,
        period_end=end,
        profile=profile,
    )

    # Export as Markdown
    markdown = generator.export_markdown(report)
    print(markdown)

    # Or export as HTML
    html = generator.export_html(report)
    with open("compliance_report.html", "w") as f:
        f.write(html)

    print(f"\nReport generated: {report.title}")
    print(f"Compliance Score: {report.compliance_score:.2%}")
    print(f"Status: {report.status}")

asyncio.run(main())
```

## Privacy Mode Selection

Choose the appropriate privacy mode for your use case:

=== "Hash-Only (Default)"

    ```python
    # Only stores SHA-256 hashes of content
    logger = AuditLogger(
        storage="/var/log/audit",
        store_content=False,  # Default
    )
    ```

    Best for: Maximum privacy, content verification without storage

=== "Encrypted Content"

    ```python
    # Stores encrypted content with Fernet encryption
    encryption = EncryptionManager()
    logger = AuditLogger(
        storage="/var/log/audit",
        encryption=encryption,
        store_content=True,
    )

    # Save the key securely!
    key = encryption.get_key()
    ```

    Best for: Full audit trails with data protection

=== "Plaintext Content"

    ```python
    # Stores content as-is (no encryption)
    logger = AuditLogger(
        storage="/var/log/audit",
        store_content=True,
        encryption=None,
    )
    ```

    Best for: Development/testing environments only

## Storage Backend Selection

=== "File Storage"

    ```python
    from rotalabs_comply import AuditLogger

    logger = AuditLogger(
        storage="/var/log/ai-audit",  # Directory path
    )
    ```

    - JSONL format with automatic date-based files
    - Automatic rotation when files exceed size limit
    - Good for single-server deployments

=== "S3 Storage"

    ```python
    from rotalabs_comply.audit import S3Storage, AuditLogger

    storage = S3Storage(
        bucket="my-audit-bucket",
        prefix="prod/audit-logs/",
        region="us-west-2",
    )
    logger = AuditLogger(storage)
    ```

    - Requires `boto3` (`pip install rotalabs-comply[s3]`)
    - Uses S3 lifecycle policies for retention
    - Best for cloud-native deployments

=== "Memory Storage"

    ```python
    from rotalabs_comply.audit import MemoryStorage, AuditLogger

    storage = MemoryStorage(max_entries=10000)
    logger = AuditLogger(storage)
    ```

    - Data lost when process ends
    - Good for testing and development
    - Optional entry limit to prevent memory issues

## Next Steps

- Read [Core Concepts](concepts.md) to understand compliance infrastructure
- Follow [Audit Logging Tutorial](tutorials/audit-logging.md) for detailed walkthrough
- See [API Reference](api/core.md) for full documentation
