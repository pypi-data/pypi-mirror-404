from django.core.signals import setting_changed

from saas.settings import BaseSettings


class DomainSettings(BaseSettings):
    SETTINGS_KEY = 'SAAS_DOMAIN'
    DEFAULT_SETTINGS = {
        'TENANT_MAX_DOMAINS': 1,
        'SUPPORTED_PROVIDERS': [],
        'BLOCKED_DOMAINS': [],
        'PROVIDERS': {},
    }
    IMPORT_SETTINGS = [
        'PROVIDERS',
    ]

    def get_supported_providers(self):
        if self.SUPPORTED_PROVIDERS:
            return self.SUPPORTED_PROVIDERS
        return list(self.PROVIDERS.keys())


domain_settings = DomainSettings()
setting_changed.connect(domain_settings.listen_setting_changed)
