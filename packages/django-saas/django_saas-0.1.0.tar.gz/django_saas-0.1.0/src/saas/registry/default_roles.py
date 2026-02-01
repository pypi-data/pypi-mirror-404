from .registry import perm_registry

# 1. Define Core Roles
perm_registry.register_role('ADMIN', 'Administrator', 'Staff management access')
perm_registry.register_role('MEMBER', 'Member', 'Regular access')

# 2. Register Permissions
perm_registry.assign_to_role('ADMIN', 'iam.*')
perm_registry.assign_to_role('ADMIN', 'org.*')
perm_registry.assign_to_role('MEMBER', 'iam.*.view')
perm_registry.assign_to_role('MEMBER', 'org.*.view')
