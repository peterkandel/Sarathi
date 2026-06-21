# Workflow Orchestration Engine Design

## Scope
This design defines a configurable workflow orchestration engine for the following supported processes:
- Citizenship
- Passport
- Driving License
- PAN Registration

The design covers state machine architecture, workflow definitions, escalation rules, SLA tracking, notifications, audit trails, database schema, and APIs.

## Structured Output

### 1. State Machine Architecture
```json
{
  "engine_name": "Government Workflow Orchestration Engine",
  "architecture_style": "Configurable state machine engine with policy-driven transitions and asynchronous task execution",
  "design_goals": [
    "Support multiple government workflows in one orchestration platform",
    "Allow process definitions to change without code changes",
    "Provide auditable state transitions",
    "Track SLAs and escalations as first-class workflow concerns",
    "Trigger notifications from workflow events",
    "Support citizen, officer, and agency handoff states",
    "Handle synchronous and asynchronous steps consistently"
  ],
  "core_building_blocks": [
    {
      "name": "Workflow Definition Registry",
      "purpose": "Stores versioned workflow definitions, states, transitions, guards, SLAs, and escalation policies."
    },
    {
      "name": "Workflow Instance Manager",
      "purpose": "Creates and advances individual workflow instances for citizen applications."
    },
    {
      "name": "State Transition Engine",
      "purpose": "Evaluates allowed transitions and executes state changes deterministically."
    },
    {
      "name": "Task Orchestrator",
      "purpose": "Creates human and system tasks, assigns owners, and tracks completion."
    },
    {
      "name": "SLA Monitor",
      "purpose": "Computes deadlines, overdue states, and escalation triggers."
    },
    {
      "name": "Escalation Manager",
      "purpose": "Applies policy-driven escalation paths when SLAs or guards are violated."
    },
    {
      "name": "Notification Adapter",
      "purpose": "Emits citizen and officer notifications from workflow events."
    },
    {
      "name": "Audit Publisher",
      "purpose": "Writes immutable workflow events and state history for compliance."
    }
  ],
  "state_machine_model": {
    "state_types": ["initial", "active", "waiting", "blocked", "escalated", "completed", "rejected", "cancelled"],
    "transition_types": ["automatic", "manual", "system_event", "timer_event", "approval_event"],
    "guard_types": ["field_validation", "document_presence", "identity_verified", "payment_confirmed", "sla_due", "role_authorized", "external_reference_available"],
    "event_sources": ["citizen action", "officer action", "system callback", "timer", "external agency event"]
  },
  "recommended_runtime": {
    "api_layer": "FastAPI",
    "workflow_state_store": "PostgreSQL",
    "fast_state_cache": "Redis",
    "eventing": "Message broker / event bus",
    "document_artifacts": "S3-compatible object storage"
  }
}
```

