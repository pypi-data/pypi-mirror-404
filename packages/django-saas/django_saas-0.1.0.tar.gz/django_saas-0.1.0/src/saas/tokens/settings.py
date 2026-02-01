from functools import cached_property

from django.core.signals import setting_changed
from django.utils.module_loading import import_string

from saas.settings import BaseSettings


class TokenSettings(BaseSettings):
    SETTINGS_KEY = 'SAAS_TOKENS'
    DEFAULT_SETTINGS = {
        'TOKEN_KEY_GENERATOR': 'saas.utils.token.gen_token_key',
        'USER_TOKEN_RECORD_INTERVAL': 300,
    }

    @cached_property
    def generate_token(self):
        return import_string(self.TOKEN_KEY_GENERATOR)


token_settings = TokenSettings()
setting_changed.connect(token_settings.listen_setting_changed)
