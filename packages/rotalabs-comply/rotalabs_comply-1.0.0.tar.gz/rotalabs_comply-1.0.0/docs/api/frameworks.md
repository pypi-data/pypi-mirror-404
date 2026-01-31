# Frameworks Module

Compliance framework implementations for EU AI Act, SOC2, HIPAA, GDPR, NIST AI RMF, ISO 42001, and MAS FEAT.

---

## Base Types

### ComplianceRule

::: rotalabs_comply.frameworks.base.ComplianceRule
    options:
      show_bases: false

Definition of a single compliance rule within a framework.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_id` | `str` | Unique identifier within framework |
| `name` | `str` | Human-readable name |
| `description` | `str` | Detailed requirement description |
| `severity` | `RiskLevel` | Default severity for violations |
| `category` | `str` | Category grouping |
| `check_fn` | `Optional[Callable]` | Custom check function |
| `remediation` | `str` | Default remediation guidance |
| `references` | `List[str]` | External references |

**Example:**

```python
from rotalabs_comply.frameworks.base import ComplianceRule, RiskLevel

rule = ComplianceRule(
    rule_id="CUSTOM-001",
    name="Custom Requirement",
    description="Description of what's required",
    severity=RiskLevel.MEDIUM,
    category="custom",
    remediation="How to fix violations",
    references=["Internal Policy 1.2.3"],
)
```

---

### ComplianceFramework Protocol

::: rotalabs_comply.frameworks.base.ComplianceFramework
    options:
      show_bases: false

Protocol defining the interface for compliance frameworks.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Framework name |
| `version` | `str` | Framework version |
| `rules` | `List[ComplianceRule]` | All rules |

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `check` | `async (entry, profile) -> ComplianceCheckResult` | Check entry |
| `get_rule` | `(rule_id: str) -> Optional[ComplianceRule]` | Get rule by ID |
| `list_categories` | `() -> List[str]` | List categories |

---

### BaseFramework

::: rotalabs_comply.frameworks.base.BaseFramework
    options:
      show_bases: false

Abstract base class for compliance frameworks.

### Constructor

```python
BaseFramework(name: str, version: str, rules: List[ComplianceRule])
```

### Abstract Method

Subclasses must implement:

```python
def _check_rule(
    self, entry: AuditEntry, rule: ComplianceRule
) -> Optional[ComplianceViolation]
```

**Example Custom Framework:**

```python
from rotalabs_comply.frameworks.base import BaseFramework, ComplianceRule, RiskLevel

class MyFramework(BaseFramework):
    def __init__(self):
        rules = [
            ComplianceRule(
                rule_id="MY-001",
                name="My Rule",
                description="Description",
                severity=RiskLevel.MEDIUM,
                category="custom",
            ),
        ]
        super().__init__("My Framework", "1.0", rules)

    def _check_rule(self, entry, rule):
        if rule.rule_id == "MY-001":
            if not entry.metadata.get("my_field"):
                return self._create_violation(entry, rule, "my_field missing")
        return None
```

---

### AuditEntry (Frameworks)

::: rotalabs_comply.frameworks.base.AuditEntry
    options:
      show_bases: false

Audit entry structure used by frameworks for compliance checking.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `entry_id` | `str` | Required | Unique identifier |
| `timestamp` | `datetime` | Required | Event time |
| `event_type` | `str` | Required | Type of event |
| `actor` | `str` | Required | Who triggered event |
| `action` | `str` | Required | Action description |
| `resource` | `str` | `""` | Resource accessed |
| `metadata` | `Dict[str, Any]` | `{}` | Additional context |
| `risk_level` | `RiskLevel` | `LOW` | Risk classification |
| `system_id` | `str` | `""` | AI system identifier |
| `data_classification` | `str` | `"unclassified"` | Data sensitivity |
| `user_notified` | `bool` | `False` | User knows about AI |
| `human_oversight` | `bool` | `False` | Human oversight present |
| `error_handled` | `bool` | `True` | Errors handled gracefully |
| `documentation_ref` | `Optional[str]` | `None` | Documentation reference |

---

### ComplianceProfile (Frameworks)

::: rotalabs_comply.frameworks.base.ComplianceProfile
    options:
      show_bases: false

Configuration profile for compliance evaluation.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile_id` | `str` | Required | Unique identifier |
| `name` | `str` | Required | Profile name |
| `description` | `str` | `""` | Profile description |
| `enabled_frameworks` | `List[str]` | `[]` | Frameworks to evaluate |
| `enabled_categories` | `List[str]` | `[]` | Categories to check |
| `min_severity` | `RiskLevel` | `LOW` | Minimum severity to report |
| `system_classification` | `str` | `"standard"` | System classification |
| `custom_rules` | `List[str]` | `[]` | Additional rule IDs |
| `excluded_rules` | `List[str]` | `[]` | Rules to skip |
| `metadata` | `Dict[str, Any]` | `{}` | Additional config |

