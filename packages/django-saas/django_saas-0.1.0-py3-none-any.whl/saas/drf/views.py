import typing as t

from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings

from .errors import BadRequest
from .filters import TenantIdFilter
from .permissions import HasResourcePermission, IsTenantActiveOrReadOnly
from .types import SaasRequest

__all__ = [
    'Endpoint',
    'AuthenticatedEndpoint',
    'TenantEndpoint',
]


class Endpoint(GenericAPIView):
    request: SaasRequest
    permission_classes = [HasResourcePermission] + api_settings.DEFAULT_PERMISSION_CLASSES
    required_permission: t.Optional[str] = None

    @staticmethod
    def get_object_or_404(queryset: QuerySet, **kwargs):
        return get_object_or_404(queryset, **kwargs)

    def prevent_duplicate_request(self, suffix: t.Union[str, int], timeout: int = 120, force: bool = False):
        if getattr(settings, 'TESTING', False) and not force:
            return

        path = self.request.path
        key = f'request:{path}:{suffix}'
        if cache.get(key):
            raise BadRequest('Duplicate request')
        cache.set(key, 1, timeout=timeout)


class AuthenticatedEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, HasResourcePermission] + api_settings.DEFAULT_PERMISSION_CLASSES


class TenantEndpoint(Endpoint):
    permission_classes = [
        IsAuthenticated,
        IsTenantActiveOrReadOnly,
        HasResourcePermission,
    ] + api_settings.DEFAULT_PERMISSION_CLASSES
    filter_backends = [TenantIdFilter]

    def get_tenant_id(self):
        tenant_id = getattr(self.request, 'tenant_id', None)
        if not tenant_id:
            raise BadRequest('Missing Tenant ID')
        return tenant_id
