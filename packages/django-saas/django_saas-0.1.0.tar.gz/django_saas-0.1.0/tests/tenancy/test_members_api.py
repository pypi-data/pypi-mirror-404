from saas.tenancy.models import Member
from tests.client import FixturesTestCase


class TestMembersAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID
    base_url = '/m/members/'

    def create_member(self):
        return Member.objects.create(
            tenant_id=self.tenant_id,
            user_id=self.MEMBER_USER_ID,
            role='MEMBER',
        )

    def test_list_invitations(self):
        self.force_login()
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 1)

        self.create_member()
        resp = self.client.get(self.base_url)
        data = resp.json()
        self.assertEqual(data['count'], 2)

    def test_update_member_role(self):
        self.force_login()
        member = self.create_member()
        data = {'role': 'ADMIN'}
        resp = self.client.patch(f'{self.base_url}{member.id}/', data=data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['role'], 'ADMIN')

    def test_update_member_role_invalid(self):
        self.force_login()
        member = self.create_member()
        data = {'role': 'INVALID'}
        resp = self.client.patch(f'{self.base_url}{member.id}/', data=data)
        self.assertEqual(resp.status_code, 400)

    def test_update_role_not_permission(self):
        self.force_login(user_id=self.MEMBER_USER_ID)
        member = self.create_member()
        data = {'role': 'ADMIN'}
        resp = self.client.patch(f'{self.base_url}{member.id}/', data=data)
        self.assertEqual(resp.status_code, 403)

    def test_update_always_owner(self):
        self.force_login(self.OWNER_USER_ID)
        member = Member.objects.get(user_id=self.OWNER_USER_ID, tenant_id=self.tenant_id)
        data = {'role': 'ADMIN'}
        resp = self.client.patch(f'{self.base_url}{member.id}/', data=data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['role'], 'OWNER')

    def test_update_member_permissions(self):
        self.force_login()
        member = self.create_member()
        data = {'permissions': ['iam.member.view']}
        resp = self.client.patch(f'{self.base_url}{member.id}/', data=data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['permissions']), 1)

    def test_update_member_permissions_invalid(self):
        self.force_login()
        member = self.create_member()
        data = {'permissions': ['invalid.permission']}
        resp = self.client.patch(f'{self.base_url}{member.id}/', data=data)
        self.assertEqual(resp.status_code, 400)

    def test_delete_member(self):
        self.force_login()
        member = self.create_member()
        resp = self.client.delete(f'{self.base_url}{member.id}/')
        self.assertEqual(resp.status_code, 204)
