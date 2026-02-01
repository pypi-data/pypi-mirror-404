from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile',
    )
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    region = models.CharField(blank=True, null=True, max_length=4)
    locale = models.CharField(blank=True, null=True, max_length=10)
    timezone = models.CharField(max_length=50, default='UTC', help_text="e.g., 'America/New_York'")

    class Meta:
        db_table = 'saas_user_profile'
