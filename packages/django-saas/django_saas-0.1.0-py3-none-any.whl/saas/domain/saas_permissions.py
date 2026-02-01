from django.utils.translation import gettext_lazy as _

from saas.registry import Severity, perm_registry

perm_registry.register_permission(
    key='security.domain.view',
    label=_('View Domain'),
    module='Security',
    description=_('Can view the list of custom domains and their verification status'),
    severity=Severity.NORMAL,
)
perm_registry.register_permission(
    key='security.domain.create',
    label=_('Add Domain'),
    module='Security',
    description=_('Can add new custom domains to the tenant'),
    severity=Severity.CRITICAL,
)
perm_registry.register_permission(
    key='security.domain.verify',
    label=_('Verify Domain'),
    module='Security',
    description=_('Can trigger DNS verification checks for domains'),
    severity=Severity.HIGH,
)
perm_registry.register_permission(
    key='security.domain.manage',
    label=_('Manage Domains'),
    module='Security',
    description=_('Can re-add domain and change the primary domain'),
    severity=Severity.CRITICAL,
)
perm_registry.register_permission(
    key='security.domain.delete',
    label=_('Delete a Domain'),
    module='Security',
    description=_('Can delete a domain from the tenant'),
    severity=Severity.CRITICAL,
)
