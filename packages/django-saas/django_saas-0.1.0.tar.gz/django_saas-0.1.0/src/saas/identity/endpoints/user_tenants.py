from django.db.models import Count, OuterRef, Subquery
from django.utils.translation import gettext as _
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
)
from rest_framework.request import Request

from saas.drf.decorators import resource_permission
from saas.drf.filters import CurrentUserFilter, IncludeFilter
from saas.drf.views import AuthenticatedEndpoint

from ..models import Membership
from ..serializers.user_tenant import UserTenantSerializer

__all__ = [
    'UserTenantListEndpoint',
    'UserTenantItemEndpoint',
]


class UserTenantListEndpoint(ListModelMixin, AuthenticatedEndpoint):
    serializer_class = UserTenantSerializer
    queryset = Membership.objects.select_related('tenant').all()
    pagination_class = None

    filter_backends = [CurrentUserFilter, IncludeFilter]
    include_annotate_fields = ['member_count']

    def annotate_queryset(self, queryset, terms):
        if 'member_count' in terms:
            member_count_subquery = (
                Membership.objects.filter(tenant=OuterRef('tenant'))
                .values('tenant')
                .annotate(count=Count('id'))
                .values('count')
            )
            queryset = queryset.annotate(member_count=Subquery(member_count_subquery))
        return queryset

    @resource_permission('user.org.view')
    def get(self, request: Request, *args, **kwargs):
        """List all the current user's tenants."""
        return self.list(request, *args, **kwargs)


class UserTenantItemEndpoint(DestroyModelMixin, AuthenticatedEndpoint):
    queryset = Membership.objects.all()
    filter_backends = [CurrentUserFilter]
    lookup_field = 'tenant_id'

    @resource_permission('user.org.leave')
    def delete(self, request: Request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance: Membership):
        if instance.tenant.owner_id == self.request.user.pk:
            raise PermissionDenied(_('Cannot leave your own tenant.'))
        instance.delete()
