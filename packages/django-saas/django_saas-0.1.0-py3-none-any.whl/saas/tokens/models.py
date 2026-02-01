from django.conf import settings
from django.db import models
from django.utils import timezone

from .settings import token_settings


class UserToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='+',
    )
    tenant = models.ForeignKey(
        settings.SAAS_TENANT_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name='+',
    )
    name = models.CharField(max_length=48)
    key = models.CharField(unique=True, max_length=48, default=token_settings.generate_token, editable=False)
    scope = models.TextField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'saas_user_token'
        ordering = ('-created_at',)

    def __str__(self):
        return f'UserToken<{self.name}>'

    @property
    def is_expired(self):
        return self.expires_at and self.expires_at < timezone.now()