### 2. Workflow Definitions
```json
{
  "workflow_definitions": [
    {
      "workflow_code": "citizenship_registration",
      "workflow_name": "Citizenship",
      "purpose": "Manage citizenship application intake, verification, review, approval, and issuance.",
      "version": 1,
      "states": [
        "draft",
        "submitted",
        "identity_verification_pending",
        "document_review_pending",
        "field_verification_pending",
        "field_verification_failed",
        "officer_review_pending",
        "additional_information_required",
        "approved",
        "rejected",
        "issued",
        "completed",
        "cancelled"
      ],
      "transitions": [
        {"from": "draft", "event": "submit_application", "to": "submitted"},
        {"from": "submitted", "event": "identity_verified", "to": "identity_verification_pending"},
        {"from": "identity_verification_pending", "event": "documents_received", "to": "document_review_pending"},
        {"from": "document_review_pending", "event": "field_verification_passed", "to": "field_verification_pending"},
        {"from": "document_review_pending", "event": "field_verification_failed", "to": "field_verification_failed"},
        {"from": "field_verification_pending", "event": "officer_assigned", "to": "officer_review_pending"},
        {"from": "officer_review_pending", "event": "more_info_requested", "to": "additional_information_required"},
        {"from": "officer_review_pending", "event": "approved", "to": "approved"},
        {"from": "approved", "event": "issued", "to": "issued"},
        {"from": "issued", "event": "close_case", "to": "completed"}
      ],
      "key_tasks": ["identity check", "document validation", "field verification", "officer review", "issuance"],
      "primary_sla_hours": 72
    },
    {
      "workflow_code": "passport_application",
      "workflow_name": "Passport",
      "purpose": "Manage passport application intake, payment confirmation, biometric scheduling, review, and issuance.",
      "version": 1,
      "states": [
        "draft",
        "submitted",
        "payment_pending",
        "payment_confirmed",
        "biometric_scheduling_pending",
        "biometrics_completed",
        "security_check_pending",
        "officer_review_pending",
        "approved",
        "printed",
        "issued",
        "completed",
        "rejected",
        "cancelled"
      ],
      "transitions": [
        {"from": "draft", "event": "submit_application", "to": "submitted"},
        {"from": "submitted", "event": "payment_required", "to": "payment_pending"},
        {"from": "payment_pending", "event": "payment_confirmed", "to": "payment_confirmed"},
        {"from": "payment_confirmed", "event": "schedule_biometrics", "to": "biometric_scheduling_pending"},
        {"from": "biometric_scheduling_pending", "event": "biometrics_completed", "to": "biometrics_completed"},
        {"from": "biometrics_completed", "event": "security_check_passed", "to": "security_check_pending"},
        {"from": "security_check_pending", "event": "officer_review_started", "to": "officer_review_pending"},
        {"from": "officer_review_pending", "event": "approved", "to": "approved"},
        {"from": "approved", "event": "print_completed", "to": "printed"},
        {"from": "printed", "event": "issued", "to": "issued"},
        {"from": "issued", "event": "close_case", "to": "completed"}
      ],
      "key_tasks": ["fee confirmation", "biometric booking", "security clearance", "approval", "print and dispatch"],
      "primary_sla_hours": 168
    },
    {
      "workflow_code": "driving_license_application",
      "workflow_name": "Driving License",
      "purpose": "Manage driving license application intake, eligibility checks, testing, review, and issuance.",
      "version": 1,
      "states": [
        "draft",
        "submitted",
        "eligibility_check_pending",
        "medical_clearance_pending",
        "test_scheduling_pending",
        "test_completed",
        "test_failed",
        "officer_review_pending",
        "approved",
        "card_print_pending",
        "issued",
        "completed",
        "rejected",
        "cancelled"
      ],
      "transitions": [
        {"from": "draft", "event": "submit_application", "to": "submitted"},
        {"from": "submitted", "event": "eligibility_verified", "to": "eligibility_check_pending"},
        {"from": "eligibility_check_pending", "event": "medical_cleared", "to": "medical_clearance_pending"},
        {"from": "medical_clearance_pending", "event": "test_scheduled", "to": "test_scheduling_pending"},
        {"from": "test_scheduling_pending", "event": "test_passed", "to": "test_completed"},
        {"from": "test_scheduling_pending", "event": "test_failed", "to": "test_failed"},
        {"from": "test_completed", "event": "officer_review_started", "to": "officer_review_pending"},
        {"from": "officer_review_pending", "event": "approved", "to": "approved"},
        {"from": "approved", "event": "print_completed", "to": "card_print_pending"},
        {"from": "card_print_pending", "event": "issued", "to": "issued"},
        {"from": "issued", "event": "close_case", "to": "completed"}
      ],
      "key_tasks": ["eligibility check", "medical clearance", "test scheduling", "test result", "license issuance"],
      "primary_sla_hours": 96
    },
    {
      "workflow_code": "pan_registration",
      "workflow_name": "PAN Registration",
      "purpose": "Manage PAN registration intake, verification, approval, and PAN issuance.",
      "version": 1,
      "states": [
        "draft",
        "submitted",
        "identity_check_pending",
        "taxpayer_validation_pending",
        "officer_review_pending",
        "additional_information_required",
        "approved",
        "pan_allocated",
        "issued",
        "completed",
        "rejected",
        "cancelled"
      ],
      "transitions": [
        {"from": "draft", "event": "submit_application", "to": "submitted"},
        {"from": "submitted", "event": "identity_verified", "to": "identity_check_pending"},
        {"from": "identity_check_pending", "event": "taxpayer_validated", "to": "taxpayer_validation_pending"},
        {"from": "taxpayer_validation_pending", "event": "officer_review_started", "to": "officer_review_pending"},
        {"from": "officer_review_pending", "event": "more_info_requested", "to": "additional_information_required"},
        {"from": "officer_review_pending", "event": "approved", "to": "approved"},
        {"from": "approved", "event": "pan_allocated", "to": "pan_allocated"},
        {"from": "pan_allocated", "event": "issued", "to": "issued"},
        {"from": "issued", "event": "close_case", "to": "completed"}
      ],
      "key_tasks": ["identity validation", "taxpayer validation", "officer review", "PAN allocation"],
      "primary_sla_hours": 48
    }
  ],
  "common_state_patterns": [
    "draft to submitted",
    "submitted to validation states",
    "validation to review states",
    "review to approved or rejected",
    "approved to issuance",
    "issuance to completed"
  ]
}
```

### Workflow State Machine Pattern
```json
{
  "state_machine_pattern": {
    "state_record": {
      "workflow_instance_id": "uuid",
      "workflow_definition_id": "uuid",
      "current_state": "string",
      "previous_state": "string",
      "entered_at": "datetime",
      "version": "integer"
    },
    "transition_record": {
      "workflow_instance_id": "uuid",
      "from_state": "string",
      "to_state": "string",
      "trigger_event": "string",
      "trigger_type": "manual | automatic | timer | external",
      "actor_type": "citizen | officer | system | agency",
      "actor_reference": "string",
      "transition_at": "datetime",
      "notes": "string"
    },
    "guard_evaluation": {
      "guard_code": "string",
      "status": "passed | failed | skipped",
      "reason": "string"
    }
  }
}
```