---

### ComplianceViolation (Frameworks)

::: rotalabs_comply.frameworks.base.ComplianceViolation
    options:
      show_bases: false

A compliance violation detected during evaluation.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_id` | `str` | Violated rule ID |
| `rule_name` | `str` | Rule name |
| `severity` | `RiskLevel` | Violation severity |
| `description` | `str` | Rule description |
| `evidence` | `str` | Specific evidence |
| `remediation` | `str` | How to fix |
| `entry_id` | `str` | Entry that triggered |
| `category` | `str` | Rule category |
| `framework` | `str` | Framework name |

---

### ComplianceCheckResult (Frameworks)

::: rotalabs_comply.frameworks.base.ComplianceCheckResult
    options:
      show_bases: false

Result of a compliance check against an audit entry.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `entry_id` | `str` | Checked entry ID |
| `framework` | `str` | Framework name |
| `framework_version` | `str` | Framework version |
| `timestamp` | `datetime` | Check time |
| `violations` | `List[ComplianceViolation]` | Violations found |
| `rules_checked` | `int` | Total rules evaluated |
| `rules_passed` | `int` | Rules that passed |
| `is_compliant` | `bool` | No violations found |
| `metadata` | `Dict[str, Any]` | Additional data |

---

## EU AI Act Framework

::: rotalabs_comply.frameworks.eu_ai_act.EUAIActFramework
    options:
      show_bases: false

EU AI Act (2024) compliance framework.

### Categories

| Category | Description |
|----------|-------------|
| `transparency` | User notification requirements |
| `oversight` | Human oversight requirements |
| `risk_management` | Risk assessment and handling |
| `documentation` | Technical documentation |
| `security` | Cybersecurity measures |

### Rules

| Rule ID | Name | Severity | Category |
|---------|------|----------|----------|
| `EUAI-001` | Human Oversight Documentation | HIGH | oversight |
| `EUAI-002` | AI Interaction Notification | HIGH | transparency |
| `EUAI-003` | Risk Assessment | CRITICAL | risk_management |
| `EUAI-004` | Technical Documentation | HIGH | documentation |
| `EUAI-005` | Data Governance | HIGH | documentation |
| `EUAI-006` | Error Handling | MEDIUM | risk_management |
| `EUAI-007` | Accuracy Monitoring | MEDIUM | risk_management |
| `EUAI-008` | Cybersecurity Measures | HIGH | security |

### Usage

```python
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel
from datetime import datetime

framework = EUAIActFramework()

entry = AuditEntry(
    entry_id="test-001",
    timestamp=datetime.utcnow(),
    event_type="inference",
    actor="user@example.com",
    action="AI response",
    risk_level=RiskLevel.HIGH,
    user_notified=True,
    human_oversight=True,
    metadata={"risk_assessment_documented": True},
)

profile = ComplianceProfile(
    profile_id="eu-ai",
    name="EU AI Compliance",
)

