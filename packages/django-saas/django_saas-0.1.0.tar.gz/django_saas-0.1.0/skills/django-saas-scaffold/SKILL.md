---
name: django-saas-scaffold
description: Scaffolds a new tenant-aware feature in a django-saas project. Use when the user wants to "add a new feature", "create a model scoped to a tenant", or "implement a new CRUD module".
---

# django-saas-scaffold

This skill helps you build new modules within a SaaS project using the `django-saas` library.

## Workflow

1.  **Identify Feature Scope**: Confirm if the feature belongs to an existing app or needs a new one.
2.  **App Setup**: If a new app is needed, run `python manage.py startapp <name>`. Register it in `INSTALLED_APPS` with a clear label (e.g., `myapp_features`).
3.  **Define Models**: Use the `assets/models.py.template` as a guide. Ensure every tenant-scoped model has a `tenant` ForeignKey to `settings.SAAS_TENANT_MODEL`.
4.  **Register Permissions**: Add permissions to `saas_permissions.py` in the app directory.
    ```python
    from saas.registry import perm_registry
    perm_registry.register_permission(key='app.feature.view', label='View Feature', module='App')
    ```
5.  **Implement Serializers**: Use `assets/serializers.py.template`. Exclude `tenant` from fields as it is handled by the view.
6.  **Implement Endpoints**: Use `assets/endpoints.py.template`. Inherit from `saas.drf.views.TenantEndpoint`.
7.  **Configure URLs**: Create `api_urls.py` in the app and include it in the root `src/saas/api_urls.py`.
8.  **Add Tests**: Create tests in `tests/` verifying tenant isolation (e.g., User A cannot see User B's tenant data).

## Assets

- `assets/models.py.template`: Boilerplate for tenant-scoped models.
- `assets/serializers.py.template`: Boilerplate for DRF serializers.
- `assets/endpoints.py.template`: Boilerplate for tenant-aware DRF views.
- `assets/api_urls.py.template`: Boilerplate for app-level URL routing.

## Guidelines

- **Isolation**: Always use `saas.drf.filters.TenantIdFilter` in list views.
- **Security**: Always protect views with `@resource_permission`.
- **Consistency**: Use `get_tenant_model()` when referring to tenants in code.