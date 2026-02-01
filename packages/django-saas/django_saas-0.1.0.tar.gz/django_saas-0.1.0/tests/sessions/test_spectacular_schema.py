from saas.test import SaasTestCase


class TestOpenAPISchema(SaasTestCase):
    def test_fetch_openapi_schema(self):
        resp = self.client.get('/schema/openapi')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Retrieve a user session', resp.text)
