from django.utils.translation import gettext_lazy as _

from .registry import perm_registry

# Special default role
perm_registry.register_role('OWNER', _('Owner'), _('Full organization access'))
perm_registry.assign_to_role('OWNER', '*')
