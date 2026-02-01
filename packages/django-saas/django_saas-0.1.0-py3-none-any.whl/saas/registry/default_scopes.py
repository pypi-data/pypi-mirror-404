from .registry import perm_registry

perm_registry.register_scope(
    key='openid',
    label='OpenID',
    permissions=[],  # Mandatory for OIDC, used as an auth flag
    is_oidc=True,
    description='Standard OIDC identifier',
)
perm_registry.register_scope(
    key='profile',
    label='Profile Information',
    permissions=['user.profile.view'],
    is_oidc=True,
    description='Access to your name, nickname, and picture',
)
perm_registry.register_scope(
    key='email',
    label='Email Address',
    permissions=['user.email.view'],
    is_oidc=True,
    description='Access to your primary and secondary emails',
)

perm_registry.register_scope(
    key='user:read',
    label='Read User Account',
    permissions=['user.*.view'],
    description='Read-only access to all personal account data',
)

perm_registry.register_scope(
    key='user:write',
    label='Manage User Account',
    permissions=[
        'user.*.update',
        'user.*.manage',
    ],
    description='Full write access to profile and secondary security settings',
)

perm_registry.register_scope(
    key='user',
    label='Full Personal Access',
    permissions=['user.*'],
    description='Complete control over personal global resources',
)

perm_registry.register_scope(
    key='org:read',
    label='Read Organization',
    permissions=['org.*.view'],
    description='Read-only access to organization settings',
)

perm_registry.register_scope(
    key='org:write',
    label='Manage Organization',
    permissions=['org.*.update'],
    description='Full write access to organization settings',
)

perm_registry.register_scope(
    key='org',
    label='Full Organization Access',
    permissions=['org.*'],
    description='Complete control over organization resources',
)
