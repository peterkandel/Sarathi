from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    CITIZEN = "Citizen"
    CLERK = "Clerk"
    REVIEWER = "Reviewer"
    MANAGER = "Manager"
    ADMINISTRATOR = "Administrator"
    SUPER_ADMINISTRATOR = "Super Administrator"


class Permission(str, Enum):
    VIEW_OWN_PROFILE = "view_own_profile"
    VIEW_OWN_APPLICATIONS = "view_own_applications"
    SUBMIT_APPLICATION = "submit_application"
    UPLOAD_DOCUMENTS = "upload_documents"
    VIEW_OWN_NOTIFICATIONS = "view_own_notifications"
    VIEW_OWN_TAX_ESTIMATE = "view_own_tax_estimate"
    VIEW_ASSIGNED_APPLICATIONS = "view_assigned_applications"
    VERIFY_CITIZEN = "verify_citizen"
    VERIFY_OCR = "verify_ocr"
    REVIEW_APPLICATION = "review_application"
    MANAGE_WORKFLOW = "manage_workflow"
    MANUAL_OVERRIDE = "manual_override"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SYSTEM_POLICY = "manage_system_policy"


class Principal(BaseModel):
    subject: str
    roles: list[Role] = Field(default_factory=list)
    agency_id: str | None = None
    permissions: list[Permission] = Field(default_factory=list)
    is_authenticated: bool = True