### 3. Escalation Rules
```json
{
  "escalation_policy": {
    "principles": [
      "Escalations are policy-driven and configured per workflow version",
      "All escalations generate audit events",
      "Escalations may notify citizens, officers, supervisors, and agencies",
      "Repeated SLA misses should promote to higher tiers automatically",
      "Manual override must be role-restricted and fully logged"
    ],
    "escalation_tiers": [
      {
        "tier": 1,
        "name": "Reminder",
        "trigger": "SLA warning threshold reached",
        "actions": ["send_citizen_reminder", "send_officer_notification", "create_inbox_alert"]
      },
      {
        "tier": 2,
        "name": "Supervisor Review",
        "trigger": "SLA due time exceeded by grace period",
        "actions": ["assign_supervisor_task", "flag_instance", "increase_priority"]
      },
      {
        "tier": 3,
        "name": "Service Management Escalation",
        "trigger": "SLA exceeded by critical threshold",
        "actions": ["notify_service_manager", "generate_overdue_case", "request_reason_code"]
      },
      {
        "tier": 4,
        "name": "Policy Escalation",
        "trigger": "Systemic repeated SLA breach or blocked external dependency",
        "actions": ["escalate_to_agency_admin", "open_operational_incident", "publish_audit_event"]
      }
    ],
    "workflow_specific_rules": [
      {
        "workflow_code": "citizenship_registration",
        "conditions": ["document_review_pending > 24h", "officer_review_pending > 48h"],
        "actions": ["remind_assigned_officer", "notify_supervisor", "flag_priority_queue"]
      },
      {
        "workflow_code": "passport_application",
        "conditions": ["payment_pending > 12h", "security_check_pending > 72h"],
        "actions": ["remind_citizen", "remind_approver", "escalate_to_supervisor"]
      },
      {
        "workflow_code": "driving_license_application",
        "conditions": ["test_scheduling_pending > 48h", "test_completed waiting review > 24h"],
        "actions": ["notify_test_center", "notify_citizen", "escalate_to_branch_manager"]
      },
      {
        "workflow_code": "pan_registration",
        "conditions": ["taxpayer_validation_pending > 24h", "officer_review_pending > 24h"],
        "actions": ["notify_tax_officer", "notify_supervisor", "create_overdue_task"]
      }
    ],
    "manual_override_controls": [
      "Require role-based permission",
      "Require reason code",
      "Record before-and-after state",
      "Emit audit event",
      "Disallow override of terminal rejection without authorization"
    ]
  }
}
```

### 4. SLA Tracking
```json
{
  "sla_model": {
    "targets": [
      {
        "workflow_code": "citizenship_registration",
        "target_hours": 72,
        "warning_threshold_hours": 48,
        "grace_period_hours": 6
      },
      {
        "workflow_code": "passport_application",
        "target_hours": 168,
        "warning_threshold_hours": 120,
        "grace_period_hours": 12
      },
      {
        "workflow_code": "driving_license_application",
        "target_hours": 96,
        "warning_threshold_hours": 72,
        "grace_period_hours": 8
      },
      {
        "workflow_code": "pan_registration",
        "target_hours": 48,
        "warning_threshold_hours": 24,
        "grace_period_hours": 4
      }
    ],
    "sla_metrics": [
      "time_in_state",
      "time_to_first_action",
      "time_to_review",
      "time_to_completion",
      "overdue_count",
      "escalation_count"
    ],
    "sla_calculation_rules": [
      "Measure from state entry time to state exit time",
      "Exclude paused intervals if the workflow definition explicitly marks the state as non-counting",
      "Apply working-hours calendars when configured",
      "Retain historical SLA snapshots at each transition",
      "Compute remaining SLA time from the latest active state"
    ],
    "sla_data_points": {
      "deadline_at": "datetime",
      "remaining_hours": "number",
      "breach_flag": "boolean",
      "warning_flag": "boolean",
      "paused_flag": "boolean"
    }
  }
}
```

### 5. Notifications
```json
{
  "notification_policy": {
    "channels": ["in_app", "push", "sms", "email"],
    "triggers": [
      "workflow_submitted",
      "task_assigned",
      "state_changed",
      "slas_warning",
      "sla_breached",
      "additional_information_required",
      "approved",
      "rejected",
      "issued"
    ],
    "recipients": [
      "citizen",
      "assigned_officer",
      "supervisor",
      "agency_admin",
      "support_agent"
    ],
    "notification_templates": [
      {
        "template_code": "workflow_state_changed",
        "variables": ["workflow_name", "old_state", "new_state", "reference_no"]
      },
      {
        "template_code": "sla_warning",
        "variables": ["workflow_name", "deadline_at", "remaining_hours"]
      },
      {
        "template_code": "sla_breached",
        "variables": ["workflow_name", "breach_duration", "next_action"]
      },
      {
        "template_code": "additional_info_request",
        "variables": ["workflow_name", "requested_items", "due_date"]
      }
    ],
    "notification_rules": [
      "Notify the citizen when a state changes materially",
      "Notify officers when a task becomes assigned or overdue",
      "Notify supervisors on repeated overdue conditions",
      "Throttle duplicate notifications within a configurable window",
      "Persist notification events for audit and dispute handling"
    ]
  }
}
```

