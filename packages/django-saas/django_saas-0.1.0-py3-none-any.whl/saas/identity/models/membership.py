from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Membership(models.Model):
    tenant = models.ForeignKey(settings.SAAS_TENANT_MODEL, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    role = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _('membership')
        verbose_name_plural = _('memberships')
        unique_together = [
            ['tenant', 'user'],
        ]
        ordering = ['-created_at']
        db_table = 'saas_identity_membership'

    def __str__(self):
        return str(self.user)

    def natural_key(self):
        return self.tenant_id, self.user_id
