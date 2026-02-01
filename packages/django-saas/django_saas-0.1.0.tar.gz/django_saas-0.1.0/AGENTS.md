# Project Context for AI Agents

## Project Overview

**Name**: django-saas
**Description**: A modular foundation for building multi-tenant SaaS products with Django.

## Tech Stack

- **Language**: Python 3.12+
- **Framework**: Django (5.0+)
- **API**: Django Rest Framework (DRF)
- **Permissions**: Custom Registry-based RBAC
- **SSO**: OAuth2/OpenID Connect (Google, GitHub, Apple)

## Project Structure

### Core Apps (`src/saas`)

- **`saas`**: Core multi-tenancy primitives. Contains the `Tenant` model and middleware.
- **`saas.identity`**: User identity, emails, profiles, invitations, and authentication (Password/SSO).
- **`saas.tenancy`**: Tenant-level organization (Members, Groups, Roles).
- **`saas.sso`**: SSO Provider implementations and OAuth2 flow handling.
- **`saas.domain`**: Custom domain management and verification.
- **`saas.tokens`**: Personal Access Tokens (PAT) for API access.
- **`saas.sessions`**: User session tracking and management.
- **`saas.drf`**: DRF enhancements (filters, permissions, view bases).

### Key Files

- `src/saas/models.py`: Root `Tenant` model.
- `src/saas/api_urls.py`: Main API routing entry point.
- `src/saas/registry/`: Permission and Role management.
- `src/saas/settings.py`: Core settings and base classes.

## Core Concepts

### 1. Multi-Tenancy
- **Tenant**: The organizational unit. A user can belong to multiple tenants.
- **Tenant Discovery**: Handled by middleware using:
  - `HTTP_HEADER`: `X-Tenant-Id`
  - `Path`: `/tenant/<id>/...`
  - `Session`: `request.session['tenant_id']`
- **Active Tenant**: Access via `request.tenant` and `request.tenant_id`.

### 2. Identity vs Tenancy
- **Identity**: Global user data (`User`, `UserEmail`, `UserProfile`).
- **Tenancy**: Relation between User and Tenant (`Member`, `Group`).

### 3. RBAC & Registry
- **Permissions**: Registered globally via `perm_registry.register_permission(key, ...)`.
- **Roles**: Logical sets of permissions (e.g., `ADMIN`, `MEMBER`).
- **Groups**: Tenant-specific collections of members with shared permissions.
- **Checking**: Use `@resource_permission('key')` on DRF views.

## Common AI Tasks

### Creating a New Feature
1.  **Define Models**: If it's tenant-specific, include a `tenant = models.ForeignKey(settings.SAAS_TENANT_MODEL, ...)`.
2.  **Register Permissions**: Create or update `saas_permissions.py` in your app.
    ```python
    from saas.registry import perm_registry
    perm_registry.register_permission(key='myapp.feature.view', label='View Feature', module='MyApp')
    ```
3.  **Implement Serializers**: Inherit from `rest_framework.serializers.ModelSerializer`.
4.  **Implement Endpoints**: Use `saas.drf.views.TenantEndpoint` for tenant-scoped data.
5.  **Expose URLs**: Add to the app's `api_urls.py` and include in `src/saas/api_urls.py`.

### Protecting an API
Use the `resource_permission` decorator:
```python
from saas.drf.decorators import resource_permission
from saas.drf.views import TenantEndpoint

class MyEndpoint(TenantEndpoint):
    @resource_permission('myapp.feature.view')
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
```

### Filtering by Tenant
For DRF views, use `TenantIdFilter`:
```python
from saas.drf.filters import TenantIdFilter

class MyListEndpoint(ListModelMixin, TenantEndpoint):
    filter_backends = [TenantIdFilter]
```

## Rules for AI Agents

1.  **Code Style**: 
    - Use single quotes `'` for strings.
    - Max line length 120.
    - `from __future__ import annotations` in all Python files.
2.  **Modularity**:
    - Keep app-specific logic inside the respective sub-app (`identity`, `tenancy`, etc.).
    - Use app-specific `settings.py` and `signals.py`.
3.  **Consistency**:
    - Use `get_user_model()` and `get_tenant_model()`.
    - Follow the established naming patterns for endpoints and serializers.
4.  **Testing**:
    - Always add tests in `tests/<app>/`.
    - Run with `uv run pytest`.