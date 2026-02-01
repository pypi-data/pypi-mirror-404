import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    session_key = models.CharField(max_length=40)
    user_agent = models.TextField()
    expiry_date = models.DateTimeField()
    location = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'session_key')
        db_table = 'saas_user_session'
        ordering = ('-last_used',)
