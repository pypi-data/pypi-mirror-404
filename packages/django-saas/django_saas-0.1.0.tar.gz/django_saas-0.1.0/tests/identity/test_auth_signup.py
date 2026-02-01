from django.core import mail
from django.test import override_settings

from saas.identity.models import Invitation, UserEmail
from tests.client import FixturesTestCase


class TestSignUpWithoutCreateUser(FixturesTestCase):
    user_id = FixturesTestCase.ADMIN_USER_ID

    def test_signup_success(self):
        data1 = {'email': 'hi@foo.com'}
        resp = self.client.post('/m/auth/signup/request/', data=data1)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)
        data2 = {
            'username': 'demo',
            'email': 'hi@foo.com',
            'password': 'hello world',
            'code': self.get_mail_auth_code(),
        }
        resp = self.client.post('/m/auth/signup/confirm/', data=data2)
        self.assertEqual(resp.status_code, 200)

    def test_signup_existed_email(self):
        user = self.get_user()
        UserEmail.objects.create(user=user, email='hi@foo.com', primary=True, verified=True)
        data = {'username': 'foo', 'email': 'hi@foo.com', 'password': 'hello world'}
        resp = self.client.post('/m/auth/signup/request/', data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('existing', resp.json()['email'][0])

    def test_signup_blocked_email(self):
        rules = [{'backend': 'saas.rules.BlockedEmailDomains'}]
        with override_settings(SAAS_IDENTITY={'SIGNUP_SECURITY_RULES': rules}):
            data = {'username': 'bar', 'email': 'hi@boofx.com', 'password': 'hello world'}
            resp = self.client.post('/m/auth/signup/request/', data=data)
            self.assertEqual(resp.status_code, 400)

        rules = [{'backend': 'saas.rules.BlockedEmailDomains', 'options': {'domains': ['bar.com']}}]
        with override_settings(SAAS_IDENTITY={'SIGNUP_SECURITY_RULES': rules}):
            data = {'username': 'bar', 'email': 'hi@bar.com', 'password': 'hello world'}
            resp = self.client.post('/m/auth/signup/request/', data=data)
            self.assertEqual(resp.status_code, 400)

    def test_signup_too_many_dots(self):
        rules = [{'backend': 'saas.rules.AvoidTooManyDots'}]
        with override_settings(SAAS_IDENTITY={'SIGNUP_SECURITY_RULES': rules}):
            data = {'username': 'bar', 'email': 'a.b.c.d.e.f@bar.com', 'password': 'hello world'}
            resp = self.client.post('/m/auth/signup/request/', data=data)
            self.assertEqual(resp.status_code, 400)

    def test_signup_using_plus(self):
        rules = [{'backend': 'saas.rules.AvoidUsingPlus'}]
        with override_settings(SAAS_IDENTITY={'SIGNUP_SECURITY_RULES': rules}):
            data = {'username': 'bar', 'email': 'username+demo@gmail.com', 'password': 'hello world'}
            resp = self.client.post('/m/auth/signup/request/', data=data)
            self.assertEqual(resp.status_code, 400)

    def test_signup_turnstile(self):
        rules = [{'backend': 'saas.rules.Turnstile'}]
        with override_settings(SAAS_IDENTITY={'SIGNUP_SECURITY_RULES': rules}):
            data = {'username': 'bar', 'email': 'hi@bar.com', 'password': 'hello world'}
            resp = self.client.post('/m/auth/signup/request/', data=data)
            self.assertEqual(resp.status_code, 400)

            data = {**data, 'cf-turnstile-response': '**token**'}
            with self.mock_requests('turnstile_success.json'):
                resp = self.client.post('/m/auth/signup/request/', data=data)
                self.assertEqual(resp.status_code, 204)

            data = {**data, 'cf-turnstile-response': '**token**'}
            with self.mock_requests('turnstile_failed.json'):
                resp = self.client.post('/m/auth/signup/request/', data=data)
                self.assertEqual(resp.status_code, 400)

    def test_turnstile_with_real_http(self):
        rules = [{'backend': 'saas.rules.Turnstile', 'options': {'secret': 'secret:turnstile'}}]
        with override_settings(SAAS_IDENTITY={'SIGNUP_SECURITY_RULES': rules}):
            data = {
                'username': 'bar',
                'email': 'hi@bar.com',
                'password': 'hello world',
                'cf-turnstile-response': '**token**',
            }
            resp = self.client.post('/m/auth/signup/request/', data=data)
            self.assertEqual(resp.status_code, 204)

    def test_signup_with_waiting_invitation(self):
        email = 'hi@foo.com'
        obj = Invitation.objects.create(
            tenant_id=self.tenant_id,
            email=email,
            status=Invitation.InviteStatus.SENT,
        )
        data = {'username': 'demo', 'password': 'hello world'}
        resp = self.client.post(f'/m/auth/signup/invite/{obj.token}/', data=data)
        self.assertEqual(resp.status_code, 200)

    def test_signup_with_pending_invitation(self):
        user = self.get_user()
        obj = Invitation.objects.create(
            tenant_id=self.tenant_id,
            email=user.email,
            status=Invitation.InviteStatus.PENDING,
        )
        data = {'username': 'demo', 'password': 'hello world'}
        resp = self.client.post(f'/m/auth/signup/invite/{obj.token}/', data=data)
        self.assertEqual(resp.status_code, 404)


@override_settings(SAAS_IDENTITY={'SIGNUP_REQUEST_CREATE_USER': True})
class TestSignUpWithCreateUser(FixturesTestCase):
    def test_signup_success(self):
        data1 = {'username': 'demo', 'email': 'hi@foo.com', 'password': 'hello world'}
        resp = self.client.post('/m/auth/signup/request/', data=data1)
        self.assertEqual(resp.status_code, 204)
        obj = UserEmail.objects.get(email='hi@foo.com')
        self.assertEqual(obj.verified, False)

        data2 = {'code': self.get_mail_auth_code(), 'email': 'hi@foo.com'}
        resp = self.client.post('/m/auth/signup/confirm/', data=data2)
        self.assertEqual(resp.status_code, 200)
        obj = UserEmail.objects.get(email='hi@foo.com')
        self.assertEqual(obj.verified, True)
