from unittest.mock import Mock

from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from saas.drf.permissions import (
    HasResourcePermission,
    IsTenantActive,
    IsTenantActiveOrReadOnly,
    IsTenantOwner,
    IsTenantOwnerOrReadOnly,
)
from saas.identity.endpoints.tenant import TenantItemEndpoint
from saas.middleware import TenantMiddleware
from saas.models import get_tenant_model
from saas.tenancy.models import Member
from tests.client import FixturesTestCase

Tenant = get_tenant_model()


class TestIsTenantOwner(FixturesTestCase):
    def setUp(self):
        super().setUp()
        self.permission = IsTenantOwner()
        self.view = Mock()
        factory = RequestFactory()
        self.middleware = TenantMiddleware(lambda req: HttpResponse())
        self.request = Request(factory.get('/'))
        self.request.tenant_id = self.tenant_id

    def test_has_permission_owner(self):
        self.request.user = self.force_login(self.OWNER_USER_ID)
        self.middleware(self.request)
        self.assertTrue(self.permission.has_permission(self.request, self.view))

    def test_has_permission_member(self):
        self.middleware(self.request)
        self.request.user = self.force_login(self.MEMBER_USER_ID)
        self.assertFalse(self.permission.has_permission(self.request, self.view))

        # readonly passes
        permission = IsTenantOwnerOrReadOnly()
        self.assertTrue(permission.has_permission(self.request, self.view))


class TestIsTenantActive(FixturesTestCase):
    def setUp(self):
        super().setUp()
        self.permission = IsTenantActive()
        self.view = Mock()
        factory = RequestFactory()
        self.middleware = TenantMiddleware(lambda req: HttpResponse())
        self.request = Request(factory.get('/'))
        self.request.tenant_id = self.tenant_id

    def test_active_tenant(self):
        self.middleware(self.request)
        user = self.force_login(self.MEMBER_USER_ID)
        self.request.user = user
        self.assertTrue(self.permission.has_permission(self.request, self.view))

    def test_expired_tenant(self):
        tenant = self.get_tenant(self.tenant_id)
        tenant.expires_at = timezone.now() - timezone.timedelta(days=1)
        tenant.save()
        user = self.force_login(self.MEMBER_USER_ID)
        self.request.user = user
        self.middleware(self.request)

        with self.assertRaises(PermissionDenied):
            self.permission.has_permission(self.request, self.view)

        # readonly passes
        permission = IsTenantActiveOrReadOnly()
        self.assertTrue(permission.has_permission(self.request, self.view))


class TestHasResourcePermission(FixturesTestCase):
    def setUp(self):
        super().setUp()
        self.permission = HasResourcePermission()
        self.view = TenantItemEndpoint.as_view()
        self.view.required_permission = 'org.info.view'
        factory = RequestFactory()
        self.middleware = TenantMiddleware(lambda req: HttpResponse())
        self.request = Request(factory.get('/'))
        self.request._auth = None
        self.request.tenant_id = self.tenant_id

    def test_has_permission_owner(self):
        user = self.force_login(self.OWNER_USER_ID)
        self.middleware(self.request)
        self.request.user = user
        self.assertTrue(self.permission.has_permission(self.request, self.view))

    def test_has_permission_member_with_perm(self):
        user = self.force_login(self.MEMBER_USER_ID)
        member = Member.objects.create(tenant=self.tenant, user=user, role='MEMBER')
        self.request.user = user
        self.middleware(self.request)
        self.assertTrue(self.permission.has_permission(self.request, self.view))

        # Test without permission
        member.role = None
        member.save()
        # SimpleLazyObject will be cached
        self.middleware(self.request)
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_has_permission_with_invalid_token_scope(self):
        user = self.force_login(self.MEMBER_USER_ID)
        self.request.user = user
        self.middleware(self.request)

        class Token1:
            scope = 'profile'

        self.request._auth = Token1
        self.assertFalse(self.permission.has_permission(self.request, self.view))

        class Token2:
            scopes = ['profile']

        self.request._auth = Token2
        self.assertFalse(self.permission.has_permission(self.request, self.view))

        class Token3:
            def get_scopes(self):
                return ['profile']

        self.request._auth = Token3()
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_has_permission_with_valid_token_scope(self):
        user = self.force_login(self.MEMBER_USER_ID)
        self.request.user = user
        self.middleware(self.request)
        Member.objects.create(tenant=self.tenant, user=user, role='MEMBER')

        class Token1:
            scope = 'org:read'

        self.request._auth = Token1
        self.assertTrue(self.permission.has_permission(self.request, self.view))

        class Token2:
            scopes = ['org:read']

        self.request._auth = Token2
        self.assertTrue(self.permission.has_permission(self.request, self.view))
