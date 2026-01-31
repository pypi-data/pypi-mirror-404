# Compliance Checking Tutorial

This tutorial covers using the built-in compliance frameworks (EU AI Act, SOC2, HIPAA, GDPR, NIST AI RMF, ISO 42001, and MAS FEAT) to evaluate AI system operations against regulatory requirements.

## Overview

Compliance checking evaluates audit entries against regulatory frameworks to identify:

- **Violations** -- Specific rules that were not followed
- **Risk levels** -- Severity of identified issues
- **Remediation** -- Steps to fix violations
- **Gaps** -- Areas needing improvement

## Understanding Compliance Frameworks

### Framework Structure

Each framework consists of rules organized by category:

```
Framework (e.g., EU AI Act)
├── Category: Transparency
│   ├── Rule: User Notification (EUAI-002)
│   └── ...
├── Category: Oversight
│   ├── Rule: Human Oversight Documentation (EUAI-001)
│   └── ...
├── Category: Risk Management
│   ├── Rule: Risk Assessment (EUAI-003)
│   └── ...
└── ...
```

### Creating Audit Entries for Compliance

Audit entries need specific fields for compliance checking:

```python
from datetime import datetime
from rotalabs_comply.frameworks.base import AuditEntry, RiskLevel

entry = AuditEntry(
    # Required identifiers
    entry_id="entry-001",
    timestamp=datetime.utcnow(),

    # Event classification
    event_type="inference",       # Type of operation
    actor="user@example.com",     # Who performed it
    action="AI response generation",

    # Resource being accessed
    resource="customer_support_model",
    system_id="prod-ai-001",

    # Risk and data classification
    risk_level=RiskLevel.HIGH,
    data_classification="confidential",

    # Compliance-relevant flags
    user_notified=True,           # Transparency: user knows about AI
    human_oversight=True,         # Oversight: human reviewed
    error_handled=True,           # Robustness: errors handled gracefully
    documentation_ref="DOC-001",  # Documentation: reference to docs

    # Framework-specific metadata
    metadata={
        # EU AI Act
        "risk_assessment_documented": True,
        "accuracy_monitored": True,
        "security_validated": True,
        "data_governance_documented": True,

        # SOC2
        "access_controlled": True,
        "monitored": True,
        "change_approved": True,

        # HIPAA (if PHI involved)
        "encryption_enabled": True,
        "authenticated": True,
        "purpose_documented": True,
        "minimum_necessary_applied": True,
    },
)
```

## EU AI Act Compliance

The EU AI Act (2024) regulates AI systems based on risk level. The framework focuses on high-risk system requirements.

### Rule Categories

| Category | Focus |
|----------|-------|
| `transparency` | User notification of AI interaction |
| `oversight` | Human oversight documentation |
| `risk_management` | Risk assessment, error handling, accuracy |
| `documentation` | Technical and data governance docs |
| `security` | Cybersecurity measures |

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    # Create framework
    framework = EUAIActFramework()

    # List available rules
    print("EU AI Act Rules:")
    for rule in framework.rules:
        print(f"  {rule.rule_id}: {rule.name} [{rule.severity.value}]")

    # Create an audit entry
    entry = AuditEntry(
        entry_id="eu-test-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="api-user",
        action="AI chatbot response",
        risk_level=RiskLevel.HIGH,
        user_notified=True,
        human_oversight=True,
        metadata={
            "risk_assessment_documented": True,
            "security_validated": True,
        },
    )

    # Create profile
    profile = ComplianceProfile(
        profile_id="eu-ai-profile",
        name="EU AI Act Compliance",
        enabled_frameworks=["EU AI Act"],
    )

    # Check compliance
    result = await framework.check(entry, profile)

    print(f"\nCompliance Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Rules checked: {result.rules_checked}")
    print(f"  Rules passed: {result.rules_passed}")

    if result.violations:
        print(f"\nViolations ({len(result.violations)}):")
        for v in result.violations:
            print(f"  [{v.severity.value.upper()}] {v.rule_name}")
            print(f"    Evidence: {v.evidence}")

