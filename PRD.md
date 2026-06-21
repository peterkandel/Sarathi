# Product Requirements Document

## Project
Nagarik App Enhancement Program for Nepal

## Document Control
- Version: 1.0
- Status: Draft
- Date: 2026-06-20
- Prepared For: Government procurement, policy review, enterprise architecture, and engineering teams

## Purpose
This document defines the product requirements for extending Nepal’s Nagarik App with the following capabilities:

1. Citizenship document scanning and data extraction
2. Tax estimation and payment assistance
3. Government application tracking
4. Cross-agency service integration
5. Citizen notification center

This PRD focuses on business, policy, user, and service requirements. It intentionally avoids implementation design.

## Product Vision
Nagarik App will evolve into Nepal’s primary digital public-service access layer, enabling citizens to submit documents, understand obligations, track applications, access services across agencies, and receive trusted official notifications through a unified and secure experience.

## Strategic Objectives
- Reduce citizen travel, paperwork, and duplicate submissions.
- Improve service transparency and accountability.
- Increase digital service adoption and completion rates.
- Improve inter-agency coordination and service continuity.
- Establish a trusted channel for official government communication.

## Target Users
- Citizens and residents of Nepal
- Taxpayers and business owners
- Government officers and case workers
- Support desk and call-center staff
- Agency administrators and supervisors

## Out of Scope
- Replacing agency core systems
- Creating new legal authorities for agencies
- Automated decision-making where law requires human review
- Commercial or social messaging features
- A brand redesign of Nagarik App

## Cross-Cutting Product Principles
- Citizen-first and mobile-first
- Secure by default
- Legally compliant and auditable
- Inclusive of low-bandwidth and low-literacy users
- Multilingual where required by policy
- Transparent and explainable

---

# 1. Citizenship Document Scanning and Data Extraction

## Problem Statement
Citizens often must manually enter identity and citizenship information from physical documents when applying for services. This creates errors, delays, repeated data entry, and unnecessary visits to service centers.

## Business Objective
- Reduce application completion time and input errors.
- Improve first-time-right submission rates.
- Lower support burden caused by manual data entry.
- Increase digital adoption for document-based services.

## User Personas
- Citizen applicant submitting a service request
- Elderly or low-literacy citizen needing guided capture
- Government operator verifying submitted documents
- Support staff assisting with rejected scans

## User Journeys
- A citizen opens the app, scans a citizenship document, and reviews extracted fields.
- The citizen corrects any inaccurate fields and submits the document as part of a service application.
- A government operator reviews the document and extracted data during processing.
- A support agent helps a user rescan a document that was unclear or incomplete.

## User Stories
- As a citizen, I want to scan my citizenship document so that I do not have to type every field manually.
- As a citizen, I want to review extracted data before submission so that I can correct mistakes.
- As a government officer, I want extracted document data attached to the application so that I can process it faster.
- As a support agent, I want to know why a scan failed so that I can guide the citizen to resubmit correctly.

## Functional Requirements
- The app shall allow capture of document images from a mobile device.
- The app shall extract key identity fields from supported citizenship documents.
- The app shall present extracted fields for citizen review and correction before submission.
- The app shall indicate when image quality is insufficient for extraction.
- The app shall support document recapture without losing entered data.
- The app shall allow citizens to attach scanned documents to eligible service applications.
- The app shall maintain a visible history of submitted documents and status where permitted.
- The app shall support manual override where extraction confidence is insufficient.

## Non-Functional Requirements
- The feature shall be usable on low and mid-range mobile devices.
- The feature shall perform reliably under low-bandwidth conditions.
- The feature shall be accessible to users with limited digital literacy.
- The feature shall meet government security and privacy standards.
- The feature shall preserve data integrity and traceability.
- The feature shall provide clear feedback in plain language and supported local languages.

