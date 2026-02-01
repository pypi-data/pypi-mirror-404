from django.utils import timezone

from saas.models import get_tenant_model
from saas.tenancy.models import Group
from tests.client import FixturesTestCase

Tenant = get_tenant_model()


class TestGroupsAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID

    def test_list_groups(self):
        self.force_login()
        Group.objects.create(tenant_id=self.tenant_id, name='Admin')
        resp = self.client.get('/m/groups/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_create_group(self):
        self.force_login()
        data = {
            'name': 'Guest',
            'permissions': ['org.info.view'],
        }
        resp = self.client.post('/m/groups/', data=data)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['name'], 'Guest')
        permission = data['permissions'][0]
        self.assertEqual(permission, 'org.info.view')

    def test_expired_tenant_create_group(self):
        tenant = Tenant.objects.create(
            owner_id=self.user_id,
            name='Expired',
            slug='expired',
            expires_at=timezone.now(),
        )
        client = self.client_class()
        client.force_login(self.user)

        client.credentials(
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        data = {
            'name': 'Guest',
            'permissions': ['org.info.view'],
        }
        resp = client.post('/m/groups/', data=data)
        self.assertEqual(resp.status_code, 403)
        data = resp.json()
        self.assertEqual(data['detail'], 'This tenant is expired.')

    def test_retrieve_group(self):
        self.force_login()
        group = Group.objects.create(
            tenant_id=self.tenant_id,
            name='Admin',
            permissions=['iam.member.update', 'iam.member.invite', 'iam.group.manage'],
        )
        resp = self.client.get(f'/m/groups/{group.id}/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['permissions']), 3)

    def test_update_group_permissions(self):
        self.force_login()
        group = Group.objects.create(
            tenant_id=self.tenant_id,
            name='Admin',
            permissions=['iam.member.update', 'iam.member.invite', 'iam.group.manage'],
        )
        data = {'permissions': ['iam.member.update']}
        resp = self.client.patch(f'/m/groups/{group.id}/', data=data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['permissions']), 1)

        data = {'permissions': ['invalid.permission']}
        resp = self.client.patch(f'/m/groups/{group.id}/', data=data)
        self.assertEqual(resp.status_code, 400)

    def test_update_group_name(self):
        self.force_login()
        group = Group.objects.create(
            tenant_id=self.tenant_id,
            name='Admin',
            permissions=['iam.member.update', 'iam.member.invite', 'iam.group.manage'],
        )
        data = {'name': 'Admin 2'}
        resp = self.client.patch(f'/m/groups/{group.id}/', data=data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['name'], 'Admin 2')
        self.assertEqual(len(data['permissions']), 3)

    def test_delete_group(self):
        self.force_login()
        group = Group.objects.create(
            tenant_id=self.tenant_id,
            name='Admin',
            permissions=['iam.member.update', 'iam.member.invite', 'iam.group.manage'],
        )
        resp = self.client.delete(f'/m/groups/{group.id}/')
        self.assertEqual(resp.status_code, 204)