asyncio.run(main())
```

### Key Requirements

**EUAI-001: Human Oversight**
```python
# For high-risk operations, human_oversight must be True
entry = AuditEntry(
    ...,
    risk_level=RiskLevel.HIGH,
    human_oversight=True,  # Required for high-risk
)
```

**EUAI-002: Transparency**
```python
# For user-facing interactions, user must be notified
entry = AuditEntry(
    ...,
    event_type="inference",  # User-facing event
    user_notified=True,      # User knows it's AI
)
```

**EUAI-003: Risk Assessment**
```python
# High-risk operations need documented risk assessment
entry = AuditEntry(
    ...,
    risk_level=RiskLevel.HIGH,
    metadata={"risk_assessment_documented": True},
)
```

## SOC2 Compliance

SOC2 Type II evaluates operational effectiveness of security controls based on AICPA Trust Service Criteria.

### Trust Service Categories

| Category | Code | Focus |
|----------|------|-------|
| Security | CC | Access controls, monitoring, incident response |
| Availability | A | SLA monitoring, recovery objectives |
| Processing Integrity | PI | Input validation, data accuracy |
| Confidentiality | C | Data classification |
| Privacy | P | Privacy notices for personal data |

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.soc2 import SOC2Framework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = SOC2Framework()

    # List categories
    categories = framework.list_categories()
    print(f"SOC2 Categories: {categories}")

    # Create audit entry with SOC2-relevant metadata
    entry = AuditEntry(
        entry_id="soc2-test-001",
        timestamp=datetime.utcnow(),
        event_type="data_access",
        actor="admin@company.com",  # Authenticated user
        action="Query customer database",
        system_id="prod-db-001",
        data_classification="confidential",
        metadata={
            "access_controlled": True,
            "monitored": True,
            "change_approved": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="soc2-profile",
        name="SOC2 Compliance",
        enabled_frameworks=["SOC2 Type II"],
    )

    result = await framework.check(entry, profile)

    print(f"\nSOC2 Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Violations: {len(result.violations)}")

asyncio.run(main())
```

### Key Requirements

**CC6.1: Logical Access Controls**
```python
# All access events need authentication and authorization
entry = AuditEntry(
    ...,
    event_type="data_access",
    actor="user@company.com",  # Must be authenticated (not "anonymous")
    metadata={"access_controlled": True},
)
```

**CC6.3: Change Management**
```python
# Changes need approval and documentation
entry = AuditEntry(
    ...,
    event_type="deployment",
    documentation_ref="CHG-001",  # Change ticket
    metadata={"change_approved": True},
)
```

**C1.1: Confidentiality Classification**
```python
# Data must be classified
entry = AuditEntry(
    ...,
    event_type="data_access",
    data_classification="confidential",  # Not "unclassified"
)
```

## HIPAA Compliance

HIPAA applies to systems processing Protected Health Information (PHI). Rules are only evaluated for PHI-related entries.

### PHI Detection

The framework identifies PHI-related entries by data classification:

```python
# These classifications trigger HIPAA evaluation
phi_classifications = {
    "PHI", "ePHI", "protected_health_information",
    "health_data", "medical", "clinical"
}
```

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.hipaa import HIPAAFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = HIPAAFramework()

    # PHI-related entry (HIPAA rules apply)
    phi_entry = AuditEntry(
        entry_id="hipaa-test-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="doctor@hospital.com",
        action="AI diagnostic assistance",
        data_classification="PHI",  # Triggers HIPAA
        metadata={
            "access_controlled": True,
            "encryption_enabled": True,
            "authenticated": True,
            "purpose_documented": True,
            "minimum_necessary_applied": True,
        },
    )

    # Non-PHI entry (HIPAA rules don't apply)
    non_phi_entry = AuditEntry(
        entry_id="hipaa-test-002",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="user@company.com",
        action="General AI query",
        data_classification="internal",  # Not PHI
    )

    profile = ComplianceProfile(
        profile_id="hipaa-profile",
        name="HIPAA Compliance",
        enabled_frameworks=["HIPAA"],
    )

    # Check PHI entry
    result1 = await framework.check(phi_entry, profile)
    print(f"PHI Entry - Rules checked: {result1.rules_checked}")

    # Check non-PHI entry
    result2 = await framework.check(non_phi_entry, profile)
    print(f"Non-PHI Entry - Rules checked: {result2.rules_checked}")  # 0

