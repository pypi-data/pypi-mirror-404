from django.http.request import split_domain_port

from saas.models import get_tenant_model

from .models import Domain

TenantModel = get_tenant_model()


__all__ = [
    'DomainTenantIdMiddleware',
]


class DomainTenantIdMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    @staticmethod
    def get_tenant_id(request):
        tenant_id = getattr(request, '_cached_tenant_id', None)
        if tenant_id:
            return tenant_id

        host = request.get_host()
        hostname = split_domain_port(host)[0]
        return Domain.objects.get_tenant_id(hostname)

    def __call__(self, request):
        request.tenant_id = self.get_tenant_id(request)
        return self.get_response(request)