### 6. Audit Trails
```json
{
  "audit_design": {
    "audit_objectives": [
      "Reconstruct every workflow state change",
      "Prove who performed each action",
      "Show when SLAs were created and breached",
      "Demonstrate why escalations were triggered",
      "Provide evidence for appeals and oversight"
    ],
    "audited_events": [
      "WorkflowDefinitionCreated",
      "WorkflowDefinitionUpdated",
      "WorkflowInstanceCreated",
      "WorkflowInstanceTransitioned",
      "WorkflowTaskAssigned",
      "WorkflowTaskCompleted",
      "SLAWarningRaised",
      "SLABreached",
      "EscalationTriggered",
      "NotificationSent",
      "ManualOverrideApplied"
    ],
    "audit_fields": [
      "event_id",
      "workflow_instance_id",
      "workflow_definition_id",
      "state_from",
      "state_to",
      "trigger_event",
      "actor_type",
      "actor_reference",
      "correlation_id",
      "event_at",
      "event_payload"
    ],
    "controls": [
      "Append-only audit store",
      "Immutable transition history",
      "Correlation IDs across notifications and escalations",
      "Role-restricted override logging",
      "Checksum or hash of published workflow definitions"
    ]
  }
}
```

## 7. Database Schema
```json
{
  "schema_name": "workflow_engine",
  "schema_principles": {
    "primary_keys": "UUID",
    "naming": "snake_case",
    "audit_fields": ["created_at", "updated_at", "deleted_at", "created_by_actor_id", "updated_by_actor_id"],
    "soft_delete": "deleted_at",
    "multi_agency": "agency_id on agency-owned tables",
    "versioning": "workflow definitions and SLA policies are versioned and effective-dated"
  },
  "tables": [
    {
      "name": "workflow_engine.workflow_definitions",
      "purpose": "Stores versioned workflow definitions for all supported processes.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "workflow_code", "type": "text", "constraints": ["not null"]},
        {"name": "workflow_name", "type": "text", "constraints": ["not null"]},
        {"name": "workflow_version", "type": "integer", "constraints": ["not null", "check workflow_version > 0"]},
        {"name": "status", "type": "text", "constraints": ["not null", "check status in ('draft','approved','active','retired')"]},
        {"name": "description", "type": "text", "constraints": ["not null"]},
        {"name": "effective_from", "type": "date", "constraints": ["not null"]},
        {"name": "effective_to", "type": "date", "constraints": ["null"]},
        {"name": "definition_hash", "type": "text", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(workflow_code, workflow_version)",
        "check effective_to is null or effective_to >= effective_from"
      ],
      "indexes": [
        "ix_workflow_definitions_agency_id",
        "ix_workflow_definitions_workflow_code",
        "ix_workflow_definitions_status",
        "uq_workflow_definitions_active"
      ],
      "relationships": ["Parent table for states, transitions, SLAs, and escalation policies."]
    },
    {
      "name": "workflow_engine.workflow_states",
      "purpose": "Stores states belonging to a workflow definition.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "workflow_definition_id", "type": "uuid", "constraints": ["not null", "fk workflow_definitions.id"]},
        {"name": "state_code", "type": "text", "constraints": ["not null"]},
        {"name": "state_name", "type": "text", "constraints": ["not null"]},
        {"name": "state_type", "type": "text", "constraints": ["not null", "check state_type in ('initial','active','waiting','blocked','escalated','completed','rejected','cancelled')"]},
        {"name": "is_terminal", "type": "boolean", "constraints": ["not null", "default false"]},
        {"name": "sort_order", "type": "integer", "constraints": ["not null", "default 0"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["unique active(workflow_definition_id, state_code)"] ,
      "indexes": ["ix_workflow_states_workflow_definition_id", "ix_workflow_states_state_type"],
      "relationships": ["Many states belong to one workflow definition."]
    },
    {
      "name": "workflow_engine.workflow_transitions",
      "purpose": "Stores allowed transitions between states.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "workflow_definition_id", "type": "uuid", "constraints": ["not null", "fk workflow_definitions.id"]},
        {"name": "from_state_id", "type": "uuid", "constraints": ["not null", "fk workflow_states.id"]},
        {"name": "to_state_id", "type": "uuid", "constraints": ["not null", "fk workflow_states.id"]},
        {"name": "trigger_event", "type": "text", "constraints": ["not null"]},
        {"name": "transition_type", "type": "text", "constraints": ["not null", "check transition_type in ('automatic','manual','system_event','timer_event','approval_event')"]},
        {"name": "guard_expression", "type": "jsonb", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["unique active(workflow_definition_id, from_state_id, trigger_event)"] ,
      "indexes": ["ix_workflow_transitions_workflow_definition_id", "ix_workflow_transitions_from_state_id", "ix_workflow_transitions_trigger_event"],
      "relationships": ["Many transitions belong to one workflow definition."]
    },
    {
      "name": "workflow_engine.workflow_instances",
      "purpose": "Stores one running case or application instance.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "workflow_definition_id", "type": "uuid", "constraints": ["not null", "fk workflow_definitions.id"]},
        {"name": "reference_no", "type": "text", "constraints": ["not null"]},
        {"name": "citizen_profile_id", "type": "uuid", "constraints": ["not null"]},
        {"name": "current_state_id", "type": "uuid", "constraints": ["not null", "fk workflow_states.id"]},
        {"name": "instance_status", "type": "text", "constraints": ["not null", "check instance_status in ('active','completed','cancelled','rejected')"]},
        {"name": "started_at", "type": "timestamptz", "constraints": ["not null"]},
        {"name": "completed_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "correlation_id", "type": "uuid", "constraints": ["null"]},
        {"name": "context_payload", "type": "jsonb", "constraints": ["not null", "default '{}'::jsonb"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["unique active(reference_no)", "instance current_state must belong to the selected workflow definition"],
      "indexes": ["ix_workflow_instances_agency_id", "ix_workflow_instances_workflow_definition_id", "ix_workflow_instances_citizen_profile_id", "ix_workflow_instances_instance_status", "uq_workflow_instances_reference_no_active"],
      "relationships": ["Many instances belong to one workflow definition and one citizen profile."]
    },
    {
      "name": "workflow_engine.workflow_instance_states",
      "purpose": "Captures state history for each workflow instance.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "workflow_instance_id", "type": "uuid", "constraints": ["not null", "fk workflow_instances.id"]},
        {"name": "state_id", "type": "uuid", "constraints": ["not null", "fk workflow_states.id"]},
        {"name": "entered_at", "type": "timestamptz", "constraints": ["not null"]},
        {"name": "exited_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "entry_reason", "type": "text", "constraints": ["null"]},
        {"name": "exit_reason", "type": "text", "constraints": ["null"]},
        {"name": "sla_deadline_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "sla_breached_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "escalation_level", "type": "integer", "constraints": ["not null", "default 0"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["one active state entry per instance at a time"],
      "indexes": ["ix_workflow_instance_states_workflow_instance_id", "ix_workflow_instance_states_state_id", "ix_workflow_instance_states_entered_at"],
      "relationships": ["Many state history records belong to one workflow instance."]
    },
    {
      "name": "workflow_engine.workflow_tasks",
      "purpose": "Stores human or system tasks created by the engine.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "workflow_instance_id", "type": "uuid", "constraints": ["not null", "fk workflow_instances.id"]},
        {"name": "task_code", "type": "text", "constraints": ["not null"]},
        {"name": "task_name", "type": "text", "constraints": ["not null"]},
        {"name": "task_type", "type": "text", "constraints": ["not null", "check task_type in ('citizen','officer','system','agency')"]},
        {"name": "assigned_party", "type": "text", "constraints": ["not null"]},
        {"name": "task_status", "type": "text", "constraints": ["not null", "check task_status in ('pending','assigned','in_progress','completed','blocked','cancelled')"]},
        {"name": "due_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "completed_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "task_payload", "type": "jsonb", "constraints": ["not null", "default '{}'::jsonb"]},
        {"name": "priority", "type": "integer", "constraints": ["not null", "default 0"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["unique active(workflow_instance_id, task_code)"] ,
      "indexes": ["ix_workflow_tasks_workflow_instance_id", "ix_workflow_tasks_task_status", "ix_workflow_tasks_due_at"],
      "relationships": ["Many tasks belong to one workflow instance."]
    },
    {
      "name": "workflow_engine.workflow_sla_policies",
      "purpose": "Stores SLA definitions for workflow states and processes.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "workflow_definition_id", "type": "uuid", "constraints": ["not null", "fk workflow_definitions.id"]},
        {"name": "state_id", "type": "uuid", "constraints": ["null", "fk workflow_states.id"]},
        {"name": "policy_name", "type": "text", "constraints": ["not null"]},
        {"name": "target_hours", "type": "integer", "constraints": ["not null", "check target_hours >= 0"]},
        {"name": "warning_threshold_hours", "type": "integer", "constraints": ["not null", "check warning_threshold_hours >= 0"]},
        {"name": "grace_period_hours", "type": "integer", "constraints": ["not null", "check grace_period_hours >= 0"]},
        {"name": "calendar_code", "type": "text", "constraints": ["null"]},
        {"name": "count_paused_time", "type": "boolean", "constraints": ["not null", "default false"]},
        {"name": "policy_status", "type": "text", "constraints": ["not null", "check policy_status in ('draft','active','retired')"]},
        {"name": "effective_from", "type": "date", "constraints": ["not null"]},
        {"name": "effective_to", "type": "date", "constraints": ["null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["unique active(workflow_definition_id, policy_name, effective_from)"] ,
      "indexes": ["ix_workflow_sla_policies_agency_id", "ix_workflow_sla_policies_workflow_definition_id", "ix_workflow_sla_policies_state_id", "ix_workflow_sla_policies_policy_status"],
      "relationships": ["Many SLA policies belong to one workflow definition."]
    },
    {
      "name": "workflow_engine.workflow_escalation_rules",
      "purpose": "Stores escalation rules tied to SLA breaches and state conditions.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "workflow_definition_id", "type": "uuid", "constraints": ["not null", "fk workflow_definitions.id"]},
        {"name": "policy_name", "type": "text", "constraints": ["not null"]},
        {"name": "tier_level", "type": "integer", "constraints": ["not null", "check tier_level > 0"]},
        {"name": "trigger_expression", "type": "jsonb", "constraints": ["not null"]},
        {"name": "actions", "type": "jsonb", "constraints": ["not null"]},
        {"name": "escalation_status", "type": "text", "constraints": ["not null", "check escalation_status in ('draft','active','retired')"]},
        {"name": "effective_from", "type": "date", "constraints": ["not null"]},
        {"name": "effective_to", "type": "date", "constraints": ["null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["unique active(workflow_definition_id, policy_name, tier_level, effective_from)"] ,
      "indexes": ["ix_workflow_escalation_rules_agency_id", "ix_workflow_escalation_rules_workflow_definition_id", "ix_workflow_escalation_rules_tier_level", "ix_workflow_escalation_rules_escalation_status"],
      "relationships": ["Many escalation rules belong to one workflow definition."]
    },
    {
      "name": "workflow_engine.workflow_notifications",
      "purpose": "Stores notifications generated by workflow events.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "workflow_instance_id", "type": "uuid", "constraints": ["not null", "fk workflow_instances.id"]},
        {"name": "notification_type", "type": "text", "constraints": ["not null"]},
        {"name": "recipient_type", "type": "text", "constraints": ["not null", "check recipient_type in ('citizen','officer','supervisor','agency','support_agent')"]},
        {"name": "recipient_reference", "type": "text", "constraints": ["not null"]},
        {"name": "channel", "type": "text", "constraints": ["not null", "check channel in ('in_app','push','sms','email')"]},
        {"name": "template_code", "type": "text", "constraints": ["not null"]},
        {"name": "payload", "type": "jsonb", "constraints": ["not null"]},
        {"name": "delivery_status", "type": "text", "constraints": ["not null", "check delivery_status in ('queued','sent','delivered','failed')"]},
        {"name": "sent_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "delivered_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "failure_reason", "type": "text", "constraints": ["null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["notification delivery should be idempotent by workflow event and template code"] ,
      "indexes": ["ix_workflow_notifications_workflow_instance_id", "ix_workflow_notifications_notification_type", "ix_workflow_notifications_delivery_status"],
      "relationships": ["Many notifications belong to one workflow instance."]
    },
    {
      "name": "workflow_engine.workflow_audit_events",
      "purpose": "Stores immutable audit events for workflow operations.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "event_type", "type": "text", "constraints": ["not null"]},
        {"name": "workflow_instance_id", "type": "uuid", "constraints": ["null", "fk workflow_instances.id"]},
        {"name": "workflow_definition_id", "type": "uuid", "constraints": ["null", "fk workflow_definitions.id"]},
        {"name": "actor_type", "type": "text", "constraints": ["not null", "check actor_type in ('citizen','officer','system','agency')"]},
        {"name": "actor_reference", "type": "text", "constraints": ["null"]},
        {"name": "correlation_id", "type": "uuid", "constraints": ["null"]},
        {"name": "event_payload", "type": "jsonb", "constraints": ["not null"]},
        {"name": "event_at", "type": "timestamptz", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": ["append-only semantics for published audit events"],
      "indexes": ["ix_workflow_audit_events_agency_id", "ix_workflow_audit_events_workflow_instance_id", "ix_workflow_audit_events_event_at", "ix_workflow_audit_events_correlation_id"],
      "relationships": ["Audit event rows may reference workflow definitions or workflow instances."]
    }
  ]
}
```

