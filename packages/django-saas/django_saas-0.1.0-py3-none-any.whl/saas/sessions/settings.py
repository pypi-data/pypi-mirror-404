from django.core.signals import setting_changed

from saas.settings import BaseSettings


class SessionSettings(BaseSettings):
    SETTINGS_KEY = 'SAAS_SESSIONS'
    DEFAULT_SETTINGS = {
        'LOCATION_RESOLVER': {
            'backend': 'saas.sessions.location.cloudflare.CloudflareBackend',
        },
        'SESSION_RECORD_INTERVAL': 300,
    }
    IMPORT_SETTINGS = [
        'LOCATION_RESOLVER',
    ]


session_settings = SessionSettings()
setting_changed.connect(session_settings.listen_setting_changed)
