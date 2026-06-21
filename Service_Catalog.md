# Service Catalog

## Program Context
This catalog decomposes the Nagarik App platform into deployable services based on the production architecture and domain model.

## Catalog Scope
The catalog includes the citizen-facing domain services, supporting governance services, and the asynchronous OCR capability required by the PRD and architecture.

## Service Naming Conventions
- Service names reflect business capability and bounded context.
- APIs are listed at a logical level, not as implementation routes.
- Events are named as domain events and integration events.
- Database ownership is exclusive to the owning service.

## Service Summary
| Service | Type | Primary Responsibility |
|---|---|---|
| API Gateway / BFF | Edge platform service | Client aggregation, routing, security enforcement |
| Identity & Consent Service | Supporting domain service | Citizen identity linkage, consent, preferences |
| Document Intake Service | Core domain service | Capture, review, and submission of citizenship documents |
| OCR / Extraction Pipeline | Supporting processing service | Document OCR and data extraction |
| Tax Guidance Service | Core domain service | Tax estimation and payment guidance |
| Application Tracking Service | Core domain service | Citizen-visible application status and history |
| Service Orchestration Service | Core coordinating service | Cross-agency journeys and governed data reuse |
| Notification Service | Core domain service | Official citizen inbox and notice lifecycle |
| Reference Policy Service | Supporting reference service | Service catalog, status taxonomy, and approved reference data |
| Audit & Records Service | Supporting compliance service | Immutable audit, records, and evidence retention |

---

# 1. API Gateway / BFF

## Name
API Gateway / Backend-for-Frontend

## Purpose
Provide a single secure entry point for the React Native client, aggregate responses from multiple services, enforce request validation, and shape mobile-friendly payloads.

## APIs Exposed
- `POST /auth/exchange`
- `GET /me`
- `GET /dashboard`
- `GET /notifications/summary`
- `GET /applications/summary`
- `POST /support/requests`
- Service-specific pass-through APIs for approved mobile journeys

## Events Produced
- RequestReceived
- AuthTokenExchanged
- ClientSessionCreated
- ClientRequestRouted

## Events Consumed
- None as a primary domain consumer; it calls services synchronously and should not own business events.

## Database Ownership
- None. The gateway should remain stateless and avoid owning transactional business data.
- Optional ephemeral runtime state may be held in Redis for throttling, session correlation, and request deduplication.

## Security Responsibilities
- Enforce TLS termination and secure headers.
- Validate OAuth2/OIDC access tokens.
- Apply rate limiting and bot protection.
- Reject malformed or unauthorized requests before they reach domain services.
- Enforce request size limits for uploads and submissions.

## Scaling Requirements
- Must scale horizontally with user traffic.
- Must support peak read demand from millions of citizens.
- Must remain highly available because all client traffic depends on it.
- Should be stateless to allow fast rollout and failover.

---

# 2. Identity & Consent Service

## Name
Identity & Consent Service

## Purpose
Maintain citizen identity linkage, consent records, communication preferences, and authorization scopes used across the platform.

## APIs Exposed
- `GET /identity/me`
- `POST /identity/link`
- `GET /consents`
- `POST /consents`
- `DELETE /consents/{id}` where legally permitted
- `GET /preferences/notifications`
- `PUT /preferences/notifications`
- `GET /authorization-scopes`

## Events Produced
- CitizenIdentityLinked
- CitizenIdentityVerified
- ConsentGranted
- ConsentRevoked
- CommunicationPreferenceUpdated
- AuthorizationScopeChanged

## Events Consumed
- IdentityAssuranceCompleted
- CitizenProfileUpdated from trusted identity sources
- PolicyReferenceUpdated when consent categories or rules change

## Database Ownership
- Owns citizen identity reference records, consent records, communication preferences, and authorization scopes.
- Does not own source-of-truth national identity registry data.

## Security Responsibilities
- Protect identity-linked personal data with encryption at rest and strict role-based access.
- Validate and persist lawful basis or consent where required.
- Provide strong auditability for consent changes and profile linkage.
- Enforce least privilege for internal and administrative access.

## Scaling Requirements
- Must support high read volume from every other domain service.
- Must be highly available because identity and consent checks are foundational.
- Should use caching for stable reference lookups where safe.
- Must handle burst traffic during onboarding, login, and major service campaigns.

---

# 3. Document Intake Service

## Name
Document Intake Service

## Purpose
Capture citizenship document images, manage review of extracted fields, validate submission quality, and maintain document submission history.

