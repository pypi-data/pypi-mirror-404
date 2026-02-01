from django.utils.translation import gettext_lazy as _

from saas.registry import Severity, perm_registry

perm_registry.register_permission(
    key='user.session.view',
    label=_('View Sessions'),
    module='User',
    description=_('List all active sessions for the user'),
    severity=Severity.NORMAL,
)

perm_registry.register_permission(
    key='user.session.manage',
    label=_('Manage Sessions'),
    module='User',
    description=_('Delete any active sessions for the user'),
    severity=Severity.HIGH,
)
