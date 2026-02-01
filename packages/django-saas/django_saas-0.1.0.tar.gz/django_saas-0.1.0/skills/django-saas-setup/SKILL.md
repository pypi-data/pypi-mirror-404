---
name: django-saas-setup
description: Bootstraps and configures django-saas in a new or existing Django project. Use when the user wants to "setup a new saas project", "install django-saas", or "initialize multi-tenancy".
---

# django-saas-setup

This skill guides you through the initial setup of `django-saas` in a Django project.

## Workflow

1.  **Installation**: Ensure `django-saas` and its dependencies are installed.
    ```bash
    pip install django-saas
    ```
2.  **Settings Configuration**: Update `settings.py` with the required Apps, Middlewares, and Auth Backends.
    - Refer to `references/settings_snippets.py` for standard configurations.
    - Ensure `AUTHENTICATION_BACKENDS` includes both `ModelBackend` and `UserIdentityBackend`.
    - Place `TenantMiddleware` *after* session and auth middlewares.
3.  **URL Routing**: Include the root SaaS URLs in your project's `urls.py`.
    ```python
    from django.urls import include, path
    urlpatterns = [
        path('api/', include('saas.api_urls')),
        path('sso/', include('saas.sso.auth_urls')),
    ]
    ```
4.  **Database Setup**: Run migrations to create the base tables.
    ```bash
    python manage.py migrate
    ```
5.  **Initial Data**: (Optional) Register default roles and permissions if needed using the `perm_registry`.

## References

- `references/settings_snippets.py`: Pre-configured dictionary snippets for project settings.

## Best Practices

- **Security**: Never hardcode client secrets in `settings.py`. Use environment variables or a secrets manager.
- **Tenant Discovery**: Choose the primary discovery method (Header, Path, or Session) and ensure the corresponding middleware is configured.
- **Customization**: If the default `Tenant` model isn't sufficient, define a custom one and set `SAAS_TENANT_MODEL` in settings.