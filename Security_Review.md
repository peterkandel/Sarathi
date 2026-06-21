# Government Security Review Board Assessment

## Scope
This review covers the Nagarik App architecture across the PRD, domain model, service catalog, database design, OCR design, workflow engine, integration architecture, and OpenAPI surfaces.

## Review Objective
Assess the architecture against the following security concerns:
- Authentication
- Authorization
- Encryption
- OCR fraud
- Data leakage
- API abuse
- Insider threats
- Audit requirements

## Executive Summary
The architecture is directionally sound for a government-grade platform because it uses service boundaries, a BFF/API gateway, encrypted persistence, asynchronous OCR, audit separation, and an integration anti-corruption layer. The largest residual risks are not in the individual services but in cross-boundary trust: identity federation, inter-agency integrations, OCR fraud handling, privileged administrative access, and the completeness of audit controls.

## Board Position
- **Approve with conditions** for design progression.
- **Do not move to implementation** until the high-risk controls listed below are defined as policy and testable acceptance criteria.

## Critical Conditions for Approval
1. Centralize identity and privileged access management before broad rollout.
2. Enforce contract-level authorization scopes for every citizen, officer, and agency API.
3. Require encryption at rest and in transit for all persistent and message-bearing stores.
4. Add explicit OCR fraud controls, manual review paths, and provenance logging.
5. Make audit logs append-only, correlation-rich, and independently protected.
6. Define data retention, records classification, and agency sharing rules before integration onboarding.
7. Require idempotency and reconciliation for all external create/submit/payment actions.

---

# 1. Threat Model

## Assets
```json
{
  "critical_assets": [
    "Citizen identity profiles and consent records",
    "Citizenship documents and OCR artifacts",
    "Tax estimates and tax guidance records",
    "Application tracking data and status history",
    "Workflow instances and state transitions",
    "Payment transactions and confirmations",
    "Cross-agency handoff payloads",
    "Audit logs, evidence packages, and retention records",
    "API credentials, service tokens, and signing keys",
    "Reference policy and workflow definitions"
  ]
}
```

## Trust Boundaries
```json
{
  "trust_boundaries": [
    "Citizen mobile app to API gateway",
    "API gateway to domain services",
    "Domain services to integration layer",
    "Integration layer to external government systems",
    "Domain services to OCR pipeline",
    "Workflow engine to notification service",
    "Operational stores to audit records",
    "Administrative portals to privileged back-office functions"
  ]
}
```

## Entry Points
- Mobile app endpoints
- Support/admin portals
- Public and internal REST APIs
- File upload endpoints for documents
- Integration callbacks and webhooks
- Batch import/export interfaces
- Message broker consumers and publishers
- OCR job submission endpoints
- Workflow state transition and task completion endpoints

## Threat Categories
### Authentication Threats
- Credential stuffing against citizen and staff accounts
- Token replay or token theft
- Weak federation with external identity providers
- Service account misuse or over-privileged machine credentials
- Inadequate step-up authentication for sensitive actions

### Authorization Threats
- Broken object-level authorization on documents, applications, and workflows
- Excessive staff permissions in support and operations tools
- Cross-agency data access beyond the declared legal basis
- Privilege escalation through misconfigured scopes or roles
- Unauthorized workflow state transitions or manual overrides

### Encryption Threats
- Sensitive data exposed in transit if TLS or mTLS is misconfigured
- Data at rest exposed through unencrypted backups or object storage
- Secret leakage from logs, configuration, or CI/CD artifacts
- Key compromise causing widespread decryption risk

### OCR Fraud Threats
- Tampered document images or synthetic alterations
- Image substitution after capture
- Replay of previously accepted documents
- Template spoofing to trick field extraction
- Deepfake-like manipulation of supporting evidence where image provenance is weak

### Data Leakage Threats
- Over-shared payloads across agencies
- PII in logs, events, or audit messages beyond minimum necessary
- Frontend overexposure of restricted fields
- Unmasked screenshots or support exports
- OCR artifacts retained longer than necessary

### API Abuse Threats
- Bot attacks on public endpoints
- Large upload abuse against document and OCR endpoints
- Brute force and enumeration via tracking reference lookups
- High-rate payment or submission retries without idempotency
- Event or callback flooding on integration channels

### Insider Threats
- Support staff accessing records without business need
- Administrators bypassing workflow rules or retention policy
- Abuse of manual override and escalation functions
- Rule or reference policy tampering
- Exfiltration through audit or export functions

### Audit Threats
- Missing correlation across services and agencies
- Mutable audit logs or audit log suppression
- Incomplete logging of privileged actions
- Inability to reconstruct OCR or workflow decisions
- Failure to retain evidence needed for complaint handling

---

