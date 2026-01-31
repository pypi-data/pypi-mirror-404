# Audit Logging Tutorial

This tutorial walks through setting up comprehensive audit logging for AI systems, including encryption, storage backends, and retention management.

## Overview

Audit logging is the foundation of AI compliance. It captures interactions with AI systems in a way that supports:

- **Accountability** -- Track who did what, when, and why
- **Verification** -- Prove compliance through documented evidence
- **Investigation** -- Analyze incidents and patterns
- **Reporting** -- Generate compliance reports from audit data

## Basic Audit Logging

### Simple File-Based Logging

The simplest setup uses file storage with hash-only mode (default):

```python
import asyncio
from rotalabs_comply import AuditLogger

async def main():
    # Create logger with file storage
    logger = AuditLogger("/var/log/ai-audit")

    # Log an AI interaction
    entry_id = await logger.log(
        input="What is the weather today?",
        output="I don't have access to real-time weather data.",
        provider="openai",
        model="gpt-4",
        safety_passed=True,
        latency_ms=150.0,
    )

    print(f"Logged entry: {entry_id}")

asyncio.run(main())
```

This creates JSONL files in `/var/log/ai-audit/` named by date (e.g., `audit_20260129.jsonl`).

### Understanding Hash-Only Mode

By default, only SHA-256 hashes of content are stored:

```python
# What gets stored in hash-only mode
{
    "id": "abc-123-def",
    "timestamp": "2026-01-29T10:30:00",
    "input_hash": "a0c299...",  # SHA-256 of input
    "output_hash": "b1d388...",  # SHA-256 of output
    "input_content": null,       # Not stored
    "output_content": null,      # Not stored
    "provider": "openai",
    "model": "gpt-4",
    "safety_passed": true,
    ...
}
```

Benefits:
- No sensitive data stored
- Content can be verified later by comparing hashes
- Compliant with data minimization principles

## Encrypted Audit Logging

When you need full audit trails but want to protect content:

### Setting Up Encryption

```python
import asyncio
from rotalabs_comply import AuditLogger, EncryptionManager

async def main():
    # Create encryption manager (generates key automatically)
    encryption = EncryptionManager()

    # IMPORTANT: Save the key securely!
    key = encryption.get_key()
    print(f"Save this key: {key.decode()}")

    # Create logger with encryption
    logger = AuditLogger(
        storage="/var/log/ai-audit",
        encryption=encryption,
        store_content=True,  # Enable content storage
    )

    # Log entries (content will be encrypted)
    entry_id = await logger.log(
        input="Tell me about patient records",
        output="Patient records are confidential...",
        provider="anthropic",
        model="claude-3-opus",
        safety_passed=True,
        latency_ms=200.0,
    )

    # Later, retrieve and decrypt
    entry = await logger.get_entry(entry_id)
    if entry and entry.input_content:
        original_input = logger.decrypt_content(entry.input_content)
        print(f"Original: {original_input}")

asyncio.run(main())
```

### Key Management Best Practices

```python
import os
from rotalabs_comply import EncryptionManager

# Option 1: Generate and save to environment
encryption = EncryptionManager()
os.environ["AUDIT_ENCRYPTION_KEY"] = encryption.get_key().decode()

# Option 2: Load from environment
key = os.environ.get("AUDIT_ENCRYPTION_KEY")
if key:
    encryption = EncryptionManager(key.encode())
else:
    raise ValueError("Encryption key not configured")

# Option 3: Load from AWS Secrets Manager
import boto3

def get_encryption_key():
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId="audit-encryption-key")
    return response["SecretString"].encode()

encryption = EncryptionManager(get_encryption_key())
```

!!! danger "Never Commit Keys"
    Never commit encryption keys to version control. Use environment variables, secrets managers, or secure key vaults.

## Storage Backends

### File Storage

Local JSONL files with automatic rotation:

```python
from rotalabs_comply import AuditLogger
from rotalabs_comply.audit import FileStorage

# Using path string (FileStorage created automatically)
logger = AuditLogger("/var/log/ai-audit")

# Or explicit FileStorage with custom rotation
storage = FileStorage(
    path="/var/log/ai-audit",
    rotation_size_mb=50,  # Rotate at 50MB (default: 100MB)
)
logger = AuditLogger(storage)
```

