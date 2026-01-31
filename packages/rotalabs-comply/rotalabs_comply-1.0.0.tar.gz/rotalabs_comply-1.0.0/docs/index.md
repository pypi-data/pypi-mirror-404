# rotalabs-comply

Comprehensive AI compliance and audit logging infrastructure for regulatory adherence.

## What is rotalabs-comply?

`rotalabs-comply` provides a complete toolkit for ensuring AI systems meet regulatory compliance requirements. It offers:

- **Audit Logging** -- Comprehensive logging of AI interactions with encryption, multiple storage backends (file, S3, memory), and configurable retention policies
- **Compliance Frameworks** -- Built-in support for EU AI Act, SOC2 Type II, HIPAA, GDPR, NIST AI RMF, ISO 42001, and MAS FEAT with extensible framework architecture
- **Privacy-First Design** -- Hash-only mode for privacy-preserving audit trails, or encrypted content storage when full records are needed
- **Report Generation** -- Automated compliance reports with executive summaries, risk assessments, and remediation recommendations

## Package Overview

```
rotalabs_comply/
├── core/              # Core types, configuration, and exceptions
│   ├── types          # RiskLevel, Framework, AuditEntry, ComplianceProfile
│   ├── config         # AuditConfig, StorageConfig
│   └── exceptions     # ComplianceError hierarchy
├── audit/             # Audit logging infrastructure
│   ├── logger         # AuditLogger main interface
│   ├── encryption     # EncryptionManager, Fernet encryption
│   └── storage        # FileStorage, MemoryStorage, S3Storage
├── frameworks/        # Compliance framework implementations
│   ├── base           # BaseFramework, ComplianceRule, ComplianceFramework
│   ├── eu_ai_act      # EU AI Act (2024) compliance checks
│   ├── soc2           # SOC2 Type II Trust Service Criteria
│   ├── hipaa          # HIPAA Security and Privacy Rules
│   ├── gdpr           # GDPR data protection compliance
│   ├── nist_ai_rmf    # NIST AI Risk Management Framework
│   ├── iso_42001      # ISO/IEC 42001:2023 AI Management System
│   └── mas            # MAS FEAT AI governance for financial services
├── reports/           # Report generation
│   ├── generator      # ReportGenerator, ComplianceReport
│   └── templates      # ReportTemplate, ReportSection, section generators
└── utils/             # Utility functions
    └── helpers        # Period formatting, statistics, JSON serialization
```

## Supported Compliance Frameworks

| Framework | Rules | Description | Categories |
|-----------|-------|-------------|------------|
| **EU AI Act** | 8 | European Union AI regulation (2024) | Transparency, oversight, risk management, documentation, security |
| **SOC2 Type II** | 10 | AICPA Trust Service Criteria | Security, availability, processing integrity, confidentiality, privacy |
| **HIPAA** | 8 | Health data protection (US) | Access control, audit, integrity, authentication, transmission, privacy |
| **GDPR** | 14 | EU General Data Protection Regulation | Data protection, legal basis, consent, transparency, data subject rights, security, accountability |
| **NIST AI RMF** | 15 | NIST AI Risk Management Framework 1.0 | Governance, context, risk identification, measurement, risk treatment |
| **ISO/IEC 42001** | 23 | AI Management System standard (2023) | Context, leadership, planning, support, operation, performance, improvement |
| **MAS FEAT** | 18 | Singapore financial AI governance | Fairness, ethics, accountability, transparency, model risk, data governance, operations |

## Key Features

### Privacy Modes

Choose the right privacy level for your compliance requirements:

- **Hash-Only Mode** (default): Store SHA-256 hashes of inputs/outputs for verification without exposing content
- **Encrypted Mode**: Store encrypted content when you need full audit trails with data protection
- **Plaintext Mode**: Store content as-is for internal development environments

### Storage Backends

Flexible storage options for different deployment scenarios:

- **FileStorage**: Local JSONL files with automatic rotation
- **S3Storage**: AWS S3 for cloud-native deployments with lifecycle management
- **MemoryStorage**: In-memory storage for testing and development

### Report Formats

Generate compliance reports in multiple formats:

- **Markdown**: Human-readable documentation
- **JSON**: Machine-readable for integration
- **HTML**: Standalone reports for stakeholders

## Quick Links

- [Getting Started](getting-started.md) - Installation and first steps
- [Core Concepts](concepts.md) - Understanding compliance infrastructure
- [API Reference](api/core.md) - Detailed API documentation
- [Tutorials](tutorials/audit-logging.md) - Step-by-step guides

## Use Cases

### Enterprise AI Governance

Track all AI interactions across your organization with centralized audit logging, ensuring consistent compliance with internal policies and external regulations.

### Healthcare AI Applications

Meet HIPAA requirements for AI systems processing Protected Health Information (PHI) with encryption, access controls, and comprehensive audit trails.

### EU AI Act Compliance

Prepare for EU AI Act requirements with built-in checks for transparency, human oversight, risk management, and technical documentation.

### SOC2 Audits

Demonstrate operational effectiveness of security controls for AI systems with audit logs and compliance reports suitable for SOC2 Type II audits.
