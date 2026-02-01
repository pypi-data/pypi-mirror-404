from saas.models import get_tenant_model
from saas.tenancy.models import Member
from tests.client import FixturesTestCase


class TestTenantsAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID

    def test_list_tenants(self):
        self.force_login()
        resp = self.client.get('/m/tenants/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_create_tenant(self):
        self.force_login()
        data = {'name': 'Demo', 'slug': 'demo'}
        resp = self.client.post('/m/tenants/', data=data)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['name'], 'Demo')

    def test_create_too_many_tenant(self):
        self.force_login(self.GUEST_USER_ID)
        for i in range(10):
            data = {'name': 'Demo', 'slug': f'test-{i}'}
            resp = self.client.post('/m/tenants/', data=data)
            self.assertEqual(resp.status_code, 201)

        data = {'name': 'Demo', 'slug': f'test-11'}
        resp = self.client.post('/m/tenants/', data=data)
        self.assertEqual(resp.status_code, 403)

    def test_fetch_tenant(self):
        self.force_login()
        resp = self.client.get('/m/tenants/1/')
        self.assertEqual(resp.status_code, 200)

    def test_update_tenant(self):
        self.force_login()
        data = {'name': 'Demo 2'}
        resp = self.client.patch('/m/tenants/1/', data=data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['name'], 'Demo 2')

    def test_cannot_update_readonly_fields(self):
        self.force_login()
        data = {'slug': 'demo-2'}
        resp = self.client.patch('/m/tenants/1/', data=data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['slug'], 'demo-1')

    def test_transfer_tenant(self):
        self.force_login()
        user = self.get_user(self.ADMIN_USER_ID)
        data = {'username': user.username, 'action': 'request'}
        resp = self.client.post('/m/tenants/1/transfer/', data=data)
        self.assertEqual(resp.status_code, 204)

        data = {'username': user.username, 'action': 'confirm', 'code': 'MISS'}
        resp = self.client.post('/m/tenants/1/transfer/', data=data)
        self.assertEqual(resp.status_code, 400)

        code = self.get_mail_auth_code()
        data = {'username': user.username, 'action': 'confirm', 'code': code}
        resp = self.client.post('/m/tenants/1/transfer/', data=data)
        self.assertEqual(resp.status_code, 204)
        tenant = self.get_tenant(1)
        self.assertEqual(tenant.owner, user)

        member = Member.objects.get(tenant=tenant, user=user)
        self.assertEqual(member.role, 'OWNER')

    def test_transfer_tenant_invalid_username(self):
        self.force_login()
        data = {'username': 'invalid', 'action': 'request'}
        resp = self.client.post('/m/tenants/1/transfer/', data=data)
        self.assertEqual(resp.status_code, 400)

    def test_transfer_tenant_no_code(self):
        self.force_login()
        user = self.get_user(self.ADMIN_USER_ID)
        data = {'username': user.username, 'action': 'confirm', 'code': ''}
        resp = self.client.post('/m/tenants/1/transfer/', data=data)
        self.assertEqual(resp.status_code, 400)

    def test_destroy_tenant(self):
        self.force_login()
        data = {'action': 'request'}
        resp = self.client.post('/m/tenants/1/destroy/', data=data)
        self.assertEqual(resp.status_code, 204)
        code = self.get_mail_auth_code()
        data = {'action': 'confirm', 'code': code}
        resp = self.client.post('/m/tenants/1/destroy/', data=data)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(get_tenant_model().objects.filter(id=1).exists())

    def test_destroy_tenant_invalid_code(self):
        self.force_login()
        data = {'action': 'confirm', 'code': 'MISS'}
        resp = self.client.post('/m/tenants/1/destroy/', data=data)
        self.assertEqual(resp.status_code, 400)

    def test_destroy_tenant_no_code(self):
        self.force_login()
        data = {'action': 'confirm'}
        resp = self.client.post('/m/tenants/1/destroy/', data=data)
        self.assertEqual(resp.status_code, 400)


class TestTenantsUsingGuestUser(FixturesTestCase):
    user_id = FixturesTestCase.GUEST_USER_ID

    def test_fetch_tenant(self):
        self.force_login()
        resp = self.client.get('/m/tenants/1/')
        self.assertEqual(resp.status_code, 403)

    def test_update_tenant(self):
        self.force_login()
        data = {'name': 'Demo 2'}
        resp = self.client.patch('/m/tenants/1/', data=data)
        self.assertEqual(resp.status_code, 403)

    def test_can_not_transfer_tenant(self):
        self.force_login()
        user = self.get_user(self.ADMIN_USER_ID)
        data = {'username': user.username, 'action': 'request'}
        resp = self.client.post('/m/tenants/1/transfer/', data=data)
        self.assertEqual(resp.status_code, 403)
