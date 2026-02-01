from django.utils.translation import gettext_lazy as _

from saas.registry import Severity, perm_registry

# Identity Management (IAM)
perm_registry.register_permission(
    key='iam.member.view',
    label=_('View Members'),
    module='IAM',
    description=_('List and view member details'),
    severity=Severity.LOW,
)
perm_registry.register_permission(
    key='iam.member.update',
    label=_('Manage Members'),
    module='IAM',
    description=_('Update member role status'),
    severity=Severity.HIGH,
)
perm_registry.register_permission(
    key='iam.member.invite',
    label=_('Invite member'),
    module='IAM',
    description=_('Invite new members to join the organization'),
    severity=Severity.HIGH,
)
perm_registry.register_permission(
    key='iam.member.delete',
    label=_('Remove Member'),
    module='IAM',
    description=_('Remove members from the organization'),
    severity=Severity.CRITICAL,
)
perm_registry.register_permission(
    key='iam.group.view',
    label=_('View Groups'),
    module='IAM',
    description=_('View tenant groups'),
    severity=Severity.LOW,
)
perm_registry.register_permission(
    key='iam.group.manage',
    label=_('Manage Groups'),
    module='IAM',
    description=_('Create or edit tenant-specific groups'),
    severity=Severity.NORMAL,
)