result = await framework.check(entry, profile)
```

### Key Requirements

**High-risk operations require:**
- `human_oversight=True`
- `metadata["risk_assessment_documented"]=True`

**User-facing interactions require:**
- `user_notified=True`

**Inference events require:**
- `metadata["accuracy_monitored"]=True`

---

## SOC2 Framework

::: rotalabs_comply.frameworks.soc2.SOC2Framework
    options:
      show_bases: false

SOC2 Type II compliance framework.

### Categories

| Category | TSC | Description |
|----------|-----|-------------|
| `security` | CC | Common Criteria - Security controls |
| `availability` | A | System availability |
| `processing_integrity` | PI | Data processing accuracy |
| `confidentiality` | C | Confidential information protection |
| `privacy` | P | Personal information protection |

### Rules

| Rule ID | Name | Severity | Category |
|---------|------|----------|----------|
| `SOC2-CC6.1` | Logical Access Controls | HIGH | security |
| `SOC2-CC6.2` | System Boundary Definition | MEDIUM | security |
| `SOC2-CC6.3` | Change Management | MEDIUM | security |
| `SOC2-CC7.1` | System Monitoring | HIGH | security |
| `SOC2-CC7.2` | Incident Response | HIGH | security |
| `SOC2-CC8.1` | Availability Monitoring | MEDIUM | availability |
| `SOC2-A1.1` | Recovery Objectives | MEDIUM | availability |
| `SOC2-PI1.1` | Processing Integrity | MEDIUM | processing_integrity |
| `SOC2-C1.1` | Confidentiality Classification | HIGH | confidentiality |
| `SOC2-P1.1` | Privacy Notice | HIGH | privacy |

### Usage

```python
from rotalabs_comply.frameworks.soc2 import SOC2Framework

framework = SOC2Framework()

entry = AuditEntry(
    entry_id="soc2-001",
    timestamp=datetime.utcnow(),
    event_type="data_access",
    actor="admin@company.com",
    action="Query database",
    data_classification="confidential",
    metadata={
        "access_controlled": True,
        "monitored": True,
    },
)

result = await framework.check(entry, profile)
```

### Key Requirements

**Access events require:**
- Authenticated actor (not "anonymous")
- `metadata["access_controlled"]=True`

**Change events require:**
- `metadata["change_approved"]=True`
- `documentation_ref` set

**Data events require:**
- `data_classification` not "unclassified"

---

## HIPAA Framework

::: rotalabs_comply.frameworks.hipaa.HIPAAFramework
    options:
      show_bases: false

HIPAA compliance framework for PHI handling.

### Categories

| Category | Rule Section | Description |
|----------|--------------|-------------|
| `access_control` | 164.312(a) | System and data access |
| `audit` | 164.312(b) | Audit controls |
| `integrity` | 164.312(c) | Data integrity |
| `authentication` | 164.312(d) | Entity authentication |
| `transmission` | 164.312(e) | Transmission security |
| `privacy` | 164.502/514/530 | Privacy rule |

### Rules

| Rule ID | Name | Severity | Category |
|---------|------|----------|----------|
| `HIPAA-164.312(a)` | Access Control | CRITICAL | access_control |
| `HIPAA-164.312(b)` | Audit Controls | HIGH | audit |
| `HIPAA-164.312(c)` | Integrity Controls | HIGH | integrity |
| `HIPAA-164.312(d)` | Authentication | CRITICAL | authentication |
| `HIPAA-164.312(e)` | Transmission Security | HIGH | transmission |
| `HIPAA-164.502` | Uses and Disclosures | CRITICAL | privacy |
| `HIPAA-164.514` | De-identification | HIGH | privacy |
| `HIPAA-164.530` | Administrative Requirements | MEDIUM | privacy |

### PHI Detection

Rules only apply when `data_classification` contains:

- `"PHI"`
- `"ePHI"`
- `"protected_health_information"`
- `"health_data"`
- `"medical"`
- `"clinical"`

### Usage

```python
from rotalabs_comply.frameworks.hipaa import HIPAAFramework

framework = HIPAAFramework()

# PHI-related entry (rules apply)
entry = AuditEntry(
    entry_id="hipaa-001",
    timestamp=datetime.utcnow(),
    event_type="inference",
    actor="doctor@hospital.com",
    action="AI diagnostic",
    data_classification="PHI",
    metadata={
        "access_controlled": True,
        "encryption_enabled": True,
        "authenticated": True,
        "purpose_documented": True,
        "minimum_necessary_applied": True,
    },
)

