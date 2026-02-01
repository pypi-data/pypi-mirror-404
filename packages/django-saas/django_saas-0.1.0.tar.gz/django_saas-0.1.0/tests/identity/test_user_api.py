from django.test import override_settings

from saas.identity.models import UserProfile
from saas.test import SaasTestCase


class TestUserAPI(SaasTestCase):
    user_id = SaasTestCase.GUEST_USER_ID

    def test_get_current_user(self):
        self.force_login()
        url = '/m/user/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data['avatar_url'])

        UserProfile.objects.create(user_id=self.user_id, avatar_url='https://example.com/avatar.jpg')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['avatar_url'], 'https://example.com/avatar.jpg')

    def test_update_user(self):
        self.force_login()
        payload = {'first_name': 'First', 'avatar_url': 'https://example.com/avatar2.jpg'}
        resp = self.client.patch('/m/user/', data=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['first_name'], 'First')
        self.assertEqual(data['avatar_url'], 'https://example.com/avatar2.jpg')

        payload = {'last_name': 'Last', 'avatar_url': 'https://example.com/avatar3.jpg'}
        resp = self.client.patch('/m/user/', data=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['first_name'], 'First')
        self.assertEqual(data['last_name'], 'Last')
        self.assertEqual(data['avatar_url'], 'https://example.com/avatar3.jpg')

    def test_use_gravatar(self):
        self.force_login()
        resp = self.client.get('/m/user/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data['avatar_url'])

        with override_settings(SAAS_IDENTITY={'ENABLE_GRAVATAR': True}):
            resp = self.client.get('/m/user/')
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data['avatar_url'].startswith('https://gravatar.com/avatar/'))