## 8. APIs
```json
{
  "api_version": "v1",
  "base_path": "/workflow-engine/v1",
  "authentication": {
    "scheme": "Bearer JWT",
    "service_to_service": "mTLS plus signed service credentials"
  },
  "endpoints": [
    {
      "method": "POST",
      "path": "/definitions",
      "purpose": "Create a draft workflow definition.",
      "authorization": ["workflow administrator access"],
      "request_schema": {
        "type": "object",
        "required": ["workflow_code", "workflow_name", "description", "effective_from", "states", "transitions"],
        "properties": {
          "workflow_code": {"type": "string"},
          "workflow_name": {"type": "string"},
          "description": {"type": "string"},
          "effective_from": {"type": "string", "format": "date"},
          "states": {"type": "array", "items": {"type": "object"}},
          "transitions": {"type": "array", "items": {"type": "object"}},
          "sla_policies": {"type": "array", "items": {"type": "object"}},
          "escalation_rules": {"type": "array", "items": {"type": "object"}}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["definition_id", "status", "workflow_version"],
        "properties": {
          "definition_id": {"type": "string", "format": "uuid"},
          "status": {"type": "string", "enum": ["draft", "approved", "active"]},
          "workflow_version": {"type": "integer"}
        }
      },
      "error_responses": [400, 401, 403, 409, 422]
    },
    {
      "method": "GET",
      "path": "/definitions",
      "purpose": "List workflow definitions with optional filters.",
      "authorization": ["workflow administrator access", "audit access", "agency officer access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "workflow_code": {"type": "string"},
          "status": {"type": "string"},
          "agency_id": {"type": "string", "format": "uuid"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["items", "page"],
        "properties": {
          "items": {"type": "array", "items": {"type": "object"}},
          "page": {"type": "object"}
        }
      },
      "error_responses": [401, 403]
    },
    {
      "method": "POST",
      "path": "/instances",
      "purpose": "Create a workflow instance for a citizen application.",
      "authorization": ["citizen access", "officer access", "system-to-system access"],
      "request_schema": {
        "type": "object",
        "required": ["workflow_code", "citizen_profile_id", "reference_no", "context_payload"],
        "properties": {
          "workflow_code": {"type": "string"},
          "workflow_version": {"type": "integer"},
          "agency_id": {"type": "string", "format": "uuid"},
          "citizen_profile_id": {"type": "string", "format": "uuid"},
          "reference_no": {"type": "string"},
          "context_payload": {"type": "object", "additionalProperties": true}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["instance_id", "reference_no", "current_state", "instance_status"],
        "properties": {
          "instance_id": {"type": "string", "format": "uuid"},
          "reference_no": {"type": "string"},
          "current_state": {"type": "string"},
          "instance_status": {"type": "string"}
        }
      },
      "error_responses": [400, 401, 403, 409, 422]
    },
    {
      "method": "GET",
      "path": "/instances/{instance_id}",
      "purpose": "Retrieve workflow instance state and metadata.",
      "authorization": ["citizen owner access", "officer access", "support access", "audit access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "instance_id": {"type": "string", "format": "uuid"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["instance_id", "reference_no", "current_state", "history"],
        "properties": {
          "instance_id": {"type": "string", "format": "uuid"},
          "reference_no": {"type": "string"},
          "current_state": {"type": "string"},
          "history": {"type": "array", "items": {"type": "object"}},
          "tasks": {"type": "array", "items": {"type": "object"}},
          "sla": {"type": "object"}
        }
      },
      "error_responses": [401, 403, 404]
    },
    {
      "method": "POST",
      "path": "/instances/{instance_id}/events",
      "purpose": "Advance a workflow instance using an explicit event.",
      "authorization": ["citizen access where allowed", "officer access", "system-to-system access"],
      "request_schema": {
        "type": "object",
        "required": ["event_type"],
        "properties": {
          "event_type": {"type": "string"},
          "payload": {"type": "object", "additionalProperties": true},
          "idempotency_key": {"type": "string"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["instance_id", "previous_state", "current_state", "transition_at"],
        "properties": {
          "instance_id": {"type": "string", "format": "uuid"},
          "previous_state": {"type": "string"},
          "current_state": {"type": "string"},
          "transition_at": {"type": "string", "format": "date-time"},
          "tasks_created": {"type": "array", "items": {"type": "object"}},
          "notifications_created": {"type": "array", "items": {"type": "object"}}
        }
      },
      "error_responses": [400, 401, 403, 404, 409, 422]
    },
    {
      "method": "POST",
      "path": "/instances/{instance_id}/tasks/{task_id}/complete",
      "purpose": "Complete a workflow task.",
      "authorization": ["assigned citizen access", "assigned officer access", "system access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "result_payload": {"type": "object", "additionalProperties": true},
          "comment": {"type": "string"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["task_id", "task_status", "completed_at"],
        "properties": {
          "task_id": {"type": "string", "format": "uuid"},
          "task_status": {"type": "string"},
          "completed_at": {"type": "string", "format": "date-time"}
        }
      },
      "error_responses": [401, 403, 404, 409, 422]
    },
    {
      "method": "GET",
      "path": "/instances/{instance_id}/sla",
      "purpose": "Retrieve SLA status for a workflow instance.",
      "authorization": ["citizen owner access", "officer access", "supervisor access", "audit access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "instance_id": {"type": "string", "format": "uuid"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["instance_id", "deadline_at", "remaining_hours", "breach_flag"],
        "properties": {
          "instance_id": {"type": "string", "format": "uuid"},
          "deadline_at": {"type": "string", "format": "date-time"},
          "remaining_hours": {"type": "number"},
          "warning_flag": {"type": "boolean"},
          "breach_flag": {"type": "boolean"},
          "escalation_level": {"type": "integer"}
        }
      },
      "error_responses": [401, 403, 404]
    },
    {
      "method": "POST",
      "path": "/instances/{instance_id}/escalate",
      "purpose": "Force or apply an escalation under policy control.",
      "authorization": ["supervisor access", "agency admin access"],
      "request_schema": {
        "type": "object",
        "required": ["reason_code"],
        "properties": {
          "reason_code": {"type": "string"},
          "notes": {"type": "string"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["instance_id", "escalation_level", "triggered_at"],
        "properties": {
          "instance_id": {"type": "string", "format": "uuid"},
          "escalation_level": {"type": "integer"},
          "triggered_at": {"type": "string", "format": "date-time"}
        }
      },
      "error_responses": [401, 403, 404, 409, 422]
    }
  ]
}
```

