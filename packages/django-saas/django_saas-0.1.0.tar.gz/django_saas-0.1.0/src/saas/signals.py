from django.dispatch import Signal

from saas.identity.signals import (
    after_login_user,
    after_signup_user,
    invitation_accepted,
    invitation_created,
    member_invited,
)

before_create_tenant = Signal()
before_update_tenant = Signal()
confirm_destroy_tenant = Signal()

mail_queued = Signal()

__all__ = [
    'before_create_tenant',
    'before_update_tenant',
    'confirm_destroy_tenant',
    'after_signup_user',
    'after_login_user',
    'mail_queued',
    'invitation_created',
    'invitation_accepted',
    'member_invited',
]
