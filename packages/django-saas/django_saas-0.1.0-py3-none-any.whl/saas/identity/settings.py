from __future__ import annotations

from django.core.signals import setting_changed

from saas.settings import BaseSettings


class IdentitySettings(BaseSettings):
    SETTINGS_KEY: str = 'SAAS_IDENTITY'
    DEFAULT_SETTINGS = {
        'LOGIN_URL': '',
        'SIGNUP_URL': '',
        'ENABLE_GRAVATAR': False,
        'GRAVATAR_PARAMS': {'d': 'identicon', 'r': 'g', 's': 200},
        'LOGIN_SECURITY_RULES': [],
        'SIGNUP_SECURITY_RULES': [],
        'RESET_PASSWORD_SECURITY_RULES': [],
        'SIGNUP_REQUEST_CREATE_USER': False,
        'INVITATION_ACCEPT_URL': '',
        'INVITATION_EXPIRES_DAYS': 7,
    }
    IMPORT_SETTINGS = [
        'LOGIN_SECURITY_RULES',
        'SIGNUP_SECURITY_RULES',
        'RESET_PASSWORD_SECURITY_RULES',
    ]


identity_settings = IdentitySettings()
setting_changed.connect(identity_settings.listen_setting_changed)