## APIs Exposed
- `POST /documents/capture-sessions`
- `POST /documents/capture-sessions/{id}/images`
- `POST /documents/capture-sessions/{id}/submit-for-extraction`
- `GET /documents/capture-sessions/{id}`
- `GET /documents/submissions/{id}`
- `POST /documents/submissions/{id}/confirm`
- `POST /documents/{id}/reject`
- `GET /documents/history`

## Events Produced
- DocumentCaptureSessionCreated
- DocumentImageStored
- DocumentSubmitted
- DocumentQualityFlagged
- DocumentExtractionRequested
- DocumentSubmissionConfirmed

## Events Consumed
- DocumentExtractionCompleted
- IdentityAssuranceCompleted
- ReferencePolicyUpdated for document type or capture rule changes
- ServiceJourneyCreated when intake is part of a larger orchestration flow

## Database Ownership
- Owns capture sessions, document metadata, extracted-field review state, submission records, and quality assessments.
- Stores large binary files and extraction artifacts in S3-compatible storage, not PostgreSQL.

## Security Responsibilities
- Validate file type, size, and content constraints on upload.
- Restrict access to submitted identity documents and extraction results.
- Ensure citizen review is completed before final submission where required.
- Maintain audit trails for capture, correction, and finalization steps.

## Scaling Requirements
- Must handle bursty upload traffic and asynchronous processing queues.
- Must scale independently from tracking and notification workloads.
- Should queue extraction requests to avoid blocking user interactions.
- Requires resilient storage and retry behavior for large file uploads.

---

# 4. OCR / Extraction Pipeline

## Name
OCR / Extraction Pipeline

## Purpose
Perform document recognition, OCR, field extraction, and confidence scoring for uploaded citizenship documents and related artifacts.

## APIs Exposed
- `POST /extractions`
- `GET /extractions/{id}`
- `POST /extractions/{id}/reprocess`
- `GET /extractions/{id}/confidence`

## Events Produced
- DocumentExtractionStarted
- DocumentExtractionCompleted
- DocumentExtractionFailed
- DocumentConfidenceScored

## Events Consumed
- DocumentImageStored
- DocumentCaptureSessionCreated
- DocumentReprocessRequested

## Database Ownership
- Owns extraction job state, model inference metadata, confidence metrics, and processing outcomes.
- Does not own the citizen document record itself.
- Intermediate artifacts should be kept in isolated storage and purged according to retention policy.

## Security Responsibilities
- Process only authorized document inputs from the document intake service.
- Isolate inference jobs and remove unnecessary access to raw citizen data.
- Protect model outputs and intermediate artifacts from unauthorized disclosure.
- Log processing provenance for audit and troubleshooting.

## Scaling Requirements
- Must scale horizontally to absorb document upload bursts.
- Should use queue-based worker pools for extraction jobs.
- Must support retries and dead-letter handling for failed jobs.
- Needs elastic capacity because OCR workloads are variable and compute-heavy.

---

# 5. Tax Guidance Service

## Name
Tax Guidance Service

## Purpose
Produce indicative tax estimates, explain calculation basis, present due dates, and provide approved payment guidance.

## APIs Exposed
- `POST /tax/estimates`
- `GET /tax/estimates/{id}`
- `GET /tax/estimates/{id}/disclosure`
- `GET /tax/obligations`
- `GET /tax/payment-guidance`
- `POST /tax/estimates/{id}/save`
- `POST /tax/estimates/{id}/acknowledge`

## Events Produced
- TaxEstimateCreated
- TaxEstimateViewed
- TaxGuidanceSaved
- TaxPaymentReminderEligible
- TaxEstimateAcknowledged

## Events Consumed
- IdentityAssuranceCompleted
- PolicyReferenceUpdated for tax category or rule changes
- CommunicationPreferenceUpdated for reminder eligibility
- PaymentOutcomeRecorded if a downstream payment status feed is available

## Database Ownership
- Owns tax estimate records, calculation snapshots, disclosures, and saved guidance history.
- Does not own authoritative tax assessment or treasury payment records.

## Security Responsibilities
- Protect sensitive tax-related information with strict access controls.
- Avoid exposing non-essential financial details to unauthorized users.
- Maintain calculation traceability for audit and dispute handling.
- Enforce legal disclaimers and user acknowledgments where estimates are advisory.

## Scaling Requirements
- Must support seasonal spikes around filing deadlines and public campaigns.
- Read traffic is expected to be high; caching should be applied to safe reference data.
- Must remain available even when external treasury or payment channels are degraded.
- Should degrade gracefully by showing advisory guidance when external dependencies fail.

---

# 6. Application Tracking Service

