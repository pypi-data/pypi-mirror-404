import os

os.environ['GEOIP_PATH'] = '/tmp'

from unittest.mock import patch

# Mock GeoIP2 before importing GeoIP2Backend
with patch('django.contrib.gis.geoip2.GeoIP2'):
    from saas.sessions.location.geoip2 import GeoIP2Backend

from django.test import RequestFactory, SimpleTestCase

from saas.sessions.location.base import BaseBackend
from saas.sessions.location.cloudflare import CloudflareBackend


class MockBackend(BaseBackend):
    def resolve_ip(self, request):
        return '1.2.3.4'

    def resolve_location(self, request):
        return {'country': 'US'}


class TestLocationBackends(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_base_backend_without_ip(self):
        backend = MockBackend()
        request = self.factory.get('/')
        data = backend.resolve(request)
        self.assertEqual(data, {'country': 'US'})

    def test_base_backend_with_ip(self):
        backend = MockBackend(record_ip=True)
        request = self.factory.get('/')
        data = backend.resolve(request)
        self.assertEqual(data, {'country': 'US', 'ip': '1.2.3.4'})

    def test_cloudflare_backend(self):
        backend = CloudflareBackend()
        request = self.factory.get('/', HTTP_CF_IPCOUNTRY='US', HTTP_CF_REGION='California', HTTP_CF_REGION_CODE='CA')
        data = backend.resolve_location(request)
        self.assertEqual(data['country'], 'US')
        self.assertEqual(data['region'], 'California')
        self.assertEqual(data['region_code'], 'CA')

        request = self.factory.get('/', HTTP_CF_CONNECTING_IP='1.2.3.4')
        self.assertEqual(backend.resolve_ip(request), '1.2.3.4')

    @patch('saas.sessions.location.geoip2._geo')
    def test_geoip2_backend(self, mock_geo):
        mock_geo.city.return_value = {
            'country_code': 'US',
            'region_name': 'California',
            'region_code': 'CA',
        }
        backend = GeoIP2Backend()
        request = self.factory.get('/', REMOTE_ADDR='1.2.3.4')
        self.assertEqual(backend.resolve_ip(request), '1.2.3.4')
        data = backend.resolve_location(request)
        self.assertEqual(data['ip'], '1.2.3.4')
        self.assertEqual(data['country'], 'US')

        # Test IP is None
        with patch('saas.sessions.location.geoip2.get_client_ip', return_value=None):
            data = backend.resolve_location(request)
            self.assertEqual(data, {})

        # Test GeoIP2Exception
        from django.contrib.gis.geoip2 import GeoIP2Exception

        mock_geo.city.side_effect = GeoIP2Exception()
        data = backend.resolve_location(request)
        self.assertEqual(data, {})
