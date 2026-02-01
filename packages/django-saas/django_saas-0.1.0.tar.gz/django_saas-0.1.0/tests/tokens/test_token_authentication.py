from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from saas.test import SaasTestCase
from saas.tokens.models import UserToken


class TestTokenAuthentication(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID
    tenant_id = 0

    def setup_user_token(self, scope):
        token = UserToken.objects.create(
            name='Test',
            scope=scope,
            user_id=self.user_id,
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.key)
        return token

    def test_can_not_fetch_tokens(self):
        self.setup_user_token('user')
        resp = self.client.get('/m/user/tokens/')
        self.assertEqual(resp.status_code, 403)

    def test_without_token(self):
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 403)

    def test_with_invalid_scope(self):
        self.setup_user_token('tenant')
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 403)

    def test_with_valid_scope(self):
        self.setup_user_token('user:read')
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 200)

    def test_record_token_last_used_at(self):
        # clear cache at first
        cache.clear()
        token = self.setup_user_token('user:read')
        self.assertIsNone(token.last_used_at)
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 200)
        token.refresh_from_db()
        last_used_at1 = token.last_used_at
        self.assertIsNotNone(last_used_at1)

        # second request should not update last_used_at
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 200)
        token.refresh_from_db()
        last_used_at2 = token.last_used_at
        self.assertEqual(last_used_at1, last_used_at2)

    def test_token_expired(self):
        token = self.setup_user_token('user:read')
        token.expires_at = timezone.now() - timedelta(days=1)
        token.save()
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 403)

    def test_token_with_tenant(self):
        token = UserToken.objects.create(
            name='Test',
            scope='user:read',
            user_id=self.user_id,
            tenant_id=1,
        )
        self.assertEqual(str(token), 'UserToken<Test>')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.key)
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 200)