asyncio.run(main())
```

### Key Requirements

**164.312(a): Access Control**
```python
# PHI access requires authentication, authorization, and encryption
entry = AuditEntry(
    ...,
    data_classification="PHI",
    actor="nurse@hospital.com",  # Authenticated
    metadata={
        "access_controlled": True,
        "encryption_enabled": True,
    },
)
```

**164.312(d): Authentication**
```python
# Strong authentication required, MFA for high-risk
entry = AuditEntry(
    ...,
    event_type="bulk_access",  # High-risk operation
    data_classification="PHI",
    metadata={
        "authenticated": True,
        "mfa_verified": True,  # Required for high-risk
    },
)
```

**164.502: Minimum Necessary**
```python
# PHI use must be limited to minimum necessary
entry = AuditEntry(
    ...,
    data_classification="PHI",
    metadata={
        "purpose_documented": True,
        "minimum_necessary_applied": True,
    },
)
```

## Multi-Framework Compliance

Check against multiple frameworks simultaneously:

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.soc2 import SOC2Framework
from rotalabs_comply.frameworks.hipaa import HIPAAFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    # Initialize all frameworks
    frameworks = {
        "eu_ai_act": EUAIActFramework(),
        "soc2": SOC2Framework(),
        "hipaa": HIPAAFramework(),
    }

    # Create comprehensive entry
    entry = AuditEntry(
        entry_id="multi-test-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="clinician@hospital.eu",
        action="AI-assisted diagnosis",
        system_id="diag-ai-001",
        risk_level=RiskLevel.HIGH,
        data_classification="PHI",  # HIPAA relevant
        user_notified=True,
        human_oversight=True,
        documentation_ref="DOC-DIAG-001",
        metadata={
            # EU AI Act
            "risk_assessment_documented": True,
            "accuracy_monitored": True,
            "security_validated": True,

            # SOC2
            "access_controlled": True,
            "monitored": True,

            # HIPAA
            "encryption_enabled": True,
            "authenticated": True,
            "purpose_documented": True,
            "minimum_necessary_applied": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="multi-framework",
        name="Multi-Framework Compliance",
        enabled_frameworks=["EU AI Act", "SOC2 Type II", "HIPAA"],
    )

    # Check against all frameworks
    all_violations = []
    for name, framework in frameworks.items():
        result = await framework.check(entry, profile)
        all_violations.extend(result.violations)
        print(f"\n{name}:")
        print(f"  Compliant: {result.is_compliant}")
        print(f"  Violations: {len(result.violations)}")

    # Overall summary
    print(f"\n=== Overall Summary ===")
    print(f"Total violations: {len(all_violations)}")

    # Group by severity
    for severity in ["critical", "high", "medium", "low"]:
        count = sum(
            1 for v in all_violations
            if v.severity.value.lower() == severity
        )
        if count > 0:
            print(f"  {severity.upper()}: {count}")

asyncio.run(main())
```

## GDPR Compliance

