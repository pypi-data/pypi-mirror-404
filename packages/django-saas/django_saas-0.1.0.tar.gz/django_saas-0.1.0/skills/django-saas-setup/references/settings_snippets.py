# --- INSTALLED_APPS ---
INSTALLED_APPS = [
    # ...
    'saas',
    'saas.identity',
    'saas.tenancy',
    'saas.sessions',
    'saas.tokens',
    'saas.domain',
    'saas.sso',
    'saas.drf',
]

# --- AUTHENTICATION_BACKENDS ---
AUTHENTICATION_BACKENDS = [
    'saas.identity.backends.ModelBackend',
    'saas.sso.backends.UserIdentityBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# --- MIDDLEWARE ---
# Must include TenantMiddleware and SessionRecordMiddleware
MIDDLEWARE = [
    # ... django defaults ...
    'saas.middleware.HeaderTenantIdMiddleware',
    'saas.middleware.PathTenantIdMiddleware',
    'saas.middleware.SessionTenantIdMiddleware',
    'saas.middleware.TenantMiddleware',
    'saas.sessions.middleware.SessionRecordMiddleware',
]

# --- SAAS CONFIG ---
SAAS = {
    'MAX_USER_TENANTS': 10,
    'TENANT_ID_HEADER': 'X-Tenant-Id',
}

SAAS_IDENTITY = {
    'ENABLE_GRAVATAR': True,
}

SAAS_SSO = {
    'PROVIDERS': [
        {
            'backend': 'saas.sso.providers.GoogleProvider',
            'options': {
                'client_id': '...',
                'client_secret': '...',
            },
        },
    ]
}
