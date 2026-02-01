from unittest.mock import patch

from django.db import IntegrityError

from saas.domain.models import Domain, DomainManager
from saas.test import SaasTestCase


class TestDomainManager(SaasTestCase):
    def test_not_found(self):
        with patch.object(DomainManager, 'get', side_effect=Domain.DoesNotExist()) as mock_get:
            value = Domain.objects.get_tenant_id('google.com')
            self.assertIsNone(value)

            # trigger get from cache
            value = Domain.objects.get_tenant_id('google.com')
            self.assertIsNone(value)
            self.assertEqual(mock_get.call_count, 1)

    def test_found(self):
        tenant = self.get_tenant()
        Domain.objects.create(tenant=tenant, hostname='example.com')

        with patch.object(DomainManager, 'get', side_effect=Domain.DoesNotExist()) as mock_get:
            value = Domain.objects.get_tenant_id('example.com')
            self.assertEqual(value, tenant.pk)

            value = Domain.objects.get_tenant_id('example.com')
            self.assertEqual(value, tenant.pk)
            mock_get.assert_not_called()

    def test_purge_tenant_events(self):
        from saas.domain.providers import NullProvider

        tenant = self.get_tenant()
        Domain.objects.create(tenant=tenant, hostname='example.com', provider='null')

        with patch.object(NullProvider, 'remove_domain') as remove_domain:
            tenant.delete()
            remove_domain.assert_called_once()

    def test_disable_domain(self):
        tenant = self.get_tenant()
        domain = Domain.objects.create(tenant=tenant, hostname='example.com')
        domain.disable()
        self.assertFalse(domain.verified)

    def test_domain_base_url(self):
        tenant = self.get_tenant()
        domain = Domain.objects.create(tenant=tenant, hostname='example.com')
        domain.ssl = True
        self.assertEqual(domain.base_url, 'https://example.com')

        domain.ssl = False
        self.assertEqual(domain.base_url, 'http://example.com')

    def test_domain_str(self):
        tenant = self.get_tenant()
        domain = Domain.objects.create(tenant=tenant, hostname='example.com')
        self.assertEqual(str(domain), 'example.com')

    def test_create_multiple_primary_domains(self):
        tenant = self.get_tenant()
        Domain.objects.create(tenant=tenant, hostname='example1.com', primary=True)

        for i in range(10):
            # ok with multiple non-primary domains
            Domain.objects.create(tenant=tenant, hostname=f'not-primary-{i}.com', primary=False)

        with self.assertRaises(IntegrityError):
            Domain.objects.create(tenant=tenant, hostname='example2.com', primary=True)