### Pagination Contract
```json
{
  "pagination": {
    "style": "limit-offset",
    "request_parameters": ["limit", "offset"],
    "response_envelope": {
      "items": [],
      "page": {
        "limit": 20,
        "offset": 0,
        "total": 0
      }
    },
    "recommended_limits": {
      "default": 20,
      "maximum": 100
    }
  }
}
```

## 9. Audit Strategy
```json
{
  "audit_strategy": {
    "objectives": [
      "Reconstruct every transition and task completion",
      "Prove SLA deadlines and breach times",
      "Capture escalation causes and recipients",
      "Track workflow definition version used for each instance",
      "Support complaint handling and legal review"
    ],
    "audit_events": [
      "WorkflowDefinitionCreated",
      "WorkflowDefinitionApproved",
      "WorkflowDefinitionActivated",
      "WorkflowInstanceCreated",
      "WorkflowInstanceTransitioned",
      "WorkflowTaskAssigned",
      "WorkflowTaskCompleted",
      "WorkflowSlaWarningRaised",
      "WorkflowSlaBreached",
      "WorkflowEscalated",
      "WorkflowNotificationSent",
      "WorkflowManualOverrideApplied"
    ],
    "audit_fields": [
      "event_id",
      "workflow_instance_id",
      "workflow_definition_id",
      "state_from",
      "state_to",
      "task_id",
      "trigger_event",
      "actor_type",
      "actor_reference",
      "correlation_id",
      "event_at",
      "event_payload"
    ],
    "controls": [
      "Append-only audit records",
      "Transition history with before/after states",
      "SLA snapshot at each state entry",
      "Escalation chain preservation",
      "Definition checksum hashing",
      "Role-restricted override logging"
    ]
  }
}
```

