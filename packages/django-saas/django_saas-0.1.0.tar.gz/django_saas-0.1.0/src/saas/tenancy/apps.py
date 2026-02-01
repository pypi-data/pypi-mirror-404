from django.apps import AppConfig


class TenancyConfig(AppConfig):
    name = 'saas.tenancy'
    label = 'saas_tenancy'
    verbose_name = 'SaaS Tenancy'

    def ready(self):
        from saas.tenancy._ready import setup_member_cache_invalidation

        setup_member_cache_invalidation()