# 2. Risk Matrix

## Risk Rating Scale
- **Likelihood**: Low / Medium / High
- **Impact**: Low / Medium / High / Critical
- **Overall Risk**: Low / Medium / High / Critical

| ID | Risk | Likelihood | Impact | Overall Risk | Affected Areas |
|---|---|---:|---:|---:|---|
| R1 | Weak identity federation or stolen tokens | Medium | Critical | Critical | Authentication, all citizen-facing APIs |
| R2 | Over-privileged staff or admin roles | Medium | Critical | Critical | Authorization, audit, workflows |
| R3 | OCR tampering or forged documents accepted as valid | Medium | High | High | OCR, document intake, workflows |
| R4 | Cross-agency data leakage through adapters or events | Medium | Critical | Critical | Integration, notifications, audit |
| R5 | API abuse through upload, lookup, or retry storms | High | High | Critical | Gateway, OCR, tracking, payment flows |
| R6 | Lost or inconsistent audit trails across services | Medium | Critical | Critical | Audit, workflow, integration |
| R7 | Backup or object storage exposure of sensitive data | Medium | Critical | Critical | Documents, OCR artifacts, backups |
| R8 | Workflow state manipulation or unauthorized override | Low | High | High | Workflow engine, support tools |
| R9 | Payment gateway callback spoofing or replay | Medium | High | High | Integration, tax guidance, workflow |
| R10 | Insider exfiltration of identity or tax data | Medium | Critical | Critical | All sensitive domains |
| R11 | Reference policy or rule tampering causing incorrect decisions | Low | Critical | High | Reference policy, tax engine, workflow |
| R12 | Silent failure of reconciliation for external systems | Medium | High | High | Integration, workflow, tracking |

## Board Interpretation
- **Critical risks** must be mitigated before implementation approval.
- **High risks** require implementation controls and test cases before production deployment.
- **Medium risks** are acceptable only with documented compensating controls.

---

# 3. Mitigations

## Authentication Mitigations
- Use a centralized government identity provider with OAuth2/OIDC and short-lived JWTs.
- Require step-up authentication for sensitive actions such as consent changes, workflow overrides, payment initiation, and administrative access.
- Bind tokens to client context where practical and enforce refresh token protection.
- Enforce service-to-service mTLS and service identities for all internal calls.
- Rotate credentials and certificates on a defined schedule with revocation capability.

## Authorization Mitigations
- Implement fine-grained RBAC plus scoped ABAC for citizen, officer, supervisor, support, admin, and service identities.
- Enforce object-level authorization on every document, workflow instance, payment record, and audit record.
- Separate read, write, override, and approval privileges.
- Restrict cross-agency access to declared legal basis, purpose, and time window.
- Require dual control or supervisory approval for high-risk manual overrides.

## Encryption Mitigations
- Enforce TLS 1.2+ or stronger across all public and internal interfaces.
- Use mTLS for domain-to-domain and integration traffic.
- Encrypt PostgreSQL, backups, object storage, and message payloads at rest.
- Store secrets in a dedicated secrets manager, not in code or environment files.
- Apply field-level encryption or tokenization to especially sensitive data where feasible.
- Use key rotation, access separation, and recovery procedures for encryption keys.

## OCR Fraud Mitigations
- Validate image integrity, file type, checksum, and provenance before OCR processing.
- Apply image quality scoring, tamper detection, and template consistency checks.
- Compare extracted fields against reference policy and citizen history.
- Flag low-confidence, template-mismatch, duplicate, or suspicious documents for human review.
- Preserve original images, preprocessing artifacts, and extraction traces for investigation.
- Block auto-acceptance when fraud score or confidence thresholds are not met.

## Data Leakage Mitigations
- Minimize payloads in APIs, events, logs, and notifications.
- Mask or redact sensitive fields in logs, traces, support tools, and dashboards.
- Use purpose-limited data sharing and explicit consent or legal basis.
- Ensure notifications avoid exposing sensitive details in channels visible to third parties.
- Apply retention controls and secure deletion for temporary artifacts.
- Limit support exports and require audit logging for any bulk access.

## API Abuse Mitigations
- Apply rate limiting, burst protection, and bot mitigation at the gateway.
- Use idempotency keys for submit, create, and payment actions.
- Limit document upload size, file types, and frequency.
- Protect public lookup endpoints from enumeration with authorization and throttling.
- Use schema validation and request signing for integration endpoints.
- Put high-cost workloads behind queues and asynchronous processing.

## Insider Threat Mitigations
- Segregate duties between rule authors, approvers, operators, and auditors.
- Require reason codes and approval logging for overrides and escalations.
- Monitor privileged access with alerting on unusual search, export, or edit behavior.
- Restrict direct database access and use break-glass accounts only under procedure.
- Use immutable audit logs and periodic access review.
- Protect reference policy and workflow definitions with change approval workflows.

