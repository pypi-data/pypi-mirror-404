from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from saas.db import CachedManager
from saas.registry import perm_registry

from .group import Group


class TenantMemberManager(CachedManager['Member']):
    natural_key = ['tenant_id', 'user_id']
    query_select_related = ['user']
    query_prefetch_related = ['groups']

    def get_by_natural_key(self, tenant_id, user_id) -> 'Member':
        return self.get_from_cache_by_natural_key(tenant_id, user_id)


class Member(models.Model):
    tenant = models.ForeignKey(settings.SAAS_TENANT_MODEL, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    role = models.CharField(max_length=50, blank=True, null=True)
    groups = models.ManyToManyField(Group, blank=True)
    permissions = models.JSONField(default=list)
    objects = TenantMemberManager()

    class Meta:
        verbose_name = _('member')
        verbose_name_plural = _('members')
        unique_together = [
            ['tenant', 'user'],
        ]
        ordering = ['-created_at']
        db_table = 'saas_tenancy_member'

    def __str__(self):
        return str(self.user)

    def natural_key(self):
        return self.tenant_id, self.user_id

    @cached_property
    def group_permissions(self) -> list[str]:
        return list(self.__get_group_permissions())

    @cached_property
    def role_permissions(self) -> list[str]:
        return self.__get_role_permissions()

    @cached_property
    def user_permissions(self) -> list[str]:
        return self.__get_user_permissions()

    def get_all_permissions(self) -> set[str]:
        perms = set()
        perms = perms.union(self.user_permissions)
        perms = perms.union(self.role_permissions)
        perms = perms.union(self.group_permissions)
        return perms

    def __get_group_permissions(self):
        perms = set([])
        queryset = self.groups.values('permissions')
        for data in queryset:
            perms.update(data['permissions'])
        return perms

    def __get_role_permissions(self):
        if self.role:
            role = perm_registry.get_role(self.role)
            if role:
                return role.permissions
        return []

    def __get_user_permissions(self):
        return self.permissions
