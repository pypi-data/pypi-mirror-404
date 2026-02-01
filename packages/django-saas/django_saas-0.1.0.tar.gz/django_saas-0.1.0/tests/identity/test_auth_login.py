import datetime
import uuid

from django.utils import timezone

from saas.identity.models import Invitation, UserEmail
from saas.tenancy.models import Member
from tests.client import FixturesTestCase


class TestLoginAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID

    def test_login_with_username(self):
        user = self.get_user()

        data = {'username': user.username, 'password': 'hello world'}
        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 400)

        user.set_password('hello world')
        user.save()

        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('next', resp.json())

    def test_login_with_email(self):
        user = self.get_user()

        data = {'username': 'hi@foo.com', 'password': 'hello world'}
        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 400)

        user.set_password('hello world')
        user.save()

        UserEmail.objects.create(user=user, email='hi@foo.com', verified=True, primary=True)
        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['username'], user.username)

    def test_login_with_not_primary_email(self):
        user = self.get_user()
        user.set_password('hello world')
        user.save()

        data = {'username': 'hi@foo.com', 'password': 'hello world'}
        UserEmail.objects.create(user=user, email='hi@foo.com', verified=True, primary=False)
        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 400)

    def test_login_with_not_verified_email(self):
        user = self.get_user()
        user.set_password('hello world')
        user.save()

        data = {'username': 'hi@foo.com', 'password': 'hello world'}
        UserEmail.objects.create(user=user, email='hi@foo.com', verified=False, primary=True)
        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 400)

    def _login_with_inviation(self, user, invitation, status):
        data = {'username': user.username, 'password': 'hello world', 'invite_code': str(invitation.token)}
        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 200)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, status)

    def test_login_with_invitation(self):
        user = self.get_user(self.GUEST_USER_ID)
        user.set_password('hello world')
        user.save()

        invitation = Invitation.objects.create(
            tenant_id=self.tenant_id,
            email=user.email,
            status=Invitation.InviteStatus.PENDING,
            role='MEMBER',
        )
        self._login_with_inviation(user, invitation, Invitation.InviteStatus.ACCEPTED)

        member = Member.objects.get(user=user, tenant=self.tenant)
        self.assertEqual(member.role, 'MEMBER')

    def test_login_with_invitation_invalid_code(self):
        user = self.get_user(self.GUEST_USER_ID)
        user.set_password('hello world')
        user.save()

        data = {'username': user.username, 'password': 'hello world', 'invite_code': 'INVALID'}
        resp = self.client.post('/m/auth/login/', data=data)
        # we just bypass it
        self.assertEqual(resp.status_code, 200)

        data = {'username': user.username, 'password': 'hello world', 'invite_code': str(uuid.uuid4())}
        resp = self.client.post('/m/auth/login/', data=data)
        self.assertEqual(resp.status_code, 200)

    def test_login_with_invitation_expired(self):
        user = self.get_user(self.GUEST_USER_ID)
        user.set_password('hello world')
        user.save()

        invitation = Invitation.objects.create(
            tenant_id=self.tenant_id,
            email=user.email,
            status=Invitation.InviteStatus.PENDING,
            expires_at=timezone.now() - datetime.timedelta(days=1),
        )

        self._login_with_inviation(user, invitation, Invitation.InviteStatus.PENDING)

    def test_login_with_not_self_invitation(self):
        user = self.get_user(self.GUEST_USER_ID)
        user.set_password('hello world')
        user.save()

        member_user = self.get_user(self.MEMBER_USER_ID)
        invitation = Invitation.objects.create(
            tenant_id=self.tenant_id,
            email=member_user.email,
            status=Invitation.InviteStatus.PENDING,
        )
        self._login_with_inviation(user, invitation, Invitation.InviteStatus.PENDING)

    def test_login_with_invitation_already_accepted(self):
        user = self.get_user(self.GUEST_USER_ID)
        user.set_password('hello world')
        user.save()

        invitation = Invitation.objects.create(
            tenant_id=self.tenant_id,
            email=user.email,
            status=Invitation.InviteStatus.ACCEPTED,
        )

        self._login_with_inviation(user, invitation, Invitation.InviteStatus.ACCEPTED)
