from saas.identity.models import Invitation
from tests.client import FixturesTestCase


class TestInvitationAPI(FixturesTestCase):
    user_id = FixturesTestCase.ADMIN_USER_ID

    def test_pending_status_invitation(self):
        email = 'hi@foo.com'
        obj = Invitation.objects.create(tenant_id=self.tenant_id, email=email)
        resp = self.client.get(f'/m/auth/invitation/{obj.token}/')
        self.assertEqual(resp.status_code, 200)
        result = resp.json()
        self.assertEqual(result['status'], 'pending')

    def test_sent_status_invitation(self):
        obj = Invitation.objects.create(
            tenant_id=self.tenant_id,
            inviter_id=self.user_id,
            email='hi@foo.com',
            status=Invitation.InviteStatus.SENT,
        )
        resp = self.client.get(f'/m/auth/invitation/{obj.token}/')
        self.assertEqual(resp.status_code, 200)
        result = resp.json()
        self.assertEqual(result['status'], 'sent')

    def test_accepted_status_invitation(self):
        obj = Invitation.objects.create(
            tenant_id=self.tenant_id,
            inviter_id=self.user_id,
            email='hi@foo.com',
            status=Invitation.InviteStatus.ACCEPTED,
        )
        resp = self.client.get(f'/m/auth/invitation/{obj.pk}/')
        self.assertEqual(resp.status_code, 404)
