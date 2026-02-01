# Django SaaS

A modular foundation for building multi-tenant SaaS products with Django.

## Features

- **Multi-Tenancy**: Flexible tenant discovery (Header, Path, Session).
- **Identity & Authentication**: Robust user management with Password and SSO (Google, GitHub, Apple) support.
- **Organization & RBAC**: Tenant-level organization with Members, Groups, and a global Permission/Role registry.
- **Custom Domains**: Support for custom domain management and verification.
- **API First**: Enhanced DRF integration with tenant-aware filters and permissions.
- **Developer Tools**: Pre-configured SKILLs for AI-assisted development.

## Install

```bash
pip install django-saas
```

## Configuration

Add the required apps to your Django project's `settings.py`:

```python
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

AUTHENTICATION_BACKENDS = [
    'saas.identity.backends.ModelBackend',
    'saas.sso.backends.UserIdentityBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # SaaS Middlewares
    'saas.middleware.HeaderTenantIdMiddleware',
    'saas.middleware.PathTenantIdMiddleware',
    'saas.middleware.SessionTenantIdMiddleware',
    'saas.middleware.TenantMiddleware',
    'saas.sessions.middleware.SessionRecordMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'saas.tokens.authentication.TokenAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'saas.drf.spectacular.AutoSchema',
}
```

### URL Configuration

Include the SaaS URLs in your project's `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path('api/', include('saas.api_urls')),
    path('sso/', include('saas.sso.auth_urls')),
]
```

## Documentation for AI Agents

This project includes specialized context for AI developers. If you are using an AI assistant, point it to `AGENTS.md` and the `skills/` directory for automated workflows.

## License

BSD-3-Clause