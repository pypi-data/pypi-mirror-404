from dataclasses import dataclass
from enum import IntEnum


class Severity(IntEnum):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


@dataclass
class Permission:
    key: str
    label: str
    description: str
    module: str
    severity: int = Severity.LOW


@dataclass
class Role:
    code: str
    name: str
    description: str
    permissions: set[str]


@dataclass
class Scope:
    key: str
    label: str
    permissions: set[str]  # Internal permission patterns
    description: str = ''
    is_oidc: bool = False  # Flag for OIDC standard scopes
