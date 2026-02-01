from django.http import HttpResponse
from django.test import RequestFactory

from saas.domain.middleware import DomainTenantIdMiddleware
from saas.domain.models import Domain
from saas.test import SaasTestCase


class TestDomainTenantIdMiddleware(SaasTestCase):
    middleware_cls = DomainTenantIdMiddleware

    @staticmethod
    def create_request(host):
        meta = {'HTTP_HOST': host}
        factory = RequestFactory(**meta)
        return factory.get('/')

    def setUp(self):
        self.middleware = self.middleware_cls(lambda req: HttpResponse())

    def test_match_tenant_id(self):
        Domain.objects.create(hostname='test.us.localhost', tenant=self.tenant)
        request = self.create_request('test.us.localhost')
        self.middleware(request)
        self.assertEqual(request.tenant_id, self.tenant.pk)

    def test_none_tenant_id(self):
        request = self.create_request('none.us.localhost')
        self.middleware(request)
        self.assertEqual(request.tenant_id, None)

    def test_cached_tenant_id(self):
        request = self.create_request('test.us.localhost')
        request._cached_tenant_id = self.tenant.pk
        self.middleware(request)
        self.assertEqual(request.tenant_id, self.tenant.pk)
