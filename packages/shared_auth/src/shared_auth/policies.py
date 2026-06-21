from __future__ import annotations

from collections.abc import Iterable

from .models import Permission, Role

PERMISSION_MATRIX: dict[Role, tuple[Permission, ...]] = {
    Role.CITIZEN: (
        Permission.VIEW_OWN_PROFILE,
        Permission.VIEW_OWN_APPLICATIONS,
        Permission.SUBMIT_APPLICATION,
        Permission.UPLOAD_DOCUMENTS,
        Permission.VIEW_OWN_NOTIFICATIONS,
        Permission.VIEW_OWN_TAX_ESTIMATE,
    ),
    Role.CLERK: (
        Permission.VIEW_ASSIGNED_APPLICATIONS,
        Permission.VERIFY_CITIZEN,
        Permission.VERIFY_OCR,
        Permission.REVIEW_APPLICATION,
        Permission.VIEW_AUDIT_LOGS,
    ),
    Role.REVIEWER: (
        Permission.VIEW_ASSIGNED_APPLICATIONS,
        Permission.VERIFY_CITIZEN,
        Permission.VERIFY_OCR,
        Permission.REVIEW_APPLICATION,
        Permission.MANAGE_WORKFLOW,
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_ANALYTICS,
    ),
    Role.MANAGER: (
        Permission.VIEW_ASSIGNED_APPLICATIONS,
        Permission.VERIFY_CITIZEN,
        Permission.VERIFY_OCR,
        Permission.REVIEW_APPLICATION,
        Permission.MANAGE_WORKFLOW,
        Permission.MANUAL_OVERRIDE,
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_ANALYTICS,
    ),
    Role.ADMINISTRATOR: (
        Permission.VIEW_ASSIGNED_APPLICATIONS,
        Permission.VERIFY_CITIZEN,
        Permission.VERIFY_OCR,
        Permission.REVIEW_APPLICATION,
        Permission.MANAGE_WORKFLOW,
        Permission.MANUAL_OVERRIDE,
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
    ),
    Role.SUPER_ADMINISTRATOR: tuple(Permission),
}


def permissions_for_role(role: Role) -> tuple[Permission, ...]:
    return PERMISSION_MATRIX.get(role, ())


def permissions_for_roles(roles: Iterable[Role]) -> set[Permission]:
    granted_permissions: set[Permission] = set()
    for role in roles:
        granted_permissions.update(permissions_for_role(role))
    return granted_permissions