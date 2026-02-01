from __future__ import annotations

from collections import OrderedDict

from .base import Permission, Role, Scope, Severity
from .checker import has_permission


class PermissionRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._permissions: OrderedDict[str, Permission] = OrderedDict()
            cls._instance._roles: OrderedDict[str, Role] = OrderedDict()
            cls._instance._scopes: OrderedDict[str, Scope] = OrderedDict()
        return cls._instance

    def register_scope(
        self,
        key: str,
        label: str,
        permissions: list[str],
        description: str = '',
        is_oidc: bool = False,
    ):
        if key not in self._scopes:
            scope = Scope(key, label, set(permissions), description, is_oidc)
            self._scopes[key] = scope

    def register_role(self, code: str, name: str, description: str = ''):
        """Define a system role structure."""
        if code not in self._roles:
            role = Role(code, name=name, description=description, permissions=set())
            self._roles[code] = role

    def register_permission(
        self,
        key: str,
        label: str,
        module: str,
        description: str = '',
        severity: int | None = None,
    ):
        """
        Register a permission and optionally assign it to default roles.
        """
        if key in self._permissions:
            raise ValueError(f'Permission {key} already registered')

        if severity is None:
            if key.endswith('.view'):
                severity = Severity.LOW
            elif key.endswith('.create'):
                severity = Severity.HIGH
            elif key.endswith('.delete'):
                severity = Severity.CRITICAL
            else:
                severity = Severity.NORMAL
        perm = Permission(
            key=key,
            label=label,
            description=description,
            module=module,
            severity=severity,
        )
        self._permissions[key] = perm

    def assign_to_role(self, role_code: str, permission: str):
        """Manually assign a pattern to a role."""
        if role_code not in self._roles:
            self.register_role(role_code, role_code.capitalize())

        role = self._roles[role_code]
        role.permissions.add(permission)

    def assign_to_scopes(self, scope_key: str, permissions: list[str]):
        if scope_key not in self._scopes:
            raise ValueError(f'Scope {scope_key} not registered')
        self._scopes[scope_key].permissions.update(permissions)

    def get_permission_keys(self):
        return self._permissions.keys()

    def get_permission_list(self):
        return self._permissions.values()

    def get_role(self, code: str):
        return self._roles.get(code)

    def get_role_codes(self):
        return list(self._roles.keys())

    def get_role_list(self):
        return self._roles.values()

    def get_scope_keys(self):
        return self._scopes.keys()

    def get_scope_list(self):
        return self._scopes.values()

    def get_permissions_for_scopes(self, scopes):
        perms: set[str] = set()
        for key in scopes:
            if key in self._scopes:
                obj = self._scopes[key]
                perms.update(obj.permissions)
        return perms

    def get_scopes_for_permission(self, perm_key: str) -> list[str]:
        matching_scopes = []
        for scope_key, scope_obj in self._scopes.items():
            # If the scope's patterns match the required permission
            if has_permission(perm_key, scope_obj.permissions):
                matching_scopes.append(scope_key)
        return matching_scopes

    def get_scope_inclusion_map(self):
        inclusion_map = {}
        all_scopes = self._scopes.values()

        scope_expanded = {}
        for scope in all_scopes:
            scope_expanded[scope.key] = {
                p.key for p in self._permissions.values() if has_permission(p.key, scope.permissions)
            }

        for s_a in all_scopes:
            inclusion_map[s_a.key] = []
            for s_b in all_scopes:
                if s_a.key == s_b.key:
                    continue

                perms_a = scope_expanded[s_a.key]
                perms_b = scope_expanded[s_b.key]
                if not perms_a or not perms_b:
                    continue

                if perms_b.issubset(perms_a):
                    inclusion_map[s_a.key].append(s_b.key)

        return inclusion_map


perm_registry = PermissionRegistry()