result = await framework.check(entry, profile)
```

### Key Requirements

**All PHI access requires:**
- Authenticated actor
- `metadata["access_controlled"]=True`
- `metadata["encryption_enabled"]=True`

**High-risk PHI operations require:**
- `metadata["mfa_verified"]=True`

**PHI use requires:**
- `metadata["purpose_documented"]=True`
- `metadata["minimum_necessary_applied"]=True`

---

## GDPR Framework

::: rotalabs_comply.frameworks.gdpr.GDPRFramework
    options:
      show_bases: false

GDPR (EU General Data Protection Regulation 2016/679) compliance framework for processing personal data.

### Categories

| Category | Description |
|----------|-------------|
| `data_protection` | Core data protection principles (Article 5) |
| `legal_basis` | Lawful processing requirements (Article 6) |
| `consent` | Valid consent conditions (Article 7) |
| `transparency` | Information provision and communication (Articles 12-13) |
| `data_subject_rights` | Individual rights (Articles 15, 17, 20, 22) |
| `security` | Data security measures (Articles 32-33) |
| `accountability` | Demonstrating compliance (Articles 25, 30, 35) |

### Rules

| Rule ID | Name | Category | Severity |
|---------|------|----------|----------|
| `GDPR-Art5` | Data Processing Principles | data_protection | CRITICAL |
| `GDPR-Art6` | Lawful Basis for Processing | legal_basis | CRITICAL |
| `GDPR-Art7` | Conditions for Consent | consent | HIGH |
| `GDPR-Art12` | Transparent Information and Communication | transparency | HIGH |
| `GDPR-Art13` | Information at Collection | transparency | HIGH |
| `GDPR-Art15` | Right of Access | data_subject_rights | HIGH |
| `GDPR-Art17` | Right to Erasure (Right to be Forgotten) | data_subject_rights | HIGH |
| `GDPR-Art20` | Right to Data Portability | data_subject_rights | MEDIUM |
| `GDPR-Art22` | Automated Decision-Making and Profiling | data_subject_rights | CRITICAL |
| `GDPR-Art25` | Data Protection by Design and Default | accountability | HIGH |
| `GDPR-Art30` | Records of Processing Activities | accountability | HIGH |
| `GDPR-Art32` | Security of Processing | security | CRITICAL |
| `GDPR-Art33` | Personal Data Breach Notification | security | CRITICAL |
| `GDPR-Art35` | Data Protection Impact Assessment | accountability | HIGH |

### Usage

```python
from rotalabs_comply.frameworks.gdpr import GDPRFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel
from datetime import datetime

framework = GDPRFramework()

entry = AuditEntry(
    entry_id="gdpr-001",
    timestamp=datetime.utcnow(),
    event_type="data_processing",
    actor="analyst@company.eu",
    action="Process customer data",
    data_classification="pii",
    metadata={
        "lawful_basis_documented": True,
        "lawful_basis": "consent",
        "purpose_documented": True,
        "consent_recorded": True,
        "consent_specific": True,
        "consent_informed": True,
        "encryption_applied": True,
        "access_controlled": True,
    },
)

profile = ComplianceProfile(
    profile_id="gdpr-profile",
    name="GDPR Compliance",
)

