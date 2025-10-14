from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SyncedRoleDefinition:
    """Represents a synced role configuration."""
    days_required: int
    role_id: int
    level: Optional[int] = None
    extra_roles: Optional[list[int]] = None
    days_override: Optional[int] = None
