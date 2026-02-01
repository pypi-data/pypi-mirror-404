from saas.test import SaasTestCase


class TestUserTokensAPI(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID

    def test_list_user_sessions(self):
        self.force_login()
        # Create another session for the user
        from saas.sessions.models import Session

        Session.objects.create(
            user_id=self.user_id,
            session_key='other_session',
            user_agent='Other',
            expiry_date='2099-01-01 00:00:00+00:00',
        )

        resp = self.client.get('/m/user/sessions/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 2)

        results = data['results']
        current = next(r for r in results if r['current_session'])
        other = next(r for r in results if not r['current_session'])
        self.assertTrue(current)
        self.assertFalse(other['current_session'])

    def test_retrieve_user_session(self):
        self.force_login()
        resp = self.client.get('/m/user/sessions/')
        data = resp.json()
        session_id = data['results'][0]['id']
        resp = self.client.get(f'/m/user/sessions/{session_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['current_session'])

        resp = self.client.delete(f'/m/user/sessions/{session_id}/')
        self.assertEqual(resp.status_code, 204)
