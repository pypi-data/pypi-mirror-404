import uuid
from unittest.mock import Mock

from django.core.cache import cache
from django.utils import timezone

from saas.models import get_tenant_model
from saas.tenancy.models import Group, Member
from saas.test import SaasTestCase

Tenant = get_tenant_model()


class TestCachedManager(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID

    def setUp(self):
        super().setUp()
        cache.clear()

    def test_update_foreign_key(self):
        member = Member.objects.get_from_cache_by_natural_key(self.tenant_id, self.user_id)
        self.assertEqual(member.user.username, 'demo-1')

        user = self.get_user()
        user.username = 'changed-1'
        user.save()

        member = Member.objects.get_from_cache_by_natural_key(self.tenant_id, self.user_id)
        self.assertEqual(member.user.username, 'changed-1')

    def test_update_untracked_foreign_key1(self):
        tenant = Tenant.objects.get_from_cache_by_pk(self.tenant_id)
        self.assertEqual(tenant.owner_id, self.user_id)
        tenant.owner_id = self.ADMIN_USER_ID
        tenant.save()
        self.assertEqual(tenant.owner_id, self.ADMIN_USER_ID)

    def test_update_untracked_foreign_key2(self):
        tenant = Tenant.objects.get_from_cache_by_pk(self.tenant_id)
        self.assertEqual(tenant.owner_id, self.user_id)

    def test_update_m2m(self):
        member = Member.objects.get_from_cache_by_natural_key(self.tenant_id, self.user_id)
        perms = member.get_all_permissions()
        self.assertEqual(perms, {'*'})

        group = Group.objects.create(tenant_id=self.tenant_id, name='Admin', permissions=['org.info.view'])
        member.groups.add(group)

        member = Member.objects.get_from_cache_by_natural_key(self.tenant_id, self.user_id)
        perms = member.get_all_permissions()
        self.assertEqual(perms, {'*', 'org.info.view'})

    def test_update_field(self):
        tenant = Tenant.objects.get_from_cache_by_pk(self.tenant_id)
        tenant.name = 'Changed'
        self.assertEqual(tenant.name, 'Changed')

        tenant = Tenant.objects.get_from_cache_by_pk(self.tenant_id)
        self.assertIsNone(tenant.expires_at)
        self.assertNotEqual(tenant.name, 'Changed')

        tenant.name = 'Changed'
        tenant.expires_at = timezone.now()
        tenant.save()

        tenant = Tenant.objects.get_from_cache_by_pk(self.tenant_id)
        self.assertEqual(tenant.name, 'Changed')
        self.assertIsNotNone(tenant.expires_at)

    def test_get_many_from_cache(self):
        # Create members
        m1 = Member.objects.get(tenant_id=self.tenant_id, user_id=self.user_id)
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user2 = User.objects.create_user(username='u2', email='u2@example.com', password='password')
        m2 = Member.objects.create(tenant_id=self.tenant_id, user=user2, role='member')

        # Ensure m1 is in cache
        Member.objects.get_from_cache_by_pk(m1.pk)

        # Get many (m1 cached, m2 not)
        results = Member.objects.get_many_from_cache([m1.pk, m2.pk])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[m1.pk].pk, m1.pk)
        self.assertEqual(results[m2.pk].pk, m2.pk)
