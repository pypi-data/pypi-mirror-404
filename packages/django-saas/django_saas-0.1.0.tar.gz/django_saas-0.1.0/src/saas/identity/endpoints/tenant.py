from django.utils.translation import gettext_lazy as _
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.throttling import ScopedRateThrottle

from saas.drf.decorators import resource_permission
from saas.drf.permissions import IsTenantOwner
from saas.drf.views import AuthenticatedEndpoint, TenantEndpoint
from saas.models import get_tenant_model
from saas.settings import saas_settings
from saas.signals import confirm_destroy_tenant, mail_queued

from ..serializers.email_code import EmailCode
from ..serializers.tenant import (
    TenantDestroySerializer,
    TenantSerializer,
    TenantTransferSerializer,
    TenantUpdateSerializer,
)

__all__ = [
    'SelectedTenantEndpoint',
    'TenantListEndpoint',
    'TenantItemEndpoint',
    'TenantTransferEndpoint',
    'TenantDestroyEndpoint',
]


class SelectedTenantEndpoint(RetrieveModelMixin, TenantEndpoint):
    serializer_class = TenantSerializer
    queryset = get_tenant_model().objects.all()
    tenant_id_field = 'pk'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = self.get_object_or_404(queryset)
        self.check_object_permissions(self.request, obj)
        return obj

    @resource_permission('org.info.view')
    def get(self, request: Request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class TenantListEndpoint(CreateModelMixin, ListModelMixin, AuthenticatedEndpoint):
    serializer_class = TenantSerializer
    queryset = get_tenant_model().objects.all()
    pagination_class = None
    permission_classes = [IsAuthenticated] + api_settings.DEFAULT_PERMISSION_CLASSES
    throttle_classes = [ScopedRateThrottle]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    @property
    def throttle_scope(self):
        # add rate limit for tenant creation
        if self.request.method == 'POST':
            return 'user'
        return None

    @resource_permission('user.org.view')
    def get(self, request: Request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @resource_permission('user.org.create')
    def post(self, request: Request, *args, **kwargs):
        if saas_settings.MAX_USER_TENANTS and self.get_queryset().count() >= saas_settings.MAX_USER_TENANTS:
            return Response({'detail': _('Maximum number of tenants reached.')}, status=403)
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TenantItemEndpoint(RetrieveModelMixin, UpdateModelMixin, TenantEndpoint):
    serializer_class = TenantUpdateSerializer
    queryset = get_tenant_model().objects.all()
    filter_backends = []
    tenant_id_field = 'pk'

    @resource_permission('org.info.view')
    def get(self, request: Request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @resource_permission('org.info.manage')
    def patch(self, request: Request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class TenantRequestConfirmEndpoint(TenantEndpoint):
    email_template_id = ''
    email_subject = ''
    serializer_class = None

    queryset = get_tenant_model().objects.all()
    permission_classes = [IsTenantOwner]
    filter_backends = []
    tenant_id_field = 'pk'

    def send_request_email(self, request, obj: EmailCode):
        tenant = self.get_object()
        mail_queued.send(
            sender=self.__class__,
            template_id=self.email_template_id,
            subject=str(self.email_subject),
            recipients=[obj.recipient()],
            context={'code': obj.code, 'tenant': tenant},
            request=request,
        )

    def perform_confirm(self, tenant):
        pass

    def post(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        if request.data['action'] == 'request':
            self.send_request_email(request, obj)
        elif request.data['action'] == 'confirm':
            self.perform_confirm(request.tenant)
        return Response(status=204)


class TenantTransferEndpoint(TenantRequestConfirmEndpoint):
    email_template_id = 'transfer_tenant'
    email_subject = _('Tenant Transfer Request')
    serializer_class = TenantTransferSerializer


class TenantDestroyEndpoint(TenantRequestConfirmEndpoint):
    email_template_id = 'destroy_tenant'
    email_subject = _('Tenant Destroy Request')
    serializer_class = TenantDestroySerializer

    def perform_confirm(self, tenant):
        confirm_destroy_tenant.send(
            sender=self.__class__,
            tenant=tenant,
            request=self.request,
        )
