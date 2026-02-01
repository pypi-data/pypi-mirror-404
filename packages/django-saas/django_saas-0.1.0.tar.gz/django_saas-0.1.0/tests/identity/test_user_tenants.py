from saas.identity.models import Membership
from saas.models import get_tenant_model
from tests.client import FixturesTestCase

Tenant = get_tenant_model()


class TestUserTenantsAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID

    def test_list_tenants(self):
        self.force_login()
        url = '/m/user/tenants/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        tenants = resp.json()
        self.assertEqual(len(tenants), 2)
        self.assertIn('role', tenants[0])
        self.assertNotIn('member_count', tenants[0])

        url = '/m/user/tenants/?include=member_count'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        tenants = resp.json()
        self.assertEqual(len(tenants), 2)
        self.assertIn('role', tenants[0])
        self.assertTrue(tenants[0]['is_owner'])
        self.assertEqual(tenants[0]['member_count'], 1)

        self.force_login(self.GUEST_USER_ID)
        resp = self.client.get(url)
        self.assertEqual(len(resp.json()), 0)

    def test_leave_tenant(self):
        self.force_login()
        resp = self.client.delete(f'/m/user/tenants/{self.tenant_id}/')
        self.assertEqual(resp.status_code, 403)

        self.force_login(self.GUEST_USER_ID)
        Membership.objects.create(user_id=self.GUEST_USER_ID, tenant_id=self.tenant_id)
        resp = self.client.delete(f'/m/user/tenants/{self.tenant_id}/')
        self.assertEqual(resp.status_code, 204)
