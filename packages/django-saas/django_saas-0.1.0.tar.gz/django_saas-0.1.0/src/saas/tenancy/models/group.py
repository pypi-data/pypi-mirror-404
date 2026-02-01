from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Group(models.Model):
    tenant = models.ForeignKey(settings.SAAS_TENANT_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, db_index=True)
    permissions = models.JSONField(default=list)
    managed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        unique_together = [['tenant', 'name']]
        db_table = 'saas_tenancy_group'
        ordering = ['created_at']

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.tenant_id, self.name