result = await framework.check(entry, profile)
```

### Key Requirements

**Personal data processing requires:**
- `data_classification` set to "pii", "personal", "sensitive", or "special_category"
- `metadata["lawful_basis_documented"]=True`
- `metadata["purpose_documented"]=True`
- `metadata["lawful_basis"]` set to one of: "consent", "contract", "legal_obligation", "vital_interests", "public_interest", "legitimate_interests"

**Consent-based processing requires:**
- `metadata["consent_recorded"]=True`
- `metadata["consent_specific"]=True`
- `metadata["consent_informed"]=True`

**Automated decisions with significant effects require:**
- `metadata["human_intervention_available"]=True`
- `metadata["right_to_contest_enabled"]=True`
- `metadata["logic_explained"]=True`

---

## NIST AI RMF Framework

::: rotalabs_comply.frameworks.nist_ai_rmf.NISTAIRMFFramework
    options:
      show_bases: false

NIST AI Risk Management Framework (AI RMF 1.0, January 2023) compliance framework.

### Categories

| Category | Function | Description |
|----------|----------|-------------|
| `governance` | GOVERN | Organizational AI governance structures and accountability |
| `context` | MAP | AI system context, intended use, and stakeholder analysis |
| `risk_identification` | MAP | Identification of risks from AI systems and components |
| `measurement` | MEASURE | Metrics, evaluation, and tracking of AI characteristics |
| `risk_treatment` | MANAGE | Risk prioritization, response, and post-deployment monitoring |

### Rules

| Rule ID | Name | Category | Severity |
|---------|------|----------|----------|
| `NIST-GOV-1` | AI Risk Management Governance Structure | governance | HIGH |
| `NIST-GOV-2` | Organizational AI Principles and Values | governance | MEDIUM |
| `NIST-GOV-3` | Roles and Responsibilities Defined | governance | HIGH |
| `NIST-GOV-4` | Third-Party AI Risk Management | governance | HIGH |
| `NIST-MAP-1` | AI System Context Established | context | MEDIUM |
| `NIST-MAP-2` | AI Categorization and Intended Use Documented | context | HIGH |
| `NIST-MAP-3` | AI Benefits and Costs Assessed | context | MEDIUM |
| `NIST-MAP-4` | Risks from Third-Party Components Mapped | risk_identification | HIGH |
| `NIST-MEAS-1` | Appropriate Metrics Identified | measurement | MEDIUM |
| `NIST-MEAS-2` | AI Systems Evaluated for Trustworthy Characteristics | measurement | HIGH |
| `NIST-MEAS-3` | Mechanisms for Tracking Identified Risks | measurement | MEDIUM |
| `NIST-MAN-1` | AI Risks Prioritized and Responded To | risk_treatment | HIGH |
| `NIST-MAN-2` | AI System Deployment Decisions Documented | risk_treatment | HIGH |
| `NIST-MAN-3` | Post-Deployment Monitoring in Place | risk_treatment | HIGH |
| `NIST-MAN-4` | Incident Response and Recovery Procedures | risk_treatment | CRITICAL |

### Usage

```python
from rotalabs_comply.frameworks.nist_ai_rmf import NISTAIRMFFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel
from datetime import datetime

framework = NISTAIRMFFramework()

