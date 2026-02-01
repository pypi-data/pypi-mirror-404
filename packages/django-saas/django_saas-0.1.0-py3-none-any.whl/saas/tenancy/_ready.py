from django.db.models.signals import post_save
from django.dispatch import receiver

from saas.identity.models import Membership
from saas.tenancy.models import Member


def setup_member_cache_invalidation():
    Member.objects.setup_related_cache_invalidation()


@receiver(post_save, sender=Membership)
def sync_membership_role(sender, instance: Membership, *args, **kwargs):
    # enter tenant connection
    instance.tenant.active()
    Member.objects.update_or_create(
        tenant_id=instance.tenant_id,
        user_id=instance.user_id,
        defaults={'role': instance.role},
    )
