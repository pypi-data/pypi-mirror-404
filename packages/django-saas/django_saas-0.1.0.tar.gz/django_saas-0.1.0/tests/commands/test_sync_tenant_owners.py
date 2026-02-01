from io import StringIO

from django.core.management import call_command

from saas.identity.models import Membership
from saas.tenancy.models import Member
from tests.client import FixturesTestCase


class TestSyncTenantOwners(FixturesTestCase):
    def test_sync_tenant_owners_creates_missing_member(self):
        # clear all existing memberships
        Membership.objects.all().delete()
        Member.objects.all().delete()

        tenant = self.tenant
        self.assertFalse(Member.objects.filter(tenant=tenant, user=tenant.owner).exists())

        call_command('sync_tenant_owners')

        member = Member.objects.get(tenant=tenant, user=tenant.owner)
        self.assertEqual(member.role, 'OWNER')

    def test_sync_tenant_owners_updates_wrong_role(self):
        tenant = self.tenant
        Membership.objects.filter(tenant=tenant, user=tenant.owner).update(role='MEMBER')
        Member.objects.filter(tenant=tenant, user=tenant.owner).update(role='MEMBER')

        call_command('sync_tenant_owners')

        member = Member.objects.get(tenant=tenant, user=tenant.owner)
        member.refresh_from_db()
        self.assertEqual(member.role, 'OWNER')

    def test_sync_tenant_owners_no_changes_needed(self):
        tenant = self.tenant
        member = Member.objects.get(tenant=tenant, user=tenant.owner)
        self.assertEqual(member.role, 'OWNER')

        # Capture output to verify counts
        out = StringIO()
        call_command('sync_tenant_owners', stdout=out)

        output = out.getvalue()
        self.assertIn('Created 0 missing owner members', output)
        self.assertIn('Updated 0 owner roles', output)
