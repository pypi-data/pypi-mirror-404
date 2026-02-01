from django.conf import settings
from django.db import models

from saas.db.fields import EncryptedField


class UserSecret(models.Model):
    secret_key = EncryptedField(null=True, blank=True)


class TenantSecret(models.Model):
    tenant = models.ForeignKey(settings.SAAS_TENANT_MODEL, on_delete=models.CASCADE)
    secret_key = EncryptedField(null=True, blank=True)
