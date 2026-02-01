TESTING = True
SECRET_KEY = 'django-insecure'
ALLOWED_HOSTS = ['*']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
TASKS = {
    'default': {
        'BACKEND': 'django.tasks.backends.immediate.ImmediateBackend',
    },
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ]
        },
    }
]
AUTHENTICATION_BACKENDS = [
    'saas.identity.backends.ModelBackend',
    'saas.sso.backends.UserIdentityBackend',
]
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'saas.middleware.HeaderTenantIdMiddleware',
    'saas.middleware.PathTenantIdMiddleware',
    'saas.middleware.SessionTenantIdMiddleware',
    'saas.middleware.TenantMiddleware',
    'saas.sessions.middleware.SessionRecordMiddleware',
]
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
    },
]
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'rest_framework',
    'drf_spectacular',
    'saas',
    'saas.identity',
    'saas.tenancy',
    'saas.sessions',
    'saas.tokens',
    'saas.domain',
    'saas.sso',
    'saas.drf',
    'tests.demo_app',
]
REST_FRAMEWORK = {
    'PAGE_SIZE': 10,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'saas.tokens.authentication.TokenAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_SCHEMA_CLASS': 'saas.drf.spectacular.AutoSchema',
}
SAAS_SSO = {
    'TRUST_EMAIL_VERIFIED': False,
    'AUTO_CREATE_USER': False,
    'AUTHORIZED_REDIRECT_URL': '',
    'PROVIDERS': [
        {
            'backend': 'saas.sso.providers.GoogleProvider',
            'options': {
                'client_id': 'google_client_id',
                'client_secret': 'google_client_secret',
            },
        },
        {
            'backend': 'saas.sso.providers.GitHubProvider',
            'options': {
                'client_id': 'github_client_id',
                'client_secret': 'github_client_secret',
            },
        },
        {
            'backend': 'saas.sso.providers.AppleProvider',
            'options': {
                'client_id': 'apple_client_id',
                'team_id': 'apple_team_id',
                'key_id': 'apple_key_id',
                'private_key_path': 'tests/fixtures/sso/apple_private_key.p8',
            },
        },
    ],
}
SAAS_DOMAIN = {
    'BLOCKED_DOMAINS': ['blocked.domain'],
    'PROVIDERS': {
        'null': {
            'backend': 'saas.domain.providers.NullProvider',
            'options': {},
        },
        'cloudflare': {
            'backend': 'saas.domain.providers.CloudflareProvider',
            'options': {'zone_id': '123', 'auth_key': 'auth-key', 'ignore_hostnames': ['localtest.me']},
        },
    },
}
USE_TZ = True
TIME_ZONE = 'UTC'
ROOT_URLCONF = 'tests.urls'

SAAS_SECRETS_FILE = 'tests/fixtures/saas_secrets'

SAAS = {
    'TENANT_ID_HEADER': 'X-Tenant-Id',
    'MAX_USER_TENANTS': 10,
}

SAAS_IDENTITY = {
    'LOGIN_URL': '/login/',
    'SIGNUP_URL': '/signup/',
}
