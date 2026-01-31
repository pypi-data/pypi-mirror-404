# Audit Module

Audit logging infrastructure including the main logger, encryption utilities, and storage backends.

---

## AuditLogger

::: rotalabs_comply.audit.logger.AuditLogger
    options:
      show_bases: false

Main audit logging interface for AI compliance.

### Constructor

```python
AuditLogger(
    storage: Union[StorageBackend, str],
    encryption: Optional[EncryptionManager] = None,
    store_content: bool = False,
    retention_days: int = 365,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `storage` | `Union[StorageBackend, str]` | Required | Storage backend or file path |
| `encryption` | `Optional[EncryptionManager]` | `None` | Encryption manager for content |
| `store_content` | `bool` | `False` | Store actual content vs hashes |
| `retention_days` | `int` | `365` | Days to retain entries |

### Methods

#### log

```python
async def log(
    input: str,
    output: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    conversation_id: Optional[str] = None,
    safety_passed: bool = True,
    detectors_triggered: Optional[List[str]] = None,
    block_reason: Optional[str] = None,
    alerts: Optional[List[str]] = None,
    latency_ms: float = 0.0,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str
```

Log an AI interaction and return the entry ID.

**Example:**

```python
entry_id = await logger.log(
    input="Tell me a joke",
    output="Why did the chicken...",
    provider="anthropic",
    model="claude-3-opus",
    safety_passed=True,
    latency_ms=250.5,
    metadata={"session_id": "abc123"},
)
```

#### get_entry

```python
async def get_entry(entry_id: str) -> Optional[AuditEntry]
```

Retrieve an audit entry by ID.

**Example:**

```python
entry = await logger.get_entry("abc-123-def")
if entry:
    print(f"Safety passed: {entry.safety_passed}")
```

#### get_entries

```python
async def get_entries(start: datetime, end: datetime) -> List[AuditEntry]
```

Retrieve all entries within a time range.

**Example:**

```python
from datetime import datetime, timedelta

end = datetime.utcnow()
start = end - timedelta(days=7)
entries = await logger.get_entries(start, end)
```

#### cleanup_expired

```python
async def cleanup_expired() -> int
```

Delete entries older than the retention period. Returns count of deleted entries.

**Example:**

```python
deleted = await logger.cleanup_expired()
print(f"Cleaned up {deleted} expired entries")
```

#### decrypt_content

```python
def decrypt_content(encrypted_content: str) -> str
```

Decrypt encrypted content from an audit entry.

**Raises:**

- `ValueError`: If no encryption manager is configured
- `cryptography.fernet.InvalidToken`: If decryption fails

**Example:**

```python
entry = await logger.get_entry("abc-123")
if entry and entry.input_content:
    original = logger.decrypt_content(entry.input_content)
```

---

## Encryption

### EncryptionManager

::: rotalabs_comply.audit.encryption.EncryptionManager
    options:
      show_bases: false

High-level encryption manager for string data.

### Constructor

```python
EncryptionManager(key: Optional[bytes] = None)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `Optional[bytes]` | Auto-gen | Fernet encryption key |

### Methods

#### encrypt

```python
def encrypt(data: str) -> str
```

Encrypt a string and return base64-encoded result.

#### decrypt

```python
def decrypt(data: str) -> str
```

Decrypt a base64-encoded encrypted string.

#### get_key

```python
def get_key() -> bytes
```

Get the encryption key. Store this securely!

**Example:**

```python
from rotalabs_comply import EncryptionManager

manager = EncryptionManager()
encrypted = manager.encrypt("sensitive data")
decrypted = manager.decrypt(encrypted)

# Save key securely
key = manager.get_key()
```

### Helper Functions

#### generate_key

```python
def generate_key() -> bytes
```

Generate a new Fernet encryption key.

**Example:**

```python
from rotalabs_comply import generate_key

key = generate_key()
print(len(key))  # 44
```

#### encrypt

```python
def encrypt(data: bytes, key: bytes) -> bytes
```

Encrypt raw bytes using Fernet symmetric encryption.

#### decrypt

```python
def decrypt(data: bytes, key: bytes) -> bytes
```

Decrypt data that was encrypted with Fernet.

#### hash_content

```python
def hash_content(content: str) -> str
```

Compute SHA-256 hash of string content.

**Example:**

```python
from rotalabs_comply import hash_content

content_hash = hash_content("hello world")
# Returns: 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
```

---

## Storage Backends

### StorageBackend Protocol

::: rotalabs_comply.audit.storage.StorageBackend
    options:
      show_bases: false

Protocol defining the interface for audit log storage backends.

**Required Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `write` | `async (entry: AuditEntry) -> str` | Write entry, return ID |
| `read` | `async (entry_id: str) -> Optional[AuditEntry]` | Read entry by ID |
| `list_entries` | `async (start: datetime, end: datetime) -> List[AuditEntry]` | List entries in range |
| `delete` | `async (entry_id: str) -> bool` | Delete entry, return success |
| `count` | `async () -> int` | Count total entries |

---

### FileStorage

::: rotalabs_comply.audit.storage.FileStorage
    options:
      show_bases: false

File-based storage backend using JSONL format.

### Constructor

```python
FileStorage(path: str, rotation_size_mb: int = 100)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | Required | Directory for audit files |
| `rotation_size_mb` | `int` | `100` | Max file size before rotation |

**File Structure:**

```
{path}/
├── audit_20260128.jsonl
├── audit_20260128_001.jsonl  # Rotated
├── audit_20260129.jsonl
└── ...
```

**Example:**

```python
from rotalabs_comply.audit import FileStorage

storage = FileStorage("/var/log/audit", rotation_size_mb=50)
entry_id = await storage.write(entry)
```

---

### MemoryStorage

::: rotalabs_comply.audit.storage.MemoryStorage
    options:
      show_bases: false

In-memory storage backend for testing and development.

### Constructor

```python
MemoryStorage(max_entries: Optional[int] = None)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_entries` | `Optional[int]` | `None` | Max entries (LRU eviction) |

**Example:**

```python
from rotalabs_comply.audit import MemoryStorage

storage = MemoryStorage(max_entries=1000)
count = await storage.count()
```

!!! warning "Data Persistence"
    Data is lost when the process ends. Use only for testing.

---

### S3Storage

::: rotalabs_comply.audit.storage.S3Storage
    options:
      show_bases: false

AWS S3 storage backend for audit logs.

### Constructor

```python
S3Storage(
    bucket: str,
    prefix: str = "audit/",
    region: Optional[str] = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | `str` | Required | S3 bucket name |
| `prefix` | `str` | `"audit/"` | Key prefix for files |
| `region` | `Optional[str]` | `None` | AWS region |

**Key Structure:**

```
s3://{bucket}/{prefix}{YYYY-MM-DD}/{entry_id}.json
```

**Example:**

```python
from rotalabs_comply.audit import S3Storage

storage = S3Storage(
    bucket="my-audit-bucket",
    prefix="prod/audit/",
    region="us-west-2",
)
```

!!! note "Dependency"
    Requires `boto3`. Install with `pip install rotalabs-comply[s3]`.

---

## AuditEntry (Storage)

::: rotalabs_comply.audit.storage.AuditEntry
    options:
      show_bases: false

Dataclass representing a single audit log entry in storage.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier |
| `timestamp` | `str` | ISO format timestamp |
| `input_hash` | `str` | SHA-256 of input |
| `output_hash` | `str` | SHA-256 of output |
| `input_content` | `Optional[str]` | Input content (if stored) |
| `output_content` | `Optional[str]` | Output content (if stored) |
| `provider` | `Optional[str]` | AI provider |
| `model` | `Optional[str]` | Model identifier |
| `conversation_id` | `Optional[str]` | Conversation ID |
| `safety_passed` | `bool` | Safety check result |
| `detectors_triggered` | `List[str]` | Triggered detectors |
| `block_reason` | `Optional[str]` | Block reason |
| `alerts` | `List[str]` | Alert messages |
| `latency_ms` | `float` | Response latency |
| `input_tokens` | `Optional[int]` | Input token count |
| `output_tokens` | `Optional[int]` | Output token count |
| `metadata` | `Dict[str, Any]` | Custom metadata |

**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict()` | Convert to dictionary |
| `from_dict(data)` | Create from dictionary |

---

## Helper Functions

### create_entry_id

```python
def create_entry_id() -> str
```

Generate a unique entry ID (UUID v4).

**Example:**

```python
from rotalabs_comply.audit.storage import create_entry_id

entry_id = create_entry_id()
# Returns: "550e8400-e29b-41d4-a716-446655440000"
```
