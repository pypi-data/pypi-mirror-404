from tests.client import FixturesTestCase

TEST_DATA = {
    'hostname': 'example.com',
    'provider': 'cloudflare',
}


class TestCloudflareAPI(FixturesTestCase):
    user_id = FixturesTestCase.OWNER_USER_ID

    def test_add_domain(self):
        self.force_login()
        with self.mock_requests('domain/cloudflare_create_verified.json'):
            resp = self.client.post('/m/domains/', data=TEST_DATA)
            self.assertEqual(resp.status_code, 201)
            self.assertEqual(resp.json()['hostname'], 'example.com')
            self.assertTrue(resp.json()['verified'])
            self.assertTrue(resp.json()['ssl'])

    def test_add_ignore_hostnames(self):
        self.force_login()
        with self.mock_requests('domain/cloudflare_create_success.json'):
            resp = self.client.post(
                '/m/domains/',
                data={
                    'hostname': 'blog.localtest.me',
                    'provider': 'cloudflare',
                },
            )
            self.assertEqual(resp.status_code, 201)
            self.assertEqual(resp.json()['hostname'], 'blog.localtest.me')
            self.assertEqual(resp.json()['verified'], False)
            self.assertEqual(resp.json()['ssl'], False)

    def test_verify_domain(self):
        self.force_login()
        with self.mock_requests(
            'domain/cloudflare_create_success.json',
            'domain/cloudflare_verify_success.json',
        ):
            resp = self.client.post('/m/domains/', data=TEST_DATA)
            self.assertEqual(resp.status_code, 201)
            data = resp.json()
            hostname = data['hostname']
            resp = self.client.post(f'/m/domains/{hostname}/verify/')
            self.assertEqual(resp.status_code, 200)

    def test_remove_domain(self):
        self.force_login()
        with self.mock_requests(
            'domain/cloudflare_create_success.json',
            'domain/cloudflare_delete_success.json',
        ):
            resp = self.client.post('/m/domains/', data=TEST_DATA)
            self.assertEqual(resp.status_code, 201)
            data = resp.json()
            hostname = data['hostname']
            resp = self.client.delete(f'/m/domains/{hostname}/')
            self.assertEqual(resp.status_code, 204)
