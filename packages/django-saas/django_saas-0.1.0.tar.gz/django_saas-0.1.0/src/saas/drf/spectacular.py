from typing import Any, List

from drf_spectacular.openapi import AutoSchema as _AutoSchema

from saas.registry import perm_registry
from saas.registry.checker import get_view_permission

__all__ = ['AutoSchema']


class AutoSchema(_AutoSchema):
    def get_security(self):
        required_perm = get_view_permission(self.view, self.method)
        if not required_perm:
            return []

        required_scopes = perm_registry.get_scopes_for_permission(required_perm)

        if required_scopes:
            return [
                {'oauth2': required_scopes},
            ]

        return []

    def get_filter_backends(self) -> List[Any]:
        return getattr(self.view, 'filter_backends', [])

    def get_description(self) -> str:
        description = super().get_description()
        required_perm = get_view_permission(self.view, self.method)
        if required_perm:
            description = f'**Permissions**: {required_perm}\n\n{description}'
        return description
