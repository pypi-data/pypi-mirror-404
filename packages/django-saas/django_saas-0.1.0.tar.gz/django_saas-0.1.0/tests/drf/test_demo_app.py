from tests.client import FixturesTestCase


class TestDemoAppAPI(FixturesTestCase):
    def test_create_secret_by_guest(self):
        self.force_login(self.GUEST_USER_ID)
        resp = self.client.post('/m/secrets/', data={'secret': 'hello world'})
        self.assertEqual(resp.status_code, 403)

    def test_create_secret_by_owner(self):
        self.force_login(self.OWNER_USER_ID)
        resp = self.client.post('/m/secrets/', data={'secret': 'hello world'})
        self.assertEqual(resp.status_code, 201)

    def test_update_secret(self):
        self.force_login(self.OWNER_USER_ID)
        resp = self.client.post('/m/secrets/', data={'secret': 'hello world'})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        obj_id = data['id']
        resp = self.client.patch(f'/m/secrets/{obj_id}/', data={'secret': 'hello2'})
        self.assertEqual(resp.status_code, 204)
