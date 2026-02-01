from tests.client import FixturesTestCase


class TestInternalsAPI(FixturesTestCase):
    def test_list_all_permissions(self):
        resp = self.client.get('/m/_/permissions/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_list_all_roles(self):
        resp = self.client.get('/m/_/roles/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        role_names = [d['name'] for d in data]
        self.assertIn('Owner', role_names)

    def test_list_all_scopes(self):
        resp = self.client.get('/m/_/scopes/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        scope_keys = [d['key'] for d in data]
        self.assertIn('profile', scope_keys)

        user_scope = [d for d in data if d['key'] == 'user'][0]
        self.assertIn('user:read', user_scope['includes'])
        self.assertIn('user:write', user_scope['includes'])
