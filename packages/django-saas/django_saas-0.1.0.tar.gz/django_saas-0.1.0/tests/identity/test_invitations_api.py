import re

from django.core import mail

from saas.identity.models import Invitation
from tests.client import FixturesTestCase


class TestInvitationsAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID
    base_url = '/m/invitations/'

    def setUp(self):
        super().setUp()
        self.invitation = Invitation.objects.create(
            tenant=self.tenant,
            inviter_id=self.OWNER_USER_ID,
            email='invitee@example.com',
            role='MEMBER',
            status=Invitation.InviteStatus.SENT,
        )

    @staticmethod
    def get_mail_invite_link():
        msg = mail.outbox[0]
        links = re.findall(r'(http:.+?)\n', msg.body)
        return links[0]

    def test_list_invitations(self):
        self.force_login()
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)

    def test_create_invitation(self):
        self.force_login()
        data = {
            'email': 'new@example.com',
            'role': 'MEMBER',
        }
        resp = self.client.post(self.base_url, data)
        self.assertEqual(resp.status_code, 201)

        invitation = Invitation.objects.get(email='new@example.com')
        self.assertEqual(invitation.tenant_id, self.tenant_id)
        self.assertEqual(invitation.role, 'MEMBER')
        self.assertEqual(invitation.inviter_id, self.user_id)

        # tracing invite link
        link = self.get_mail_invite_link()
        self.assertEqual(link, f'http://testserver/v/invites/accept/{invitation.token}/')
        resp = self.client.get(link)
        self.assertEqual(resp.status_code, 404)
        invitation.status = Invitation.InviteStatus.SENT
        invitation.save()
        resp = self.client.get(link)
        self.assertEqual(resp.status_code, 302)

    def test_create_invitation_invalid_role(self):
        self.force_login()
        data = {
            'email': 'new@example.com',
            'role': 'INVALID',
        }
        resp = self.client.post(self.base_url, data)
        self.assertEqual(resp.status_code, 400)

    def test_invite_self(self):
        self.force_login()
        email = self.user.email
        data = {
            'email': email,
            'role': 'MEMBER',
        }
        resp = self.client.post(self.base_url, data)
        self.assertEqual(resp.status_code, 400)
        errors = resp.json()
        self.assertEqual(errors['email'][0], 'This user is already a member.')

    def test_invite_already_exist(self):
        self.force_login()
        data = {
            'email': 'invitee@example.com',
            'role': 'MEMBER',
        }
        resp = self.client.post(self.base_url, data)
        self.assertEqual(resp.status_code, 400)
        errors = resp.json()
        self.assertEqual(errors['email'][0], 'This email has already been invited.')

    def test_update_invitation(self):
        self.force_login()
        url = f'/m/invitations/{self.invitation.id}/'
        data = {
            'role': 'ADMIN',
        }
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, 200)

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.role, 'ADMIN')

    def test_delete_invitation(self):
        self.force_login()
        url = f'/m/invitations/{self.invitation.id}/'
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

        self.assertFalse(Invitation.objects.filter(id=self.invitation.id).exists())

    def test_permission_denied(self):
        self.force_login(self.GUEST_USER_ID)
        url = '/m/invitations/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        resp = self.client.post(url, {'email': 'test@example.com', 'role': 'MEMBER'})
        self.assertEqual(resp.status_code, 403)

    def test_update_invalid_invitation(self):
        self.force_login()
        url = '/m/invitations/invalid/'
        data = {'role': 'ADMIN'}
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, 404)