## 10. Example Workflow Instances
```json
{
  "examples": [
    {
      "workflow_code": "citizenship_registration",
      "scenario": "Citizen submits an application with identity and document review pending.",
      "path": [
        "draft",
        "submitted",
        "identity_verification_pending",
        "document_review_pending",
        "officer_review_pending",
        "approved",
        "issued",
        "completed"
      ],
      "escalation_example": "If document_review_pending exceeds 24 hours, send reminder and notify supervisor."
    },
    {
      "workflow_code": "passport_application",
      "scenario": "Application waits for fee payment and biometric appointment.",
      "path": [
        "draft",
        "submitted",
        "payment_pending",
        "payment_confirmed",
        "biometric_scheduling_pending",
        "biometrics_completed",
        "security_check_pending",
        "officer_review_pending",
        "approved",
        "issued",
        "completed"
      ],
      "escalation_example": "If payment_pending exceeds 12 hours, notify citizen by push and SMS."
    },
    {
      "workflow_code": "driving_license_application",
      "scenario": "Applicant completes testing and awaits approval.",
      "path": [
        "draft",
        "submitted",
        "eligibility_check_pending",
        "medical_clearance_pending",
        "test_scheduling_pending",
        "test_completed",
        "officer_review_pending",
        "approved",
        "issued",
        "completed"
      ],
      "escalation_example": "If test_scheduling_pending exceeds 48 hours, notify the test center and branch manager."
    },
    {
      "workflow_code": "pan_registration",
      "scenario": "PAN registration awaits identity and taxpayer validation.",
      "path": [
        "draft",
        "submitted",
        "identity_check_pending",
        "taxpayer_validation_pending",
        "officer_review_pending",
        "approved",
        "pan_allocated",
        "issued",
        "completed"
      ],
      "escalation_example": "If officer review exceeds 24 hours, create overdue task and notify supervisor."
    }
  ]
}
```

