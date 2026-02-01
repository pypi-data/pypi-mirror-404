from dataclasses import asdict

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from saas.registry import perm_registry

__all__ = ['PermissionListEndpoint', 'RoleListEndpoint', 'ScopeListEndpoint']


class PermissionListEndpoint(APIView):
    permission_classes = []
    pagination_class = None

    def get(self, request: Request, *args, **kwargs):
        """Show all supported permissions."""
        data = [asdict(p) for p in perm_registry.get_permission_list()]
        return Response(data)


class RoleListEndpoint(APIView):
    permission_classes = []
    pagination_class = None

    def get(self, request: Request, *args, **kwargs):
        """Show all supported Roles."""
        data = [asdict(p) for p in perm_registry.get_role_list()]
        return Response(data)


class ScopeListEndpoint(APIView):
    permission_classes = []
    pagination_class = None

    def get(self, request: Request, *args, **kwargs):
        """Show all supported Roles."""
        inclusions = perm_registry.get_scope_inclusion_map()
        data = [self.asdict_scope(p, inclusions) for p in perm_registry.get_scope_list()]
        return Response(data)

    def asdict_scope(self, p, inclusions):
        rv = asdict(p)
        rv['includes'] = inclusions[p.key]
        return rv
