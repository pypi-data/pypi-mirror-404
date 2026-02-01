from django.test import override_settings

from saas.domain.models import Domain
from saas.tenancy.models import Member
from saas.test import SaasTestCase
from tests.settings import SAAS_DOMAIN

TEST_DATA = {
    'hostname': 'example.com',
    'provider': 'null',
}


class TestDomainAPIWithOwner(SaasTestCase):
    def test_list_domains(self):
        self.force_login(self.OWNER_USER_ID)

        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        Domain.objects.create(tenant=self.tenant, hostname='example.com')
        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]['hostname'], 'example.com')

    def test_create_domain(self):
        self.force_login(self.OWNER_USER_ID)
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['hostname'], 'example.com')
        self.assertFalse(data['verified'])
        self.assertTrue(data['primary'])
        hostname = data['hostname']
        resp = self.client.post(f'/m/domains/{hostname}/verify/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['verified'])

    @override_settings(SAAS_DOMAIN={**SAAS_DOMAIN, 'TENANT_MAX_DOMAINS': 2})
    def test_create_domain_not_primary(self):
        self.force_login(self.OWNER_USER_ID)
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        print(resp.json())
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertFalse(data['primary'])

    def test_create_blocked_domain(self):
        self.force_login(self.OWNER_USER_ID)
        payload = {
            'hostname': 'amce.blocked.domain',
            'provider': 'null',
        }
        resp = self.client.post('/m/domains/', data=payload)
        self.assertEqual(resp.status_code, 400)

    def test_multiple_domains(self):
        self.force_login(self.OWNER_USER_ID)
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        self.assertEqual(resp.status_code, 201)
        resp = self.client.post(
            '/m/domains/',
            data={
                'hostname': 'example2.com',
                'provider': 'null',
            },
        )
        self.assertEqual(resp.status_code, 403)

    def test_create_domain_with_invalid_provider(self):
        self.force_login(self.OWNER_USER_ID)
        payload = {
            'hostname': 'example.com',
            'provider': 'invalid',
        }
        resp = self.client.post('/m/domains/', data=payload)
        self.assertEqual(resp.status_code, 400)

    def test_delete_domain_with_admin_role(self):
        self.force_login(self.OWNER_USER_ID)

        domain = Domain.objects.create(tenant=self.tenant, hostname='example.com')
        resp = self.client.delete(f'/m/domains/{domain.hostname}/')
        self.assertEqual(resp.status_code, 204)

    def test_enable_and_refresh_domain(self):
        self.force_login(self.OWNER_USER_ID)
        domain = Domain.objects.create(
            tenant=self.tenant,
            hostname='example.com',
            provider='null',
        )
        # enable domain
        resp = self.client.post(f'/m/domains/{domain.hostname}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['instrument']['ownership_status'], 'pending')

    @override_settings(SAAS_DOMAIN={'TENANT_MAX_DOMAINS': 2})
    def test_set_primary_domain(self):
        self.force_login(self.OWNER_USER_ID)
        d1 = Domain.objects.create(tenant=self.tenant, hostname='example1.com', provider='null')
        d2 = Domain.objects.create(tenant=self.tenant, hostname='example2.com', provider='null')

        # Set d1 as primary
        resp = self.client.patch(f'/m/domains/{d1.hostname}/', data={'primary': True}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        d1.refresh_from_db()
        d2.refresh_from_db()
        self.assertTrue(d1.primary)
        self.assertFalse(d2.primary)

        # Set d2 as primary, d1 should be unset
        resp = self.client.patch(f'/m/domains/{d2.hostname}/', data={'primary': True}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        d1.refresh_from_db()
        d2.refresh_from_db()
        self.assertFalse(d1.primary)
        self.assertTrue(d2.primary)

        # Unset d2
        resp = self.client.patch(f'/m/domains/{d2.hostname}/', data={'primary': False}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        d1.refresh_from_db()
        d2.refresh_from_db()
        self.assertFalse(d1.primary)
        self.assertFalse(d2.primary)


class TestDomainAPIWithGuestUser(SaasTestCase):
    def test_list_domains_with_read_permission(self):
        user = self.force_login(self.MEMBER_USER_ID)
        Member.objects.create(tenant=self.tenant, user=user, role='MEMBER')

        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        Domain.objects.create(tenant=self.tenant, hostname='example.com')
        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]['hostname'], 'example.com')

    def test_list_domains_without_permission(self):
        self.force_login(self.GUEST_USER_ID)
        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 403)

    def test_create_domain_with_admin_role(self):
        user = self.force_login(self.ADMIN_USER_ID)
        Member.objects.create(tenant=self.tenant, user=user, role='ADMIN')
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        self.assertEqual(resp.status_code, 403)

    def test_create_domain_with_member_role(self):
        user = self.force_login(self.MEMBER_USER_ID)
        Member.objects.create(tenant=self.tenant, user=user, role='MEMBER')
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        self.assertEqual(resp.status_code, 403)

    def test_retrieve_domain_with_member_role(self):
        self.force_login(self.MEMBER_USER_ID)
        domain = Domain.objects.create(
            tenant=self.tenant,
            hostname='example.com',
            provider='null',
        )
        resp = self.client.get(f'/m/domains/{domain.hostname}/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(f'/m/domains/{domain.hostname}/verify/')
        self.assertEqual(resp.status_code, 403)

    def test_delete_domain_with_admin_role(self):
        self.force_login(self.ADMIN_USER_ID)

        domain = Domain.objects.create(tenant=self.tenant, hostname='example.com')
        resp = self.client.delete(f'/m/domains/{domain.hostname}/')
        self.assertEqual(resp.status_code, 403)
