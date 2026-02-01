from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from saas.models import get_tenant_model
from saas.registry import perm_registry
from saas.registry.checker import get_view_permission, has_permission

__all__ = [
    'IsTenantOwner',
    'IsTenantOwnerOrReadOnly',
    'IsTenantActive',
    'IsTenantActiveOrReadOnly',
    'HasResourcePermission',
    'HasResourcePermissionOrReadOnly',
]

TenantModel = get_tenant_model()


class BaseTenantPermission(BasePermission):
    tenant_id_field = 'tenant_id'

    @staticmethod
    def check_tenant_permission(request, view):
        return True

    def has_permission(self, request: Request, view):
        if not request.user.is_authenticated:
            return False

        # tenant is required for this permission
        if not hasattr(request, 'tenant'):
            raise ImproperlyConfigured('Missing TenantMiddleware in MIDDLEWARE setting.')

        if not request.tenant:
            return False

        return self.check_tenant_permission(request, view)


class IsTenantOwner(BaseTenantPermission):
    """The authenticated user is the tenant owner."""

    @staticmethod
    def check_tenant_permission(request, view):
        return request.user.pk == request.tenant.owner_id


class IsTenantOwnerOrReadOnly(IsTenantOwner):
    """The authenticated user is the tenant owner, or is a read-only request."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().has_permission(request, view)


class IsTenantActive(BaseTenantPermission):
    """The requested tenant is not expired."""

    @staticmethod
    def check_tenant_permission(request, view):
        tenant = request.tenant

        if not tenant.expires_at:
            return True

        if tenant.expires_at < timezone.now():
            raise PermissionDenied(_('This tenant is expired.'))
        return True


class IsTenantActiveOrReadOnly(IsTenantActive):
    """The requested tenant is not expired, or is a read-only request."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().has_permission(request, view)


class HasResourcePermission(BasePermission):
    """The authenticated user is a member of the tenant, and the user
    has the given resource permission.
    """

    tenant_id_field = 'tenant_id'

    def has_permission(self, request: Request, view):
        required_perm = get_view_permission(view, request.method)
        # attach current required_permission to Django's request
        setattr(request._request, 'required_permission', required_perm)

        if not required_perm:
            return True

        if not request.user.is_authenticated:
            return False

        # filter scopes permissions
        if request.auth:
            scopes_perms = self.get_scopes_permissions(request.auth)
            if not has_permission(required_perm, scopes_perms):
                return False

        # this is a tenant related permission
        if required_perm.startswith('user.'):
            # user related permission has been checked above by token scopes permissions
            # if there is no `request.auth`, it is a session based authentication
            return True

        # tenant is required for this permission
        if not hasattr(request, 'tenant') or not hasattr(request, 'tenant_member'):
            raise ImproperlyConfigured('Missing TenantMiddleware in MIDDLEWARE setting.')

        if not request.tenant:
            return False

        # Tenant owner has all permissions
        if request.tenant.owner_id == request.user.pk:
            return True

        if not request.tenant_member:
            return False

        assigned_perms = request.tenant_member.get_all_permissions()
        return has_permission(required_perm, assigned_perms)

    @staticmethod
    def get_scopes_permissions(token):
        if hasattr(token, 'scope') and token.scope:
            scopes = token.scope.split(' ')
        elif hasattr(token, 'scopes'):
            scopes = token.scopes
        elif hasattr(token, 'get_scopes'):
            scopes = token.get_scopes()
        else:
            scopes = []

        if not scopes:
            return

        return perm_registry.get_permissions_for_scopes(scopes)


class HasResourcePermissionOrReadOnly(HasResourcePermission):
    """The authenticated user has the tenant permission, or is a read-only request."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().has_permission(request, view)
