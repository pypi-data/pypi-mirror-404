from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command

from saas.domain.models import Domain
from saas.domain.providers.base import BaseProvider
from saas.test import SaasTestCase


class TestVerifyDomainsCommand(SaasTestCase):
    def create_domain(self, hostname, provider='mock_provider'):
        return Domain.objects.create(
            tenant_id=self.tenant_id,
            hostname=hostname,
            provider=provider,
        )

    def test_verify_domains_no_pending(self):
        out = StringIO()
        call_command('verify_domains', stdout=out)
        self.assertIn('No pending domains to verify.', out.getvalue())

    @patch('saas.domain.management.commands.verify_domains.get_domain_provider')
    def test_verify_domains_success(self, mock_get_provider):
        domain = self.create_domain('pending.example.com')
        provider_instance = MagicMock(spec=BaseProvider)

        def verify_side_effect(d):
            d.verified = True
            d.save()
            return d

        provider_instance.verify_domain.side_effect = verify_side_effect
        mock_get_provider.return_value = provider_instance

        out = StringIO()
        call_command('verify_domains', stdout=out)

        self.assertIn('Successfully verified pending.example.com', out.getvalue())
        domain.refresh_from_db()
        self.assertTrue(domain.verified)

    @patch('saas.domain.management.commands.verify_domains.get_domain_provider')
    def test_verify_domains_still_pending(self, mock_get_provider):
        domain = self.create_domain('still-pending.example.com')

        provider_instance = MagicMock(spec=BaseProvider)
        mock_get_provider.return_value = provider_instance

        out = StringIO()
        call_command('verify_domains', stdout=out)

        self.assertIn('checked still-pending.example.com: Still pending', out.getvalue())
        domain.refresh_from_db()
        self.assertFalse(domain.verified)

    @patch('saas.domain.management.commands.verify_domains.get_domain_provider')
    def test_verify_domains_error(self, mock_get_provider):
        self.create_domain('error.example.com')

        provider_instance = MagicMock(spec=BaseProvider)
        provider_instance.verify_domain.side_effect = Exception('API Error')
        mock_get_provider.return_value = provider_instance

        out = StringIO()
        call_command('verify_domains', stdout=out)

        self.assertIn('Error verifying error.example.com: API Error', out.getvalue())
