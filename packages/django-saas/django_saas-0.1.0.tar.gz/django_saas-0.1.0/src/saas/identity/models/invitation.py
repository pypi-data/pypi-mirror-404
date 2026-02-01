from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from saas.db.defaults import set_invitation_expires_at

from .membership import Membership
from .user_email import UserEmail


class Invitation(models.Model):
    class InviteStatus(models.IntegerChoices):
        PENDING = 1, 'pending'
        SENT = 2, 'sent'
        ACCEPTED = 3, 'accepted'
        EXPIRED = 4, 'expired'
        DECLINED = 5, 'declined'

    tenant = models.ForeignKey(settings.SAAS_TENANT_MODEL, on_delete=models.CASCADE)
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    token = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    email = models.EmailField()
    role = models.CharField(max_length=50, blank=True, null=True)
    status = models.IntegerField(default=InviteStatus.PENDING, choices=InviteStatus.choices)
    expires_at = models.DateTimeField(default=set_invitation_expires_at)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = _('invitation')
        verbose_name_plural = _('invitations')
        unique_together = [
            ['tenant', 'email'],
        ]
        ordering = ['-created_at']
        db_table = 'saas_identity_invitation'

    def __str__(self):
        return self.email

    def is_expired(self) -> bool:
        if self.status == self.InviteStatus.EXPIRED:
            return True
        return timezone.now() > self.expires_at

    def belongs_to_user(self, user) -> bool:
        if self.email == user.email:
            return True

        try:
            user_email = UserEmail.objects.get_by_email(self.email)
            return user_email.verified and user_email.user_id == user.pk
        except UserEmail.DoesNotExist:
            return False

    def accept_invite(self, user):
        if Membership.objects.filter(user=user, tenant_id=self.tenant_id).exists():
            self.status = self.InviteStatus.ACCEPTED
            self.accepted_at = timezone.now()
            self.save()

        elif self.is_expired():
            self.status = self.InviteStatus.EXPIRED
            self.save()
        else:
            Membership.objects.create(
                tenant_id=self.tenant_id,
                user=user,
                role=self.role,
            )
            self.accepted_at = timezone.now()
            self.status = Invitation.InviteStatus.ACCEPTED
            self.save()
