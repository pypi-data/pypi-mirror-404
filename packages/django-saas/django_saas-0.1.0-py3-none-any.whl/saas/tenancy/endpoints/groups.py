from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request

from saas.drf.decorators import resource_permission
from saas.drf.views import TenantEndpoint

from ..models import Group
from ..serializers.group import GroupSerializer

__all__ = ['GroupListEndpoint', 'GroupItemEndpoint']


class GroupListEndpoint(ListModelMixin, CreateModelMixin, TenantEndpoint):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    pagination_class = None

    @resource_permission('iam.group.view')
    def get(self, request: Request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @resource_permission('iam.group.manage')
    def post(self, request: Request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        tenant_id = self.get_tenant_id()
        serializer.save(tenant_id=tenant_id)


class GroupItemEndpoint(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, TenantEndpoint):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    required_permission = 'iam.group.manage'

    @resource_permission('iam.group.view')
    def get(self, request: Request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: Request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request: Request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs):
        """Remove a permission group."""
        return self.destroy(request, *args, **kwargs)
