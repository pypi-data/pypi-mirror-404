import datetime

from django.utils import timezone

from saas.identity.settings import identity_settings


def set_invitation_expires_at():
    return timezone.now() + datetime.timedelta(days=identity_settings.INVITATION_EXPIRES_DAYS)