## Audit Mitigations
- Make audit records append-only and immutable once published.
- Record correlation IDs, causation IDs, actor identity, agency, and payload hashes.
- Capture both successful and failed attempts for sensitive operations.
- Separate audit storage from operational storage and protect it with stricter access.
- Perform periodic reconciliation between service logs, audit trails, and integration records.
- Retain evidence packages for disputes, complaints, and oversight according to policy.

---

# 4. Compliance Checklist

## Identity and Access Management
- [ ] Centralized identity provider approved by government security policy
- [ ] OAuth2/OIDC implemented for citizen and staff access
- [ ] mTLS implemented for service-to-service communication
- [ ] Step-up authentication required for sensitive actions
- [ ] Service accounts are unique, scoped, and rotated

## Authorization and Segregation of Duties
- [ ] RBAC defined for citizen, officer, supervisor, support, admin, and system roles
- [ ] Object-level authorization enforced on documents, workflows, taxes, and audit records
- [ ] Cross-agency access limited to purpose and legal basis
- [ ] Manual override requires reason code and approval trail
- [ ] Admin and audit roles separated from operational roles

## Encryption and Key Management
- [ ] TLS enforced for all external and internal traffic
- [ ] PostgreSQL encrypted at rest
- [ ] Object storage encrypted at rest
- [ ] Backups encrypted and access controlled
- [ ] Secrets stored in dedicated secrets manager
- [ ] Key rotation and revocation procedures defined

## OCR and Document Security
- [ ] Uploaded files validated for type, size, integrity, and provenance
- [ ] OCR confidence thresholds defined
- [ ] Fraud detection or tamper detection enabled
- [ ] Low-confidence or suspicious documents routed to human review
- [ ] Original images and artifacts retained only per policy

## Data Protection and Privacy
- [ ] Data minimization applied in APIs, events, logs, and notifications
- [ ] Sensitive fields masked or tokenized where appropriate
- [ ] Consent or lawful basis recorded for data sharing
- [ ] Retention and deletion policies defined by data category
- [ ] Support tools and exports controlled and audited

## API and Integration Security
- [ ] Rate limiting and WAF policies active
- [ ] Idempotency keys required for create/submit/payment operations
- [ ] External callbacks authenticated and signed where possible
- [ ] Retry and reconciliation policies defined for external systems
- [ ] Dead-letter queue handling and replay controls defined
- [ ] Schema validation enforced on inbound and outbound payloads

## Audit and Monitoring
- [ ] Append-only audit trail implemented for all sensitive actions
- [ ] Correlation and causation IDs propagated across services
- [ ] Privileged actions logged and monitored
- [ ] Audit retention and evidence packages defined
- [ ] SIEM integration or equivalent security monitoring active

## Operational Resilience
- [ ] Multi-AZ deployment for production
- [ ] Disaster recovery strategy defined with RPO and RTO
- [ ] Backups tested and restore procedures validated
- [ ] External system outages handled with graceful degradation
- [ ] Reconciliation process in place for uncertain external transactions

## Governance
- [ ] Policy owners assigned for reference data and workflow definitions
- [ ] Change approval workflow defined for rules and reference data
- [ ] Periodic access reviews scheduled
- [ ] Incident response procedures defined
- [ ] Security exceptions formally approved and time-bounded

---

# 5. Board Findings

## High-Priority Findings
1. The architecture is only as secure as its identity federation and privileged access controls. These are currently design intents, but the implementation must be explicitly governed.
2. OCR and document intake are high-risk entry points for tampering and abuse. They require stronger integrity, fraud, and rate-limit controls than ordinary APIs.
3. Cross-agency integration introduces the highest data leakage risk. The anti-corruption layer is necessary, but not sufficient without legal basis checks, scope enforcement, and auditability.
4. Audit separation is a strong design decision, but the audit store must be append-only and independently protected from operational access.
5. Workflow override and reference policy changes are potential insider-threat vectors. These require segregation of duties and strong change control.

## Board Recommendations
- Establish a formal security baseline for every service before implementation.
- Require threat modeling at the adapter, workflow, and OCR layers before go-live.
- Mandate security test cases for broken authorization, replay, tampering, and audit completeness.
- Define the records classification and retention policy before onboarding external agencies.
- Add operational runbooks for fraud handling, replay, reconciliation, and break-glass access.

## Final Verdict
The architecture is suitable for a controlled delivery program provided the critical security conditions are completed and verified. Without those controls, the platform would be exposed to high-impact risks in identity, inter-agency data sharing, OCR fraud, and privileged access.