## Acceptance Criteria
- A citizen can capture a document image and review extracted fields before submission.
- A citizen can correct at least one extracted field and resubmit without restarting.
- The system flags unreadable or incomplete images before submission.
- Government officers can see the submitted document and extracted fields in the application record.
- The feature works consistently for supported citizenship document formats defined by policy.
- All submitted data is recorded with an auditable trail.

## Dependencies
- Official data field definitions for supported citizenship documents
- Policy on document acceptance and validation
- Authentication and identity assurance within Nagarik App
- Agency service forms that accept scanned document attachments
- Citizen support and escalation workflow

## Risks
- Poor image quality may reduce extraction accuracy.
- Document format variation may create inconsistent extraction performance.
- Citizens may distrust automatic data capture if corrections are not easy.
- Misuse or unauthorized storage of identity documents may create privacy concerns.
- Operational confusion may occur if agencies do not align on acceptance rules.

## Regulatory Considerations
- Personal data handling must comply with applicable Nepal privacy and data protection requirements.
- Identity documents must be stored, shared, and retained according to government record rules.
- Citizen consent and lawful basis for document capture must be explicit.
- Access must be restricted to authorized agencies and personnel.
- Retention and deletion must follow government archival and security policy.

## Success Metrics
- Document scan completion rate
- Field extraction accuracy rate
- Percentage of applications submitted without manual data entry
- Reduction in rejection due to missing document data
- User satisfaction with scan and review experience
- Reduction in support tickets related to document submission

---

# 2. Tax Estimation and Payment Assistance

## Problem Statement
Citizens and businesses often struggle to understand tax obligations, estimate amounts due, and complete payment steps correctly. This leads to underpayment, late payment, confusion, and unnecessary office visits.

## Business Objective
- Improve tax compliance and payment completion.
- Reduce taxpayer confusion and support inquiries.
- Increase timely revenue collection.
- Simplify payment preparation for citizens and businesses.

## User Personas
- Individual taxpayer
- Small business owner
- Self-employed professional
- Government tax officer
- Support staff assisting taxpayers

## User Journeys
- A user enters income or selects a relevant service and receives an estimated tax amount.
- The user reviews applicable tax components and prepares payment.
- The user receives guidance on approved payment channels.
- The user saves proof of payment or returns later to confirm payment status.

## User Stories
- As a taxpayer, I want an estimated tax amount so that I can plan for payment.
- As a taxpayer, I want to understand how the estimate was derived so that I can trust it.
- As a taxpayer, I want guidance on the payment process so that I can complete payment without visiting an office.
- As a tax officer, I want taxpayers to submit complete information so that processing is faster.
- As a support agent, I want to see what the user entered so that I can help resolve discrepancies.

## Functional Requirements
- The app shall support tax estimation for approved tax categories defined by government policy.
- The app shall explain the inputs used in the estimate in user-friendly language.
- The app shall show the due amount, due date, and relevant payment guidance.
- The app shall allow users to save and revisit estimates.
- The app shall link payment guidance to approved government channels only.
- The app shall allow users to record payment completion status where legally and operationally appropriate.
- The app shall display disclaimers where an estimate is not legally binding.
- The app shall support alerts for due dates and incomplete payment preparation.

## Non-Functional Requirements
- Calculations shall be consistent, accurate, and auditable.
- The experience shall be understandable to non-expert users.
- The feature shall remain responsive on low-bandwidth mobile networks.
- The feature shall be secure against unauthorized exposure of financial information.
- The feature shall provide high availability during tax filing and payment periods.

## Acceptance Criteria
- A user can obtain an estimate using approved input fields.
- The app clearly shows that estimates are advisory where applicable.
- The app provides payment guidance for approved channels.
- The user can revisit a saved estimate without re-entering all information.
- The estimate output includes enough explanation for the user to understand the basis.
- Tax officers and support staff can verify the user’s submitted inputs where permitted.

## Dependencies
- Tax policy rules and rate schedules
- Approved payment channels and treasury coordination
- Taxpayer identity and account linkage
- Agency-defined calculation and validation rules
- Notification service for reminders and due-date alerts

