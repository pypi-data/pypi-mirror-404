from django.apps import AppConfig


class IdentityConfig(AppConfig):
    name = 'saas.identity'
    label = 'saas_identity'
    verbose_name = 'SaaS Core'

    def ready(self):
        from saas.identity._ready import setup_user_email_cache_invalidation

        setup_user_email_cache_invalidation()
