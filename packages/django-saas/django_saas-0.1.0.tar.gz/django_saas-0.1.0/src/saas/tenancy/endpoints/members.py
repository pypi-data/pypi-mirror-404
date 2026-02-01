from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request

from saas.drf.decorators import resource_permission
from saas.drf.filters import IncludeFilter, TenantIdFilter
from saas.drf.views import TenantEndpoint

from ..models import Member
from ..serializers.member import (
    MemberSerializer,
    MemberUpdateSerializer,
)

__all__ = [
    'MemberListEndpoint',
    'MemberItemEndpoint',
]


class MemberListEndpoint(ListModelMixin, TenantEndpoint):
    serializer_class = MemberSerializer
    filter_backends = [TenantIdFilter, IncludeFilter]
    queryset = Member.objects.all().select_related('user').prefetch_related('groups')

    @resource_permission('iam.member.view')
    def get(self, request: Request, *args, **kwargs):
        """List all members in the tenant."""
        return self.list(request, *args, **kwargs)


class MemberItemEndpoint(UpdateModelMixin, DestroyModelMixin, TenantEndpoint):
    serializer_class = MemberUpdateSerializer
    queryset = Member.objects.all()

    @resource_permission('iam.member.update')
    def patch(self, request: Request, *args, **kwargs):
        """Update a member's permissions and groups."""
        return self.partial_update(request, *args, **kwargs)

    @resource_permission('iam.member.delete')
    def delete(self, request: Request, *args, **kwargs):
        """Remove a member from the tenant."""
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance: Member):
        if instance.user_id == self.request.tenant.owner_id:
            raise PermissionDenied('Cannot remove the owner from the tenant.')
        instance.delete()
