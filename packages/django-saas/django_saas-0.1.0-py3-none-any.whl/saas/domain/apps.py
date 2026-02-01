from django.apps import AppConfig


class DomainConfig(AppConfig):
    name = 'saas.domain'
    label = 'saas_domain'
    verbose_name = 'SaaS Domain'

    def ready(self):
        from ._ready import register_checks

        register_checks()
