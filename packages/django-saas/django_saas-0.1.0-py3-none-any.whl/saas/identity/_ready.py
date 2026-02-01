from django.db.models.signals import post_save
from django.dispatch import receiver

from saas.models import get_tenant_model

from .models import Membership, UserEmail

Tenant = get_tenant_model()


@receiver(post_save, sender=Tenant)
def ensure_owner_is_member(sender, instance: Tenant, created: bool, *args, **kwargs):
    if created:
        Membership.objects.get_or_create(
            tenant=instance,
            user_id=instance.owner_id,
            defaults={'role': 'OWNER'},
        )


def setup_user_email_cache_invalidation():
    UserEmail.objects.setup_related_cache_invalidation()
