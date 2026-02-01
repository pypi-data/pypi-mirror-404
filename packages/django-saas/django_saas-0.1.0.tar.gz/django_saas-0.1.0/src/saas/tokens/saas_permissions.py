from django.utils.translation import gettext_lazy as _

from saas.registry import Severity, perm_registry

perm_registry.register_permission(
    key='user.token.view',
    label=_('View Tokens'),
    module='User',
    description=_('List all API tokens for the user'),
    severity=Severity.NORMAL,
)

perm_registry.register_permission(
    key='user.token.manage',
    label=_('Manage Tokens'),
    module='User',
    description=_('Add, update, delete any API tokens for the user'),
    severity=Severity.CRITICAL,
)
