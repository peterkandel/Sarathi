from fastapi import Depends, FastAPI, Request

from shared_auth import (
    AuditLoggingMiddleware,
    AuthSettings,
    AuditLogger,
    PrincipalMiddleware,
    Permission,
    Role,
    authorize_resource_access,
    build_audit_event,
    get_principal,
    require_permission,
    require_role,
)

app = FastAPI(title="SARATHI API Gateway", version="0.1.0")
app.add_middleware(PrincipalMiddleware, settings=AuthSettings())
app.add_middleware(AuditLoggingMiddleware)

audit_logger = AuditLogger()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "api_gateway"}


@app.get("/v1")
def root() -> dict[str, str]:
    return {"service": "api_gateway", "version": "v1"}


@app.get("/v1/citizen/me", dependencies=[Depends(require_permission(Permission.VIEW_OWN_PROFILE))])
def citizen_me(request: Request) -> dict[str, object]:
    principal = get_principal(request)
    return {
        "subject": principal.subject,
        "roles": [role.value for role in principal.roles],
        "agency_id": principal.agency_id,
        "permissions": [permission.value for permission in principal.permissions],
    }


@app.get("/v1/citizen/profiles/{citizen_id}")
def citizen_profile(citizen_id: str, request: Request) -> dict[str, object]:
    principal = authorize_resource_access(request, resource_owner_id=citizen_id)
    return {
        "citizen_id": citizen_id,
        "requested_by": principal.subject,
        "access_mode": "owner-or-privileged",
    }


@app.post(
    "/v1/citizen/applications",
    dependencies=[Depends(require_permission(Permission.SUBMIT_APPLICATION))],
)
def submit_application(request: Request) -> dict[str, object]:
    principal = get_principal(request)
    audit_logger.log(
        build_audit_event(
            event_type="ApplicationSubmitted",
            action="submit_application",
            outcome="accepted",
            principal=principal,
            resource_type="application",
            details={"surface": "citizen"},
        )
    )
    return {"status": "submitted", "submitted_by": principal.subject}


@app.get(
    "/v1/admin/work-queue",
    dependencies=[Depends(require_role(Role.CLERK, Role.REVIEWER, Role.MANAGER, Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR))],
)
def work_queue(request: Request) -> dict[str, object]:
    principal = get_principal(request)
    return {"queue": [], "requested_by": principal.subject}


@app.post(
    "/v1/admin/applications/{application_id}/approve",
    dependencies=[Depends(require_role(Role.REVIEWER, Role.MANAGER, Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR))],
)
def approve_application(application_id: str, request: Request) -> dict[str, object]:
    principal = get_principal(request)
    audit_logger.log(
        build_audit_event(
            event_type="ApplicationApproved",
            action="approve_application",
            outcome="approved",
            principal=principal,
            resource_type="application",
            resource_id=application_id,
            details={"surface": "admin"},
        )
    )
    return {"application_id": application_id, "status": "approved", "approved_by": principal.subject}


@app.get(
    "/v1/admin/audit/events",
    dependencies=[Depends(require_role(Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR))],
)
def audit_events(request: Request) -> dict[str, object]:
    principal = get_principal(request)
    return {"events": [], "requested_by": principal.subject}


@app.get(
    "/v1/admin/users",
    dependencies=[Depends(require_role(Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR))],
)
def admin_users(request: Request) -> dict[str, object]:
    principal = get_principal(request)
    return {"users": [], "requested_by": principal.subject}