## 11. Failure Modes
```json
{
  "failure_modes": [
    {
      "code": "WF-001",
      "name": "definition_not_found",
      "severity": "high",
      "behavior": "Reject instance creation until a valid workflow definition exists."
    },
    {
      "code": "WF-002",
      "name": "invalid_transition",
      "severity": "high",
      "behavior": "Reject transition and preserve current state."
    },
    {
      "code": "WF-003",
      "name": "guard_failed",
      "severity": "medium",
      "behavior": "Return guard evaluation failure with reason codes."
    },
    {
      "code": "WF-004",
      "name": "sla_policy_missing",
      "severity": "medium",
      "behavior": "Allow workflow to continue but mark SLA as undefined and alert administrators."
    },
    {
      "code": "WF-005",
      "name": "notification_delivery_failed",
      "severity": "medium",
      "behavior": "Queue retry and record the failure for audit."
    },
    {
      "code": "WF-006",
      "name": "audit_publish_failed",
      "severity": "high",
      "behavior": "Fail closed or move to a protected pending state according to policy."
    },
    {
      "code": "WF-007",
      "name": "external_dependency_timeout",
      "severity": "medium",
      "behavior": "Pause the workflow, mark blocked, and trigger escalation after threshold."
    }
  ],
  "resilience_policy": {
    "transient_failures": "Retry external callbacks, notification delivery, and audit publication with bounded backoff.",
    "permanent_failures": "Reject the action and preserve the state history.",
    "idempotency": "Require idempotency keys for state-changing API calls and task completion actions."
  }
}
```

## 12. Implementation Notes
```json
{
  "implementation_notes": [
    "Keep workflow definitions versioned and effective-dated.",
    "Use a generic state machine rather than process-specific hardcoding.",
    "Persist all transitions and SLA snapshots in PostgreSQL.",
    "Use Redis for active timers, deduplication, and short-lived workflow caches.",
    "Emit notifications and audit events asynchronously.",
    "Separate workflow configuration from workflow execution.",
    "Allow process administrators to edit definitions through controlled admin APIs only."
  ]
}
```

## Summary
```json
{
  "summary": "This workflow orchestration engine design provides configurable state machines, versioned workflow definitions, SLA tracking, escalation rules, notifications, and immutable audit trails for Citizenship, Passport, Driving License, and PAN Registration.",
  "recommended_next_step": "Convert the workflow definitions into an implementation backlog and a definition authoring specification."
}
```