The GDPR framework enforces data protection requirements for processing personal data of EU residents.

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.gdpr import GDPRFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = GDPRFramework()

    # List categories
    categories = framework.list_categories()
    print(f"GDPR Categories: {categories}")

    # Create audit entry for personal data processing
    entry = AuditEntry(
        entry_id="gdpr-test-001",
        timestamp=datetime.utcnow(),
        event_type="data_processing",
        actor="analyst@company.eu",
        action="Process customer profiles",
        data_classification="pii",  # Triggers GDPR rules
        metadata={
            # Article 5 & 6: Lawful basis
            "lawful_basis_documented": True,
            "lawful_basis": "consent",
            "purpose_documented": True,

            # Article 7: Consent conditions
            "consent_recorded": True,
            "consent_specific": True,
            "consent_informed": True,

            # Article 32: Security
            "encryption_applied": True,
            "access_controlled": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="gdpr-profile",
        name="GDPR Compliance",
        enabled_frameworks=["GDPR"],
    )

    result = await framework.check(entry, profile)

    print(f"\nGDPR Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Violations: {len(result.violations)}")

asyncio.run(main())
```

### Automated Decision-Making (Article 22)

```python
# Entry for AI-driven automated decision with significant effects
entry = AuditEntry(
    entry_id="gdpr-ai-001",
    timestamp=datetime.utcnow(),
    event_type="automated_decision",
    actor="ai-system@company.eu",
    action="Credit eligibility determination",
    data_classification="personal",
    metadata={
        "significant_effect": True,  # Triggers Article 22
        "human_intervention_available": True,
        "right_to_contest_enabled": True,
        "logic_explained": True,
    },
)
```

## NIST AI RMF Compliance

The NIST AI Risk Management Framework provides voluntary guidance for managing AI risks across the lifecycle.

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.nist_ai_rmf import NISTAIRMFFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = NISTAIRMFFramework()

    # Create entry for high-risk AI deployment
    entry = AuditEntry(
        entry_id="nist-test-001",
        timestamp=datetime.utcnow(),
        event_type="deployment",
        actor="mlops@company.com",
        action="Deploy production model",
        risk_level=RiskLevel.HIGH,
        documentation_ref="DOC-DEPLOY-001",
        metadata={
            # GOVERN function
            "governance_documented": True,
            "governance_approval": True,
            "accountability_documented": True,

            # MAP function
            "system_context_documented": True,
            "ai_categorization_documented": True,
            "intended_use_documented": True,
            "benefit_cost_assessed": True,

            # MEASURE function
            "trustworthiness_evaluated": True,
            "risk_tracked": True,

            # MANAGE function
            "deployment_decision_documented": True,
            "deployment_approved": True,
            "risk_assessment_documented": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="nist-profile",
        name="NIST AI RMF Compliance",
    )

    result = await framework.check(entry, profile)

    print(f"\nNIST AI RMF Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Rules checked: {result.rules_checked}")

asyncio.run(main())
```

### Third-Party AI Risk Management

```python
# Entry for third-party AI service integration
entry = AuditEntry(
    entry_id="nist-3p-001",
    timestamp=datetime.utcnow(),
    event_type="api_call",
    actor="integration@company.com",
    action="Call external AI API",
    metadata={
        "third_party_assessed": True,
        "vendor_agreement_documented": True,
        "third_party_risks_mapped": True,
        "component_inventory_updated": True,
    },
)
```

## ISO 42001 Compliance

ISO/IEC 42001:2023 establishes requirements for AI Management Systems (AIMS).

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.iso_42001 import ISO42001Framework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = ISO42001Framework()

    # Create entry for AI system deployment
    entry = AuditEntry(
        entry_id="iso-test-001",
        timestamp=datetime.utcnow(),
        event_type="deployment",
        actor="ai-engineer@company.com",
        action="Deploy AI system",
        risk_level=RiskLevel.HIGH,
        metadata={
            # Clause 4: Context
            "organizational_context_documented": True,
            "stakeholders_identified": True,
            "aims_scope_defined": True,
            "within_aims_scope": True,

            # Clause 5: Leadership
            "leadership_approved": True,
            "ai_policy_compliant": True,
            "role_defined": True,
            "authorized_role": True,

            # Clause 6: Planning
            "risk_assessment_documented": True,
            "ai_objectives_aligned": True,
            "impact_assessment_documented": True,

            # Clause 7: Support
            "resources_allocated": True,
            "competence_verified": True,

            # Clause 8: Operation
            "operational_plan_documented": True,
            "lifecycle_process_followed": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="iso-profile",
        name="ISO 42001 Compliance",
    )

    result = await framework.check(entry, profile)

    print(f"\nISO 42001 Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Rules checked: {result.rules_checked}")

asyncio.run(main())
```

### Continual Improvement (Clause 10)

```python
# Entry for handling nonconformity
entry = AuditEntry(
    entry_id="iso-nc-001",
    timestamp=datetime.utcnow(),
    event_type="nonconformity",
    actor="quality@company.com",
    action="Address audit finding",
    metadata={
        "corrective_action_documented": True,
    },
)
```

## MAS FEAT Compliance

The MAS FEAT framework provides AI governance requirements for financial institutions in Singapore.

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.mas import MASFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = MASFramework()

    # Create entry for customer-facing AI decision
    entry = AuditEntry(
        entry_id="mas-test-001",
        timestamp=datetime.utcnow(),
        event_type="credit_decision",
        actor="credit-analyst@bank.sg",
        action="AI credit scoring",
        risk_level=RiskLevel.HIGH,
        data_classification="customer_data",
        user_notified=True,
        human_oversight=True,
        error_handled=True,
        metadata={
            # Fairness
            "fairness_assessed": True,
            "bias_mitigation_documented": True,

            # Ethics
            "ethics_reviewed": True,
            "ethics_aligned": True,

            # Accountability
            "accountable_owner": "credit-risk-team",
            "accountability_documented": True,

            # Transparency
            "explanation_available": True,

            # Model Risk Management
            "development_standards_followed": True,
            "validation_completed": True,
            "monitoring_enabled": True,
            "model_inventory_id": "MODEL-CS-001",

            # Data Governance
            "data_quality_validated": True,
            "privacy_compliant": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="mas-profile",
        name="MAS FEAT Compliance",
    )

    result = await framework.check(entry, profile)

    print(f"\nMAS FEAT Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Rules checked: {result.rules_checked}")

asyncio.run(main())
```

### Model Development Standards

```python
# Entry for model training
entry = AuditEntry(
    entry_id="mas-train-001",
    timestamp=datetime.utcnow(),
    event_type="training",
    actor="data-scientist@bank.sg",
    action="Train credit scoring model",
    documentation_ref="DOC-MODEL-001",
    metadata={
        "development_standards_followed": True,
        "bias_mitigation_documented": True,
        "data_quality_validated": True,
        "lineage_documented": True,
    },
)
```

## Comprehensive Multi-Framework Compliance

For organizations subject to multiple regulations, check against all relevant frameworks:

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.soc2 import SOC2Framework
from rotalabs_comply.frameworks.hipaa import HIPAAFramework
from rotalabs_comply.frameworks.gdpr import GDPRFramework
from rotalabs_comply.frameworks.nist_ai_rmf import NISTAIRMFFramework
from rotalabs_comply.frameworks.iso_42001 import ISO42001Framework
from rotalabs_comply.frameworks.mas import MASFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def comprehensive_compliance_check():
    # Initialize all frameworks
    frameworks = {
        "EU AI Act": EUAIActFramework(),
        "SOC2": SOC2Framework(),
        "HIPAA": HIPAAFramework(),
        "GDPR": GDPRFramework(),
        "NIST AI RMF": NISTAIRMFFramework(),
        "ISO 42001": ISO42001Framework(),
        "MAS FEAT": MASFramework(),
    }

    # Create a comprehensive audit entry with metadata for all frameworks
    entry = AuditEntry(
        entry_id="comprehensive-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="system-user@global-bank.com",
        action="AI-driven customer service",
        system_id="cs-ai-001",
        risk_level=RiskLevel.HIGH,
        data_classification="pii",
        user_notified=True,
        human_oversight=True,
        error_handled=True,
        documentation_ref="DOC-CS-001",
        metadata={
            # EU AI Act
            "risk_assessment_documented": True,
            "accuracy_monitored": True,
            "security_validated": True,

            # SOC2
            "access_controlled": True,
            "monitored": True,

            # HIPAA (if PHI involved)
            "encryption_enabled": True,
            "authenticated": True,
            "purpose_documented": True,
            "minimum_necessary_applied": True,

            # GDPR
            "lawful_basis_documented": True,
            "lawful_basis": "legitimate_interests",

            # NIST AI RMF
            "governance_documented": True,
            "trustworthiness_evaluated": True,
            "risk_tracked": True,

            # ISO 42001
            "ai_policy_compliant": True,
            "lifecycle_process_followed": True,

            # MAS FEAT
            "fairness_assessed": True,
            "explanation_available": True,
            "monitoring_enabled": True,
            "model_inventory_id": "MODEL-001",
            "privacy_compliant": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="comprehensive-profile",
        name="Comprehensive Compliance",
    )

    # Check against all frameworks
    results = {}
    all_violations = []

    for name, framework in frameworks.items():
        result = await framework.check(entry, profile)
        results[name] = result
        all_violations.extend(result.violations)

    # Summary report
    print("=" * 60)
    print("COMPREHENSIVE COMPLIANCE REPORT")
    print("=" * 60)

    for name, result in results.items():
        status = "PASS" if result.is_compliant else "FAIL"
        print(f"\n{name}: {status}")
        print(f"  Rules checked: {result.rules_checked}")
        print(f"  Rules passed: {result.rules_passed}")
        if result.violations:
            print(f"  Violations:")
            for v in result.violations:
                print(f"    - [{v.severity.value.upper()}] {v.rule_id}: {v.rule_name}")

    print("\n" + "=" * 60)
    print(f"TOTAL VIOLATIONS: {len(all_violations)}")
    print("=" * 60)

asyncio.run(comprehensive_compliance_check())
```

## Filtering Compliance Checks

### By Category

```python
# Only check security-related rules
profile = ComplianceProfile(
    profile_id="security-only",
    name="Security Focus",
    enabled_categories=["security", "access_control"],
)
```

### By Severity

```python
# Only report medium severity and above
profile = ComplianceProfile(
    profile_id="high-priority",
    name="High Priority Only",
    min_severity=RiskLevel.MEDIUM,
)
```

### Exclude Specific Rules

```python
# Skip specific rules
profile = ComplianceProfile(
    profile_id="customized",
    name="Custom Profile",
    excluded_rules=["EUAI-007", "SOC2-CC8.1"],
)
```

## Handling Violations

### Analyzing Violations

```python
from collections import defaultdict

# Group violations by framework
by_framework = defaultdict(list)
for v in all_violations:
    by_framework[v.framework].append(v)

# Group by severity
by_severity = defaultdict(list)
for v in all_violations:
    by_severity[v.severity.value].append(v)

# Group by category
by_category = defaultdict(list)
for v in all_violations:
    by_category[v.category].append(v)
```

### Remediation Tracking

```python
# Track remediation progress
remediations = {}

for violation in all_violations:
    remediations[violation.rule_id] = {
        "rule_name": violation.rule_name,
        "severity": violation.severity.value,
        "remediation": violation.remediation,
        "status": "pending",
        "assigned_to": None,
        "due_date": None,
    }

# Assign and track
remediations["EUAI-001"]["assigned_to"] = "compliance-team"
remediations["EUAI-001"]["due_date"] = "2026-02-15"
remediations["EUAI-001"]["status"] = "in_progress"
```

## Custom Rule Checks

Add custom validation logic to rules:

```python
from rotalabs_comply.frameworks.base import ComplianceRule, RiskLevel

def check_custom_requirement(entry):
    """Custom check: require specific metadata field."""
    return entry.metadata.get("custom_approval", False)

custom_rule = ComplianceRule(
    rule_id="CUSTOM-001",
    name="Custom Approval Required",
    description="All AI operations require custom approval flag",
    severity=RiskLevel.MEDIUM,
    category="custom",
    check_fn=check_custom_requirement,  # Custom check function
    remediation="Set custom_approval=True in metadata",
)
```

## Best Practices

### 1. Document Everything

```python
# Ensure documentation references exist for significant events
significant_events = ["deployment", "training", "model_update"]
if entry.event_type in significant_events:
    assert entry.documentation_ref, "Documentation required"
```

### 2. Consistent Metadata Schema

```python
# Define required metadata by framework
required_metadata = {
    "eu_ai_act": ["risk_assessment_documented"],
    "soc2": ["access_controlled", "monitored"],
    "hipaa": ["encryption_enabled", "authenticated"],
}

# Validate before logging
def validate_metadata(entry, frameworks):
    for fw in frameworks:
        for field in required_metadata.get(fw, []):
            if field not in entry.metadata:
                raise ValueError(f"Missing {field} for {fw}")
```

### 3. Regular Compliance Scans

```python
async def daily_compliance_scan(logger, frameworks, profile):
    """Run daily compliance scan on recent entries."""
    from datetime import datetime, timedelta

    end = datetime.utcnow()
    start = end - timedelta(days=1)

    entries = await logger.get_entries(start, end)

    all_violations = []
    for entry in entries:
        for fw in frameworks.values():
            result = await fw.check(entry, profile)
            all_violations.extend(result.violations)

    return {
        "entries_checked": len(entries),
        "total_violations": len(all_violations),
        "critical": sum(1 for v in all_violations if v.severity.value == "critical"),
        "high": sum(1 for v in all_violations if v.severity.value == "high"),
    }
```