## Risks
- Tax policy changes may require frequent updates to rules and messaging.
- Incorrect user inputs may lead to inaccurate estimates.
- Users may interpret estimates as final legal assessments.
- External payment channel downtime may disrupt payment completion.
- High seasonal demand may affect availability.

## Regulatory Considerations
- Tax information is sensitive and subject to confidentiality obligations.
- Payment guidance must reflect only approved and lawful channels.
- Where estimates are not authoritative, the app must disclose that clearly.
- Auditability of calculations and user inputs is required.
- Any taxpayer data exchange must comply with finance and revenue regulations.

## Success Metrics
- Number of tax estimates generated
- Percentage of users who complete payment after using the estimator
- Reduction in taxpayer support inquiries
- Reduction in late or incomplete tax submissions
- User confidence score in estimate clarity
- Payment guidance click-through and completion rate

---

# 3. Government Application Tracking

## Problem Statement
Citizens often do not know the status of submitted government applications, which creates uncertainty, repeated follow-up visits, and mistrust in public service delivery.

## Business Objective
- Increase transparency in public service processing.
- Reduce follow-up calls and in-person status inquiries.
- Improve citizen trust and perceived service quality.
- Help agencies manage service accountability and workload visibility.

## User Personas
- Citizen applicant
- Family member tracking a dependent’s application where permitted
- Case worker or processing officer
- Call-center or help-desk staff
- Agency supervisor

## User Journeys
- A citizen submits an application and receives a tracking reference.
- The citizen checks status updates in the app without visiting the office.
- The app notifies the citizen when additional information is required.
- The officer updates the application stage in the agency workflow and the user sees the change.
- Support staff use the tracking number to assist with inquiries.

## User Stories
- As a citizen, I want to track my application status so that I know whether it is moving forward.
- As a citizen, I want to see if action is required from me so that I can respond promptly.
- As a case worker, I want application statuses to be visible to citizens so that they do not need to call repeatedly.
- As a support agent, I want to search by tracking reference so that I can answer status questions quickly.

## Functional Requirements
- The app shall display the current status of eligible applications.
- The app shall show milestone updates and the latest action taken.
- The app shall identify whether next action is required from the citizen, agency, or another party.
- The app shall provide the application reference number and submission date.
- The app shall support notifications for status changes.
- The app shall allow users to view the history of tracked applications.
- The app shall display clear status language, avoiding internal jargon where possible.
- The app shall support search and filter by application type and date.

## Non-Functional Requirements
- Status updates shall be timely and consistent with agency records.
- The feature shall be reliable across different agency service lines.
- The information presented shall be clear, accessible, and low-friction.
- The system shall preserve confidentiality for sensitive application categories.
- The feature shall support high demand without degrading status visibility.

## Acceptance Criteria
- A citizen can view the current status of a submitted application.
- Status changes are visible in the app within the agreed service update window.
- The app clearly identifies any action needed from the citizen.
- Support staff can use the tracking reference to locate the application status.
- The app shows historical status progression for eligible applications.
- The status labels are understandable to non-technical users.

## Dependencies
- Agency case management or workflow systems
- Defined status taxonomy and update rules
- Citizen identity verification and application linkage
- Notification center for status alerts
- Support center operating procedures

## Risks
- Agency systems may use inconsistent status definitions.
- Delayed updates could create user distrust.
- Overexposure of sensitive case details may create privacy issues.
- Some applications may not be eligible for public status display.
- Misinterpretation of status language may increase support inquiries.

## Regulatory Considerations
- Status visibility must respect confidentiality rules for sensitive applications.
- Public display of case details must be limited to authorized users only.
- Agencies must define which statuses can be shared and at what granularity.
- Record-keeping and audit requirements must be preserved.
- Access logging must support oversight and complaint handling.

