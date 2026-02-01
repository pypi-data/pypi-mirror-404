from django.apps import apps
from django.core.checks import Error, register
from django.db.models.signals import pre_delete

from saas.registry import perm_registry

from .models import Domain
from .providers import get_domain_provider


def remove_domain(sender, instance: Domain, **kwargs):
    provider = get_domain_provider(instance.provider)
    if provider:
        provider.remove_domain(instance)


pre_delete.connect(remove_domain, sender=Domain)


def register_checks():
    def check(app_configs, **kwargs):
        if not apps.is_installed('saas'):
            return [Error("'saas' must be in INSTALLED_APPS.")]
        else:
            return []

    register(check, 'saas')


def register_role_permissions():
    perm_registry.assign_to_role('ADMIN', 'security.domain.view')
    perm_registry.assign_to_role('ADMIN', 'security.domain.verify')
    perm_registry.assign_to_role('MEMBER', 'security.domain.view')
