from django.utils.translation import gettext_lazy as _

from saas.registry import Severity, perm_registry

# User Profile
perm_registry.register_permission(
    key='user.profile.view',
    label=_('View Profile'),
    module='User',
    description=_('Read access to basic profile details (name, avatar, bio)'),
    severity=Severity.LOW,
)
perm_registry.register_permission(
    key='user.profile.update',
    label=_('Update Profile'),
    module='User',
    description=_('Write access to update own profile details'),
    severity=Severity.NORMAL,
)

# User Emails
perm_registry.register_permission(
    key='user.email.view',
    label=_('View Emails'),
    module='User',
    description=_('List all registered email addresses'),
    severity=Severity.LOW,
)
perm_registry.register_permission(
    key='user.email.manage',
    label=_('Manage Emails'),
    module='User',
    description=_('Add, delete, or verify secondary email addresses'),
    severity=Severity.NORMAL,
)

# User Tenants
perm_registry.register_permission(
    key='user.org.view',
    label=_('View Organizations'),
    module='User',
    description=_('List all organizations you belong to'),
    severity=Severity.LOW,
)
perm_registry.register_permission(
    key='user.org.create',
    label=_('Create Organizations'),
    module='User',
    description=_('Create new organizations'),
    severity=Severity.HIGH,
)
perm_registry.register_permission(
    key='user.org.join',
    label=_('Join Organizations'),
    module='User',
    description=_("Join any organization you're invited to"),
    severity=Severity.NORMAL,
)
perm_registry.register_permission(
    key='user.org.leave',
    label=_('Leave Organizations'),
    module='User',
    description=_('Leave any organization you belong to'),
    severity=Severity.HIGH,
)

# Organization Management
perm_registry.register_permission(
    key='org.info.view',
    label=_('View Organization'),
    module='Organization',
    description=_('View tenant settings and info'),
    severity=Severity.LOW,
)
perm_registry.register_permission(
    key='org.info.update',
    label=_('Update Organization'),
    module='Organization',
    description=_('Update tenant name, logo, etc.'),
    severity=Severity.NORMAL,
)