## Success Metrics
- Percentage of applications with visible tracking status
- Reduction in inbound status inquiry calls or visits
- Average time for status update visibility
- User satisfaction with clarity of application progress
- Reduction in repeated duplicate submissions
- Number of applications completed without manual follow-up

---

# 4. Cross-Agency Service Integration

## Problem Statement
Citizens often must submit the same information to multiple agencies because public services are fragmented. This causes repeated effort, inconsistent records, and longer service completion times.

## Business Objective
- Reduce duplicate data submission across agencies.
- Enable joined-up public services around citizen life events.
- Improve service efficiency and coordination.
- Create a foundation for digital government interoperability.

## User Personas
- Citizen using multiple related services
- Agency officer relying on trusted data from another agency
- Service designer or policy analyst
- Government supervisor overseeing inter-agency service delivery
- Support agent assisting with service handoff issues

## User Journeys
- A citizen starts one service and is prompted to reuse verified information from another eligible agency source.
- The citizen authorizes sharing of selected data where required.
- The app guides the citizen through a multi-agency service sequence without repeating identical data entry.
- Agency officers receive only the data needed for their service step.
- The user can see which agencies are involved in the service flow.

## User Stories
- As a citizen, I want to reuse information already held by government so that I do not have to submit it again.
- As a citizen, I want to know which agencies will use my data so that I can make an informed choice.
- As an agency officer, I want trusted data from another agency so that I can process services faster.
- As a service designer, I want service handoffs to be visible so that I can reduce fragmentation.

## Functional Requirements
- The app shall support cross-agency data reuse where policy permits.
- The app shall show which agencies are participating in a service journey.
- The app shall request user consent or legal acknowledgment when required.
- The app shall minimize repeated user input across integrated services.
- The app shall indicate the source of reused data where appropriate.
- The app shall allow users to continue a service journey across agencies without losing progress.
- The app shall show service prerequisites, handoffs, and completion checkpoints.
- The app shall preserve a record of what was shared, when, and under what basis.

## Non-Functional Requirements
- The feature shall support secure data exchange across institutional boundaries.
- The feature shall maintain service continuity even when one agency responds slowly.
- The feature shall be extensible to new agencies and service types.
- The experience shall remain understandable despite cross-agency complexity.
- The feature shall support governance, audit, and traceability requirements.

## Acceptance Criteria
- A citizen can complete a multi-agency service journey without re-entering the same verified data where policy allows.
- The app clearly shows which agencies are involved in the service flow.
- The user can see what data is reused and can consent where required.
- Agency officers can receive a complete, policy-compliant service packet.
- Shared data usage is logged and auditable.
- The service journey can continue after a planned interruption without losing citizen progress.

## Dependencies
- Inter-agency data-sharing agreements
- Approved data dictionary and service standards
- Legal basis for data sharing and reuse
- Identity assurance and consent framework
- Agency readiness to participate in shared service flows

## Risks
- Inter-agency governance may be slow or contested.
- Inconsistent data quality across agencies may affect service reliability.
- Legal restrictions may limit the scope of reusable data.
- Service ownership disputes may create accountability gaps.
- Citizens may lose trust if reused data is incorrect or outdated.

## Regulatory Considerations
- Data sharing must be grounded in law, policy, or informed consent as applicable.
- Data minimization must apply to every agency interaction.
- Purpose limitation must be enforced for reused citizen data.
- Cross-border or third-party transfers are out of scope unless explicitly approved by government.
- Audit, access control, and retention standards must be harmonized across agencies.

## Success Metrics
- Number of services enabled through cross-agency integration
- Percentage of repeat data fields removed from citizen journeys
- Reduction in total steps to complete a multi-agency service
- Reduction in duplicate document requests
- User satisfaction with service continuity
- Number of inter-agency service handoffs completed successfully

---

# 5. Citizen Notification Center

