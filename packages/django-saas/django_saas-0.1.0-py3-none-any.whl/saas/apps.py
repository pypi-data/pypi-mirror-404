from django.apps import AppConfig
from django.conf import settings

if not hasattr(settings, 'SAAS_TENANT_MODEL'):
    setattr(settings, 'SAAS_TENANT_MODEL', 'saas.Tenant')


class CoreConfig(AppConfig):
    name = 'saas'
    verbose_name = 'SaaS'

    def ready(self):
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules('saas_permissions')

        # check if TenantMiddleware is in use
        middleware = getattr(settings, 'MIDDLEWARE', [])
        if 'saas.middleware.TenantMiddleware' not in middleware:
            import warnings

            warnings.warn(
                'TenantMiddleware is not found in MIDDLEWARE. It is required for saas to function properly.',
                RuntimeWarning,
            )