## Name
Application Tracking Service

## Purpose
Present citizen-readable application status, milestone progression, and next actions for eligible government services.

## APIs Exposed
- `GET /applications/{trackingReference}`
- `GET /applications/{trackingReference}/timeline`
- `GET /applications`
- `GET /applications/{trackingReference}/action-required`
- `POST /applications/lookup`

## Events Produced
- ApplicationTrackingRequested
- ApplicationStatusViewed
- ApplicationStatusMapped
- ApplicationActionRequiredFlagged
- ApplicationTrackingReferenceIssued

## Events Consumed
- ApplicationStatusUpdated
- ServiceJourneyProgressed when an application is part of a wider journey
- ReferencePolicyUpdated for status taxonomy changes
- IdentityAssuranceCompleted for ownership checks

## Database Ownership
- Owns citizen-visible tracking views, status timelines, milestone mapping records, and lookup indexes.
- Does not own the agency internal case management system or adjudication state.

## Security Responsibilities
- Restrict tracking data to the verified citizen or authorized support personnel.
- Mask sensitive case details for restricted application categories.
- Keep mapping logic auditable so status translation can be explained.
- Enforce secure lookup by tracking reference and identity binding.

## Scaling Requirements
- Must support very high read volume.
- Must use caching for status summaries and tracking lookups.
- Must be highly available because tracking is a core citizen trust function.
- Should support read replicas or denormalized read models for performance.

---

# 7. Service Orchestration Service

## Name
Service Orchestration Service

## Purpose
Coordinate cross-agency service journeys, govern reusable data sharing, manage handoffs, and maintain journey progress checkpoints.

## APIs Exposed
- `POST /journeys`
- `GET /journeys/{id}`
- `GET /journeys/{id}/steps`
- `POST /journeys/{id}/steps/{stepId}/complete`
- `POST /journeys/{id}/handoffs`
- `POST /journeys/{id}/sharing-authorizations`
- `GET /journeys/{id}/progress`

## Events Produced
- ServiceJourneyCreated
- ServiceJourneyProgressed
- ServiceHandoffInitiated
- ServiceHandoffCompleted
- ReusedDataPackagePrepared
- SharingAuthorizationGranted
- SharingAuthorizationRevoked

## Events Consumed
- CitizenIdentityVerified
- ConsentGranted
- ConsentRevoked
- PolicyReferenceUpdated
- ApplicationStatusUpdated where a journey step depends on application state
- DocumentSubmissionConfirmed where document submission is part of the journey

## Database Ownership
- Owns service journey state, step progression, handoff records, sharing authorizations, and reused-data metadata.
- Does not own source data from participating agencies.

## Security Responsibilities
- Enforce purpose limitation and data minimization on every cross-agency handoff.
- Store explicit legal basis or consent references for shared data.
- Apply strict access controls to orchestration and journey history.
- Maintain full traceability of who shared what, when, and with which agency.

## Scaling Requirements
- Must support complex but comparatively lower-volume transactions than tracking or notifications.
- Must be resilient to slow or unavailable external agencies.
- Should use asynchronous retries and stateful checkpoints to survive interruptions.
- Must be designed for eventual consistency across agency boundaries.

---

# 8. Notification Service

## Name
Notification Service

## Purpose
Maintain the official citizen notification inbox, classify notices, link notices to services, and preserve delivery and read history.

## APIs Exposed
- `GET /notifications`
- `GET /notifications/{id}`
- `POST /notifications/{id}/read`
- `POST /notifications/{id}/archive`
- `GET /notifications/summary`
- `GET /notifications/unread-count`
- `POST /notifications/preferences`

## Events Produced
- NotificationRequested
- NotificationCreated
- NotificationDelivered
- NotificationRead
- NotificationArchived
- NotificationPreferenceUpdated

## Events Consumed
- ApplicationStatusUpdated
- TaxEstimateCreated
- TaxPaymentReminderEligible
- ServiceJourneyProgressed
- ServiceHandoffCompleted
- CitizenConsentUpdated when notification preferences change

## Database Ownership
- Owns notification records, threads, delivery records, read receipts, and archive state.
- Should not store source business data beyond references and lightweight display context.

## Security Responsibilities
- Prevent spoofing and unauthorized message injection.
- Ensure notices are marked as official and traceable.
- Restrict notification content according to privacy and classification rules.
- Keep delivery evidence for legal and audit purposes.

## Scaling Requirements
- Must support extremely high read volume from the mobile client.
- Must scale for bursty event intake from multiple source services.
- Should use caching for unread counts and summary views.
- Must preserve strong delivery guarantees and idempotent notification creation.

