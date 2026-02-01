import uuid

from saas.identity.models import Invitation, UserEmail
from tests.client import FixturesTestCase


class TestAcceptInvitationView(FixturesTestCase):
    def create_invitation(self, status):
        return Invitation.objects.create(
            tenant_id=self.tenant.id,
            inviter_id=self.OWNER_USER_ID,
            email='new@example.com',
            status=status,
        )

    def test_accept_invalid_token(self):
        resp = self.client.get('/v/invites/accept/invalid-token/')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(f'/v/invites/accept/{uuid.uuid4()}/')
        self.assertEqual(resp.status_code, 404)

    def test_valid_invitation(self):
        invitation = self.create_invitation(Invitation.InviteStatus.SENT)
        resp = self.client.get(f'/v/invites/accept/{invitation.token}/')
        self.assertEqual(resp.status_code, 302)
        location = resp['Location']
        self.assertIn(f'/signup/?invite_code={invitation.token}', location)

    def test_invite_with_user(self):
        UserEmail.objects.create(
            user_id=self.GUEST_USER_ID,
            email='new@example.com',
        )
        invitation = self.create_invitation(Invitation.InviteStatus.SENT)
        resp = self.client.get(f'/v/invites/accept/{invitation.token}/')
        self.assertEqual(resp.status_code, 302)
        location = resp['Location']
        self.assertIn(f'/login/?invite_code={invitation.token}', location)

    def test_invite_already_accepted(self):
        invitation = self.create_invitation(Invitation.InviteStatus.ACCEPTED)
        resp = self.client.get(f'/v/invites/accept/{invitation.token}/')
        self.assertEqual(resp.status_code, 302)
        location = resp['Location']
        self.assertEqual(location, '/login/')

    def test_invitation_expired(self):
        invitation = self.create_invitation(Invitation.InviteStatus.EXPIRED)
        resp = self.client.get(f'/v/invites/accept/{invitation.token}/')
        self.assertEqual(resp.status_code, 404)