## Problem Statement
Citizens receive fragmented, inconsistent, or delayed communication about service updates, reminders, and requests for action. Important notices can be missed, resulting in delays, missed deadlines, and additional follow-up costs.

## Business Objective
- Establish a trusted official channel for citizen communication.
- Improve response rates to government requests and reminders.
- Reduce missed deadlines and incomplete applications.
- Increase transparency and engagement across services.

## User Personas
- Citizen receiving service updates
- Citizen with limited digital literacy needing simple notifications
- Government officer sending official notices
- Support staff resolving notification disputes
- Agency administrator managing notification categories

## User Journeys
- A citizen receives a notification about a status update, due date, or required action.
- The citizen opens the app to read the full notice and any associated service record.
- The citizen dismisses, saves, or acts on the notification.
- The user reviews a history of previous notices in one place.
- The app differentiates urgent notices from routine informational updates.

## User Stories
- As a citizen, I want all official service notifications in one place so that I do not miss important information.
- As a citizen, I want to know whether a notification is urgent so that I can prioritize action.
- As a government officer, I want citizens to receive standard notices consistently so that service follow-up is more effective.
- As a support agent, I want to verify sent notices so that I can resolve disputes accurately.

## Functional Requirements
- The app shall provide a single inbox for official government notifications.
- The app shall support notification categories such as informational, required action, deadline, and status update.
- The app shall allow citizens to open, archive, and review prior notifications.
- The app shall link notifications to relevant applications or service records where applicable.
- The app shall distinguish official government notices from non-official messages.
- The app shall allow language-appropriate and plain-language notices.
- The app shall support reminders for deadlines, pending actions, and service milestones.
- The app shall support notification preferences where allowed by policy.

## Non-Functional Requirements
- Notifications shall be timely and dependable.
- The notification center shall be clear, readable, and accessible.
- The feature shall support users with low digital literacy through simple wording and icons where appropriate.
- The system shall be secure against spoofing and unauthorized message injection.
- The feature shall preserve a verifiable record of notices sent and received.

## Acceptance Criteria
- A citizen can view all official notifications in a single inbox.
- The system clearly marks urgent or action-required notices.
- Each notification can be opened to show related context where permitted.
- Citizens can review notification history.
- Government staff can confirm when a notice was sent.
- The app differentiates official notices from any non-official content.

## Dependencies
- Service events from tracking, tax, and application modules
- Notification policy and categories approved by government
- Citizen communication preferences and contact rules
- Language and content standards
- Audit and dispute-resolution process

## Risks
- Poorly written notices may confuse citizens or reduce trust.
- Excessive notifications may cause fatigue and disengagement.
- Misclassification of urgent versus routine notices may have legal consequences.
- Spoofed or fraudulent notifications could damage confidence.
- Different agencies may send inconsistent message styles without governance.

## Regulatory Considerations
- Official notifications may carry legal significance and must meet required notice standards.
- Privacy and confidentiality rules apply to the content and recipients of notices.
- Opt-in, opt-out, or mandatory notice rules must follow applicable policy.
- Retention rules must govern notification records and delivery logs.
- Language accessibility requirements may apply depending on service scope and policy.

## Success Metrics
- Notification open rate
- Action completion rate after notification
- Reduction in missed deadlines or missed appointments
- Reduction in inbound follow-up inquiries
- User trust score for notification accuracy
- Percentage of notices delivered within expected service window

---

# Program-Level Success Metrics
- Increase in active Nagarik App usage
- Reduction in in-person visits for eligible services
- Reduction in duplicate data entry across government services
- Improvement in service completion time
- Improvement in citizen satisfaction with digital services
- Increase in number of applications and transactions completed end-to-end in-app

## Governance Requirements
- A cross-agency product governance body should approve scope, priorities, and policy dependencies.
- Each feature should have an accountable agency owner and service steward.
- Privacy, legal, security, and records-retention review should be mandatory before release.
- Service catalog, status taxonomy, and notification classes should be standardized before broad rollout.
