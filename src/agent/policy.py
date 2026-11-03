
from dataclasses import dataclass


class AuthorizationError(PermissionError):
    """The requested operation is not permitted."""


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str


ROLE_PERMISSIONS = {
    "viewer": frozenset({"orders:read", "policies:read"}),
    "analyst": frozenset({"orders:read", "policies:read"}),
    "admin": frozenset({"orders:read", "policies:read"}),
}


def authorize_action(principal: Principal, action: str) -> bool:
    """Authorize a known identity for an explicitly permitted action."""
    if not principal.user_id or not principal.user_id.strip():
        raise AuthorizationError("Missing user identity")

    permissions = ROLE_PERMISSIONS.get(principal.role)

    if permissions is None:
        raise AuthorizationError("Unknown role")

    if action not in permissions:
        raise AuthorizationError(f"Action not permitted: {action}")

    return True