entry = AuditEntry(
    entry_id="nist-001",
    timestamp=datetime.utcnow(),
    event_type="deployment",
    actor="mlops@company.com",
    action="Deploy production model",
    risk_level=RiskLevel.HIGH,
    documentation_ref="DOC-DEPLOY-001",
    metadata={
        "governance_documented": True,
        "governance_approval": True,
        "system_context_documented": True,
        "ai_categorization_documented": True,
        "intended_use_documented": True,
        "benefit_cost_assessed": True,
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
```

### Key Requirements

**High-risk operations require:**
- `metadata["governance_documented"]=True` or `metadata["governance_approval"]=True`
- `metadata["risk_assessment_documented"]=True` or `metadata["risk_prioritized"]=True`
- `metadata["risk_tracked"]=True` or `metadata["risk_registry_updated"]=True`

**Deployment operations require:**
- `metadata["deployment_decision_documented"]=True` or `metadata["deployment_approved"]=True`
- `documentation_ref` set

**Third-party AI operations require:**
- `metadata["third_party_assessed"]=True` or `metadata["vendor_agreement_documented"]=True`
- `metadata["third_party_risks_mapped"]=True` or `metadata["component_inventory_updated"]=True`

**Incident events require:**
- `metadata["incident_response_followed"]=True` or `metadata["recovery_plan_executed"]=True`

---

## ISO/IEC 42001 Framework

::: rotalabs_comply.frameworks.iso_42001.ISO42001Framework
    options:
      show_bases: false

ISO/IEC 42001:2023 AI Management System (AIMS) compliance framework.

### Categories

| Category | Clause | Description |
|----------|--------|-------------|
| `context` | 4 | Organizational context and AIMS scope |
| `leadership` | 5 | Leadership commitment, AI policy, and roles |
| `planning` | 6 | Risk assessment, objectives, and impact assessment |
| `support` | 7 | Resources, competence, awareness, communication, documentation |
| `operation` | 8 | Operational planning, lifecycle, third-party, impact |
| `performance` | 9 | Monitoring, internal audit, management review |
| `improvement` | 10 | Corrective action and continual improvement |

### Rules

| Rule ID | Name | Category | Severity |
|---------|------|----------|----------|
| `ISO42001-4.1` | Understanding Organization and Context | context | HIGH |
| `ISO42001-4.2` | Understanding Needs of Interested Parties | context | HIGH |
| `ISO42001-4.3` | Scope of AIMS Determined | context | HIGH |
| `ISO42001-5.1` | Leadership Commitment Demonstrated | leadership | HIGH |
| `ISO42001-5.2` | AI Policy Established | leadership | CRITICAL |
| `ISO42001-5.3` | Roles and Responsibilities Assigned | leadership | HIGH |
| `ISO42001-6.1` | AI Risk Assessment Conducted | planning | CRITICAL |
| `ISO42001-6.2` | AI Objectives Established | planning | HIGH |
| `ISO42001-6.3` | AI Impact Assessment Performed | planning | CRITICAL |
| `ISO42001-7.1` | Resources Provided | support | HIGH |
| `ISO42001-7.2` | Competence Ensured | support | HIGH |
| `ISO42001-7.3` | Awareness Maintained | support | MEDIUM |
| `ISO42001-7.4` | Communication Processes Established | support | MEDIUM |
| `ISO42001-7.5` | Documented Information Controlled | support | HIGH |
| `ISO42001-8.1` | Operational Planning and Control | operation | HIGH |
| `ISO42001-8.2` | AI System Lifecycle Processes | operation | CRITICAL |
| `ISO42001-8.3` | Third-Party Considerations | operation | HIGH |
| `ISO42001-8.4` | AI System Impact Assessment | operation | CRITICAL |
| `ISO42001-9.1` | Monitoring and Measurement | performance | HIGH |
| `ISO42001-9.2` | Internal Audit Conducted | performance | HIGH |
| `ISO42001-9.3` | Management Review | performance | HIGH |
| `ISO42001-10.1` | Nonconformity and Corrective Action | improvement | HIGH |
| `ISO42001-10.2` | Continual Improvement | improvement | MEDIUM |

### Usage

```python
from rotalabs_comply.frameworks.iso_42001 import ISO42001Framework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel
from datetime import datetime

framework = ISO42001Framework()

entry = AuditEntry(
    entry_id="iso-001",
    timestamp=datetime.utcnow(),
    event_type="deployment",
    actor="ai-engineer@company.com",
    action="Deploy AI system",
    risk_level=RiskLevel.HIGH,
    metadata={
        "organizational_context_documented": True,
        "stakeholders_identified": True,
        "aims_scope_defined": True,
        "within_aims_scope": True,
        "leadership_approved": True,
        "ai_policy_compliant": True,
        "role_defined": True,
        "authorized_role": True,
        "risk_assessment_documented": True,
        "impact_assessment_documented": True,
        "lifecycle_process_followed": True,
        "operational_plan_documented": True,
        "monitoring_enabled": True,
    },
)

profile = ComplianceProfile(
    profile_id="iso42001-profile",
    name="ISO 42001 Compliance",
)

result = await framework.check(entry, profile)
```

### Key Requirements

**All AI operations require:**
- `metadata["ai_policy_compliant"]=True`

**System deployments require:**
- `metadata["organizational_context_documented"]=True`
- `metadata["aims_scope_defined"]=True` and `metadata["within_aims_scope"]=True`
- `metadata["leadership_approved"]=True`
- `metadata["lifecycle_process_followed"]=True`
- `metadata["operational_plan_documented"]=True`

**High-risk operations require:**
- `metadata["risk_assessment_documented"]=True`

**Critical operations require:**
- `metadata["role_defined"]=True` and `metadata["authorized_role"]=True`
- `metadata["competence_verified"]=True`

---

## MAS FEAT Framework

::: rotalabs_comply.frameworks.mas.MASFramework
    options:
      show_bases: false

MAS (Monetary Authority of Singapore) FEAT principles and AI governance framework for financial institutions.

### Categories

| Category | Focus | Description |
|----------|-------|-------------|
| `fairness` | FEAT-F | Ensuring AI decisions are fair and unbiased |
| `ethics` | FEAT-E | Ethical use of data and AI alignment with firm standards |
| `accountability` | FEAT-A | Clear accountability and human oversight |
| `transparency` | FEAT-T | Explainability and customer notification |
| `model_risk` | MRM | Model development, validation, and monitoring |
| `data_governance` | Data | Data quality, lineage, and privacy compliance |
| `operations` | Ops | System resilience and incident management |

### Rules

| Rule ID | Name | Category | Severity |
|---------|------|----------|----------|
| `MAS-FEAT-F1` | Fair AI-Driven Decisions | fairness | HIGH |
| `MAS-FEAT-F2` | Bias Detection and Mitigation | fairness | HIGH |
| `MAS-FEAT-E1` | Ethical Use of Data and AI | ethics | HIGH |
| `MAS-FEAT-E2` | AI Alignment with Firm's Ethical Standards | ethics | MEDIUM |
| `MAS-FEAT-A1` | Clear Accountability for AI Decisions | accountability | HIGH |
| `MAS-FEAT-A2` | Human Oversight for Material AI Decisions | accountability | CRITICAL |
| `MAS-FEAT-T1` | Explainable AI Decisions | transparency | HIGH |
| `MAS-FEAT-T2` | Customer Notification of AI Use | transparency | HIGH |
| `MAS-MRM-1` | Model Development Standards | model_risk | HIGH |
| `MAS-MRM-2` | Model Validation Requirements | model_risk | HIGH |
| `MAS-MRM-3` | Model Monitoring and Review | model_risk | HIGH |
| `MAS-MRM-4` | Model Inventory Maintained | model_risk | MEDIUM |
| `MAS-DATA-1` | Data Quality Standards | data_governance | HIGH |
| `MAS-DATA-2` | Data Lineage Documentation | data_governance | MEDIUM |
| `MAS-DATA-3` | Data Privacy Compliance | data_governance | CRITICAL |
| `MAS-OPS-1` | AI System Resilience | operations | HIGH |
| `MAS-OPS-2` | Incident Management for AI Failures | operations | HIGH |
| `MAS-OPS-3` | Business Continuity for AI Systems | operations | MEDIUM |

### Usage

```python
from rotalabs_comply.frameworks.mas import MASFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel
from datetime import datetime

framework = MASFramework()

entry = AuditEntry(
    entry_id="mas-001",
    timestamp=datetime.utcnow(),
    event_type="credit_decision",
    actor="credit-officer@bank.sg",
    action="AI credit scoring",
    risk_level=RiskLevel.HIGH,
    data_classification="customer_data",
    user_notified=True,
    human_oversight=True,
    error_handled=True,
    metadata={
        "fairness_assessed": True,
        "bias_mitigation_documented": True,
        "accountable_owner": "credit-risk-team",
        "explanation_available": True,
        "monitoring_enabled": True,
        "model_inventory_id": "MODEL-CS-001",
        "privacy_compliant": True,
    },
)

profile = ComplianceProfile(
    profile_id="mas-profile",
    name="MAS FEAT Compliance",
)

result = await framework.check(entry, profile)
```

### Key Requirements

**Customer-facing AI decisions require:**
- `metadata["fairness_assessed"]=True`
- `metadata["explanation_available"]=True` or `metadata["explainability_method"]` set
- `user_notified=True`

**High-risk operations require:**
- `human_oversight=True`

**Model lifecycle events require:**
- `metadata["bias_mitigation_documented"]=True`
- `metadata["validation_completed"]=True` (for deployments)
- `metadata["model_inventory_id"]` or `metadata["model_registered"]=True`

**Personal data operations require:**
- `data_classification` set to "pii", "personal", "customer_data", or "sensitive"
- `metadata["privacy_compliant"]=True` or `metadata["consent_obtained"]=True`

**All operations require:**
- `error_handled=True` (for resilience)
