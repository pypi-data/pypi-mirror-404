from saas.registry import perm_registry

perm_registry.assign_to_role('ADMIN', 'security.domain.view')
perm_registry.assign_to_role('MEMBER', 'security.domain.view')
