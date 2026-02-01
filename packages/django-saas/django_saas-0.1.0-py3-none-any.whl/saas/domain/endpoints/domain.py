from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response

from saas.drf.decorators import resource_permission
from saas.drf.views import TenantEndpoint

from ..models import Domain
from ..providers import get_domain_provider
from ..serializers import DomainSerializer, DomainSetPrimarySerializer
from ..settings import domain_settings


class DomainListEndpoint(ListModelMixin, TenantEndpoint):
    serializer_class = DomainSerializer
    pagination_class = None
    queryset = Domain.objects.all()

    @resource_permission('security.domain.view')
    def get(self, request: Request, *args, **kwargs):
        """List all domains for the tenant."""
        return self.list(request, *args, **kwargs)

    @resource_permission('security.domain.create')
    def post(self, request: Request, *args, **kwargs):
        """Add a new domain to the tenant with a selected provider."""
        tenant_id = self.get_tenant_id()
        if self.filter_queryset(self.get_queryset()).count() >= domain_settings.TENANT_MAX_DOMAINS:
            raise PermissionDenied(detail='Maximum number of domains reached')

        serializer: DomainSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.save(tenant_id=tenant_id)
        provider = get_domain_provider(domain.provider)
        if provider:
            provider.add_domain(domain)
            serializer = self.get_serializer(domain)
        return Response(serializer.data, status=201)


class DomainItemEndpoint(TenantEndpoint):
    serializer_class = DomainSerializer
    queryset = Domain.objects.all()
    lookup_field = 'hostname'

    @resource_permission('security.domain.view')
    def get(self, request: Request, *args, **kwargs):
        """Show the details of a domain."""
        domain = self.get_object()
        serializer: DomainSerializer = self.get_serializer(domain)
        return Response(serializer.data)

    @resource_permission('security.domain.manage')
    def post(self, request: Request, *args, **kwargs):
        """Re-add a domain to the provider."""
        domain = self.get_object()
        provider = get_domain_provider(domain.provider)
        if provider:
            provider.add_domain(domain)
        serializer: DomainSerializer = self.get_serializer(domain)
        return Response(serializer.data)

    @resource_permission('security.domain.manage')
    def patch(self, request: Request, *args, **kwargs):
        """Select this domain as the primary one for the tenant."""
        domain = self.get_object()
        serializer = DomainSetPrimarySerializer(domain, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(domain)
        return Response(serializer.data)

    @resource_permission('security.domain.delete')
    def delete(self, request: Request, *args, **kwargs):
        """Remove a domain from the provider, and delete the record."""
        domain = self.get_object()
        provider = get_domain_provider(domain.provider)
        if provider:
            provider.remove_domain(domain)
        domain.delete()
        return Response(status=204)


class DomainVerifyEndpoint(TenantEndpoint):
    serializer_class = DomainSerializer
    queryset = Domain.objects.all()
    lookup_field = 'hostname'

    @resource_permission('security.domain.verify')
    def post(self, request: Request, *args, **kwargs):
        """Verify a domain, if verified by the provider, mark it as active."""
        domain = self.get_object()
        provider = get_domain_provider(domain.provider)
        if provider:
            provider.verify_domain(domain)
        serializer: DomainSerializer = self.get_serializer(domain)
        return Response(serializer.data)
