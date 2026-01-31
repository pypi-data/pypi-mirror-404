"""
Role Based Access Control (Phase 9)
"""
from enum import Enum


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

def check_role_access(user_roles: list[UserRole], required_role: UserRole | None) -> bool:
    """
    Check if user has required role access.
    Heuristic: ADMIN > USER > VIEWER
    """
    if required_role is None:
        return True

    if UserRole.ADMIN in user_roles:
        return True

    if UserRole.USER in user_roles:
        return required_role != UserRole.ADMIN

    if UserRole.VIEWER in user_roles:
        return required_role == UserRole.VIEWER

    return False
