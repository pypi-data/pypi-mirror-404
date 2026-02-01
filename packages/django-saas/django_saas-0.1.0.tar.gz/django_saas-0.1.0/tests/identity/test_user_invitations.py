from saas.identity.models import Invitation, UserEmail
from saas.tenancy.models import Member
from tests.client import FixturesTestCase


class TestUserInvitationsAPI(FixturesTestCase):
    user_id = FixturesTestCase.GUEST_USER_ID

    def setUp(self):
        super().setUp()
        self.invitation = Invitation.objects.create(
            tenant=self.tenant,
            inviter_id=self.OWNER_USER_ID,
            email=self.user.email,
            role='MEMBER',
            status=Invitation.InviteStatus.SENT,
        )

    def test_list_invitations(self):
        self.force_login()
        url = '/m/user/invitations/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.invitation.id)

    def test_accept_invitation(self):
        self.force_login()
        url = f'/m/user/invitations/{self.invitation.id}/'
        resp = self.client.patch(url, {'status': 'accepted'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'accepted')

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, Invitation.InviteStatus.ACCEPTED)
        self.assertIsNotNone(self.invitation.accepted_at)

        member = Member.objects.get(tenant_id=self.tenant_id, user_id=self.user_id)
        self.assertEqual(member.role, 'MEMBER')

    def test_accept_invitation_not_yours(self):
        self.invitation.email = 'other@example.com'
        self.invitation.save()

        self.force_login()
        url = f'/m/user/invitations/{self.invitation.id}/'
        resp = self.client.patch(url, {'status': 'accepted'})
        self.assertEqual(resp.status_code, 403)

    def test_accept_already_member(self):
        Member.objects.create(tenant=self.tenant, user=self.user, role='MEMBER')

        self.force_login()
        url = f'/m/user/invitations/{self.invitation.id}/'
        resp = self.client.patch(url, {'status': 'accepted'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'accepted')

    def test_accept_with_user_email(self):
        invitation = Invitation.objects.create(
            tenant_id=self.tenant_id,
            inviter_id=self.OWNER_USER_ID,
            email='new@example.com',
            role='MEMBER',
            status=Invitation.InviteStatus.SENT,
        )
        user_email = UserEmail.objects.create(user_id=self.GUEST_USER_ID, email='new@example.com')

        self.force_login(self.GUEST_USER_ID)
        url = f'/m/user/invitations/{invitation.id}/'
        resp = self.client.patch(url, {'status': 'accepted'})
        self.assertEqual(resp.status_code, 403)

        user_email.verified = True
        user_email.save()
        user_email.refresh_from_db()

        url = f'/m/user/invitations/{invitation.id}/'
        resp = self.client.patch(url, {'status': 'accepted'})
        self.assertEqual(resp.status_code, 200)