File structure:
```
/var/log/ai-audit/
├── audit_20260128.jsonl
├── audit_20260128_001.jsonl  # Rotated file
├── audit_20260129.jsonl
└── ...
```

### S3 Storage

Cloud-native storage with AWS S3:

```python
from rotalabs_comply import AuditLogger
from rotalabs_comply.audit import S3Storage

# Create S3 storage backend
storage = S3Storage(
    bucket="my-audit-bucket",
    prefix="prod/ai-audit/",
    region="us-west-2",
)

# Create logger
logger = AuditLogger(storage)

# Log entries (stored as individual JSON files in S3)
entry_id = await logger.log(
    input="Query",
    output="Response",
    provider="openai",
    model="gpt-4",
    safety_passed=True,
    latency_ms=100.0,
)
# Stored at: s3://my-audit-bucket/prod/ai-audit/2026-01-29/abc-123.json
```

S3 Lifecycle Policy for retention:
```json
{
    "Rules": [
        {
            "ID": "audit-log-retention",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "prod/ai-audit/"
            },
            "Expiration": {
                "Days": 365
            }
        }
    ]
}
```

### Memory Storage

For testing and development:

```python
from rotalabs_comply import AuditLogger
from rotalabs_comply.audit import MemoryStorage

# Create memory storage with entry limit
storage = MemoryStorage(max_entries=1000)
logger = AuditLogger(storage)

# Log entries (stored in memory)
entry_id = await logger.log(
    input="Test",
    output="Test response",
    provider="test",
    model="test-model",
    safety_passed=True,
    latency_ms=10.0,
)

# Check entry count
count = await storage.count()
print(f"Stored entries: {count}")
```

## Comprehensive Metadata

### Capturing Rich Context

```python
entry_id = await logger.log(
    # Core content
    input="Summarize the quarterly report",
    output="Q4 showed 15% revenue growth...",

    # Provider information
    provider="openai",
    model="gpt-4-turbo",

    # Session tracking
    conversation_id="conv-abc-123",  # Link related interactions

    # Safety information
    safety_passed=True,
    detectors_triggered=[],  # Empty if all passed
    block_reason=None,       # Set if blocked
    alerts=[],               # Warning messages

    # Performance
    latency_ms=450.5,
    input_tokens=150,
    output_tokens=200,

    # Custom metadata
    metadata={
        "user_id": "user-123",
        "session_id": "session-456",
        "department": "finance",
        "use_case": "report_summarization",
        "sensitivity": "internal",
    },
)
```

### Safety Event Logging

When safety checks fail:

```python
# Log a blocked request
entry_id = await logger.log(
    input="How to hack a bank?",
    output="",  # Empty - request was blocked
    provider="openai",
    model="gpt-4",
    safety_passed=False,
    detectors_triggered=["harmful_content", "illegal_activity"],
    block_reason="Content violates safety policy",
    alerts=["Harmful request detected", "User warned"],
    latency_ms=50.0,
    metadata={
        "user_id": "user-789",
        "blocked_at": "input",  # Blocked before API call
    },
)
```

## Querying Audit Logs

### Retrieve Single Entry

```python
# Get entry by ID
entry = await logger.get_entry("abc-123-def")

if entry:
    print(f"Provider: {entry.provider}")
    print(f"Model: {entry.model}")
    print(f"Safety passed: {entry.safety_passed}")
    print(f"Latency: {entry.latency_ms}ms")

    # Decrypt content if encrypted
    if entry.input_content and logger.encryption:
        original = logger.decrypt_content(entry.input_content)
        print(f"Input: {original}")
```

### Query by Time Range

```python
from datetime import datetime, timedelta

# Get entries from the last 7 days
end = datetime.utcnow()
start = end - timedelta(days=7)

entries = await logger.get_entries(start, end)

print(f"Found {len(entries)} entries")

# Analyze entries
safety_failures = sum(1 for e in entries if not e.safety_passed)
avg_latency = sum(e.latency_ms for e in entries) / len(entries)

print(f"Safety failures: {safety_failures}")
print(f"Average latency: {avg_latency:.2f}ms")
```

## Retention Management

