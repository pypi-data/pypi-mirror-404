import typing as t

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from saas.db import CachedManager

__all__ = ['Domain', 'DomainManager']


class DomainManager(CachedManager['Domain']):
    natural_key = ['hostname']

    def get_by_natural_key(self, hostname: str):
        return self.get_from_cache_by_natural_key(hostname)

    def get_tenant_id(self, hostname: str) -> t.Optional[t.Any]:
        try:
            instance = self.get_by_natural_key(hostname)
            return instance.tenant_id
        except self.model.DoesNotExist:
            return None


class Domain(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(settings.SAAS_TENANT_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=100)
    hostname = models.CharField(max_length=255, unique=True)
    primary = models.BooleanField(default=False)
    verified = models.BooleanField(default=False, editable=False)
    ssl = models.BooleanField(default=False, editable=False)
    active = models.BooleanField(default=False, editable=False)
    instrument_id = models.CharField(max_length=256, null=True, blank=True, editable=False)
    instrument = models.JSONField(blank=True, null=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    objects = DomainManager()

    class Meta:
        verbose_name = _('domain')
        verbose_name_plural = _('domains')
        ordering = ['created_at']
        db_table = 'saas.domain'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant'], condition=models.Q(primary=True), name='ux_tenant_primary_domain'
            )
        ]

    def __str__(self):
        return self.hostname

    @property
    def base_url(self) -> str:
        if self.ssl:
            return f'https://{self.hostname}'
        return f'http://{self.hostname}'

    def natural_key(self):
        return (self.hostname,)

    def disable(self):
        self.verified = False
        self.active = False
        self.ssl = False
        self.instrument = None
        self.save()