---

# 9. Reference Policy Service

## Name
Reference Policy Service

## Purpose
Manage governed reference data used across the platform, including service definitions, status taxonomies, document types, tax categories, notification categories, and agency participation rules.

## APIs Exposed
- `GET /reference/services`
- `GET /reference/status-taxonomies`
- `GET /reference/document-types`
- `GET /reference/tax-categories`
- `GET /reference/notification-categories`
- `GET /reference/agency-participation-rules`
- `POST /reference/changes` for authorized administrators

## Events Produced
- PolicyReferenceUpdated
- ReferenceValueApproved
- ReferenceValueDeprecated
- AgencyParticipationRuleUpdated

## Events Consumed
- None required for core operation, although policy import or admin workflows may consume governance inputs.

## Database Ownership
- Owns approved reference entities, versioned policy records, and change history.
- Does not own citizen-specific transactional records.

## Security Responsibilities
- Restrict modification to authorized policy administrators.
- Preserve approval history and change provenance.
- Protect against unauthorized changes that could affect multiple downstream services.
- Enforce versioning and publish-only semantics for approved values.

## Scaling Requirements
- Must support frequent reads from all other services.
- Change volume is low, but read availability must be very high.
- Should use aggressive caching and cache invalidation discipline.
- Must be highly reliable because downstream services depend on stable reference data.

---

# 10. Audit & Records Service

## Name
Audit & Records Service

## Purpose
Provide immutable logging, access traceability, submission evidence, retention metadata, and compliance support across the platform.

## APIs Exposed
- `POST /audit/events`
- `GET /audit/events/{id}` for authorized oversight use
- `GET /audit/search`
- `POST /records/evidence-packages`
- `GET /records/evidence-packages/{id}`
- `GET /records/retention-rules`

## Events Produced
- AuditRecordCreated
- EvidencePackageCreated
- RetentionRuleApplied
- ComplianceFlagRaised

## Events Consumed
- All significant business events from domain services, including:
- CitizenIdentityLinked
- ConsentGranted
- DocumentSubmitted
- DocumentExtractionCompleted
- TaxEstimateCreated
- ApplicationStatusUpdated
- ServiceJourneyCreated
- ServiceJourneyProgressed
- NotificationCreated
- NotificationRead
- PolicyReferenceUpdated

## Database Ownership
- Owns append-only audit logs, access logs, evidence packages, and retention metadata.
- Should be logically isolated from operational business databases.

## Security Responsibilities
- Preserve tamper-evident records.
- Restrict search and retrieval to oversight, audit, and approved operations roles.
- Log all administrative access.
- Support retention and deletion actions only where legally allowed.

## Scaling Requirements
- Must ingest a high volume of events from all services.
- Write throughput must be resilient and durable.
- Read access should be tightly controlled and comparatively lower volume.
- Must not become a bottleneck for operational services; ingestion should be asynchronous where possible.

---

# Service Dependency Summary
| Service | Key Upstream Dependencies | Key Downstream Consumers |
|---|---|---|
| API Gateway / BFF | Identity provider, client requests | All domain services |
| Identity & Consent | National identity source, policy rules | Document, Tax, Tracking, Orchestration, Notification |
| Document Intake | Identity & Consent, Reference Policy, OCR Pipeline | Orchestration, Audit, Notification |
| OCR / Extraction Pipeline | Document Intake | Document Intake, Audit |
| Tax Guidance | Identity & Consent, Reference Policy | Notification, Audit, Orchestration |
| Application Tracking | Agency case systems, Reference Policy | Notification, Audit, Orchestration |
| Service Orchestration | Identity & Consent, Reference Policy, external agencies | Tracking, Notification, Audit |
| Notification | All domain services | Citizen mobile app |
| Reference Policy | Policy administrators | All domain services |
| Audit & Records | All domain services | Oversight and compliance users |

# Recommended Service Boundary Decisions
- Keep the API Gateway / BFF stateless and outside the business domain model.
- Keep OCR separate from document intake because it is compute-heavy and variable-latency.
- Keep notifications separate from source services to preserve a single official inbox.
- Keep reference policy centralized to prevent inconsistent tax, status, and service definitions.
- Keep audit and records append-only and isolated from operational data stores.
- Keep cross-agency orchestration separate from application tracking because it coordinates journeys, not just status.

# Summary
This service catalog decomposes the platform into deployable, governable services with explicit ownership boundaries, data ownership, security responsibilities, and scale expectations suitable for a government-grade platform serving 10 million users.