### Automatic Cleanup

```python
from rotalabs_comply import AuditLogger

# Set retention period when creating logger
logger = AuditLogger(
    storage="/var/log/ai-audit",
    retention_days=365,  # Keep for 1 year
)

# Manually trigger cleanup
deleted_count = await logger.cleanup_expired()
print(f"Deleted {deleted_count} expired entries")
```

### Scheduled Cleanup

For production, schedule cleanup as a background job:

```python
import asyncio
from datetime import datetime

async def cleanup_job():
    while True:
        # Run at 2 AM daily
        now = datetime.now()
        next_run = now.replace(hour=2, minute=0, second=0)
        if next_run <= now:
            next_run = next_run + timedelta(days=1)

        sleep_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(sleep_seconds)

        # Run cleanup
        deleted = await logger.cleanup_expired()
        print(f"[{datetime.now()}] Cleaned up {deleted} entries")

# Start as background task
asyncio.create_task(cleanup_job())
```

## Integration with AI Frameworks

### LangChain Integration

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from rotalabs_comply import AuditLogger, EncryptionManager
import time

class AuditedChatModel:
    def __init__(self, model_name: str, logger: AuditLogger):
        self.llm = ChatOpenAI(model=model_name)
        self.logger = logger
        self.model_name = model_name

    async def invoke(self, messages, **kwargs):
        # Extract input
        input_text = messages[-1].content if messages else ""

        # Call LLM and measure latency
        start = time.perf_counter()
        response = await self.llm.ainvoke(messages, **kwargs)
        latency_ms = (time.perf_counter() - start) * 1000

        # Log the interaction
        await self.logger.log(
            input=input_text,
            output=response.content,
            provider="openai",
            model=self.model_name,
            safety_passed=True,
            latency_ms=latency_ms,
            metadata=kwargs,
        )

        return response

# Usage
encryption = EncryptionManager()
logger = AuditLogger("/var/log/ai-audit", encryption=encryption, store_content=True)
chat = AuditedChatModel("gpt-4", logger)

response = await chat.invoke([HumanMessage(content="Hello!")])
```

### OpenAI SDK Integration

```python
import openai
from rotalabs_comply import AuditLogger
import time

class AuditedOpenAI:
    def __init__(self, logger: AuditLogger):
        self.client = openai.AsyncOpenAI()
        self.logger = logger

    async def chat_completion(self, messages, model="gpt-4", **kwargs):
        # Extract input from last user message
        input_text = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            ""
        )

        start = time.perf_counter()
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        latency_ms = (time.perf_counter() - start) * 1000

        output_text = response.choices[0].message.content

        await self.logger.log(
            input=input_text,
            output=output_text,
            provider="openai",
            model=model,
            safety_passed=True,
            latency_ms=latency_ms,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

        return response

# Usage
logger = AuditLogger("/var/log/ai-audit")
client = AuditedOpenAI(logger)

response = await client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Best Practices

### 1. Always Log Safety Events

```python
# Log even when requests are blocked
try:
    response = await llm.generate(prompt)
    await logger.log(input=prompt, output=response, safety_passed=True, ...)
except SafetyError as e:
    await logger.log(
        input=prompt,
        output="",
        safety_passed=False,
        block_reason=str(e),
        ...
    )
    raise
```

### 2. Use Structured Metadata

```python
# Consistent metadata schema
metadata = {
    "user_id": str,        # Required
    "session_id": str,     # Required
    "department": str,     # Optional
    "use_case": str,       # Optional
    "sensitivity": str,    # Optional
}
```

### 3. Handle Encryption Key Rotation

```python
# Store key version with encrypted data
metadata = {
    "encryption_key_version": "v2",
}

# Maintain key versions for decryption
keys = {
    "v1": old_key,
    "v2": current_key,
}
```

### 4. Monitor Audit Log Health

```python
async def check_audit_health():
    count = await storage.count()
    entries = await logger.get_entries(
        datetime.utcnow() - timedelta(hours=1),
        datetime.utcnow()
    )

    metrics = {
        "total_entries": count,
        "hourly_volume": len(entries),
        "safety_failures": sum(1 for e in entries if not e.safety_passed),
    }

    return metrics
```
