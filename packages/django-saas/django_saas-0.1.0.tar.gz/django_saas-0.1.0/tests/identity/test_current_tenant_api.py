from tests.client import FixturesTestCase


class TestCurrentTenantAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID

    def test_fetch_demo_tenant(self):
        self.force_login()
        resp = self.client.get('/m/tenants/current/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['slug'], self.tenant.slug)
