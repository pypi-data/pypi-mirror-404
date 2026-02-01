from django.dispatch import receiver

from saas.domain.registry import default_roles  # noqa
from saas.registry import default_roles, default_scopes  # noqa
from saas.signals import confirm_destroy_tenant
from saas.tasks import receive_signals  # noqa


@receiver(confirm_destroy_tenant)
def confirm_destroy_tenant_handler(sender, tenant, **kwargs):
    tenant.delete()
