from typing import Type

from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from saas.db import CachedManager


class TenantManager(CachedManager):
    natural_key = ['slug']

    def get_by_slug(self, slug: str):
        return self.get_from_cache_by_natural_key(slug)


class AbstractTenant(models.Model):
    name = models.CharField(max_length=140)
    logo = models.URLField(blank=True, null=True)
    slug = models.SlugField(
        unique=True,
        help_text='Identity of the tenant, e.g. <slug>.example.com',
    )
    environment = models.CharField(max_length=48, blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)

    objects = TenantManager()

    class Meta:
        verbose_name = _('tenant')
        verbose_name_plural = _('tenants')
        abstract = True

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.slug,)

    def active(self):
        """For django-tenants compatibility"""
        pass


class Tenant(AbstractTenant):
    objects = TenantManager()

    class Meta(AbstractTenant.Meta):
        swappable = 'SAAS_TENANT_MODEL'
        db_table = 'saas_tenant'
        ordering = ['created_at']


def get_tenant_model() -> Type[Tenant]:
    return apps.get_model(settings.SAAS_TENANT_MODEL)
