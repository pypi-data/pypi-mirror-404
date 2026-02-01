from unittest.mock import Mock, patch

from rest_framework.views import APIView

from saas.drf.spectacular import AutoSchema
from saas.test import SaasTestCase


class TestCurrentTenantAPI(SaasTestCase):
    def test_fetch_openapi(self):
        resp = self.client.get('/schema/openapi')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sign Up with Invitation', resp.text)


class TestAutoSchema(SaasTestCase):
    def test_get_security_no_perm(self):
        view = APIView()
        view.request = Mock()
        schema = AutoSchema()
        schema.view = view
        schema.method = 'GET'

        self.assertEqual(schema.get_security(), [])

    def test_get_security_with_perm_no_scopes(self):
        view = APIView()
        view.required_permission = 'test.perm'
        schema = AutoSchema()
        schema.view = view
        schema.method = 'GET'

        with patch('saas.registry.perm_registry.get_scopes_for_permission', return_value=[]):
            self.assertEqual(schema.get_security(), [])

    def test_get_security_with_perm_and_scopes(self):
        view = APIView()
        view.required_permission = 'test.perm'
        schema = AutoSchema()
        schema.view = view
        schema.method = 'GET'

        with patch('saas.registry.perm_registry.get_scopes_for_permission', return_value=['scope1']):
            self.assertEqual(schema.get_security(), [{'oauth2': ['scope1']}])

    def test_get_filter_backends(self):
        view = APIView()
        view.filter_backends = ['backend1']
        schema = AutoSchema()
        schema.view = view
        self.assertEqual(schema.get_filter_backends(), ['backend1'])

    def test_get_description_with_perm(self):
        view = APIView()
        view.required_permission = 'test.perm'
        schema = AutoSchema()
        schema.view = view
        schema.method = 'GET'

        with patch('drf_spectacular.openapi.AutoSchema.get_description', return_value='desc'):
            self.assertIn('Permissions', schema.get_description())
            self.assertIn('test.perm', schema.get_description())
