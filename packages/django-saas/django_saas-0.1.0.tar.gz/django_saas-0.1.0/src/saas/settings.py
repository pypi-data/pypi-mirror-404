from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.signals import setting_changed
from django.utils.module_loading import import_string


class BaseSettings:
    SETTINGS_KEY: str = 'SAAS'
    DEFAULT_SETTINGS: dict[str, Any] = {}
    IMPORT_SETTINGS: list[str] = []

    def __init__(self):
        self._user_settings = None

    @property
    def settings_key(self):
        return self.SETTINGS_KEY

    @property
    def defaults(self):
        return self.DEFAULT_SETTINGS

    @property
    def user_settings(self):
        if self._user_settings is None:
            self._user_settings = getattr(settings, self.settings_key, {})
        return self._user_settings

    def __getitem__(self, attr):
        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]
        return val

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid %s setting: '%s'" % (self.settings_key, attr))

        val = self[attr]

        # Coerce import strings into classes
        if attr in self.IMPORT_SETTINGS:
            val = perform_import(val)

        return val

    def reload(self):
        self._user_settings = None

    def listen_setting_changed(self, setting, **kwargs):
        if setting == self.settings_key:
            self.reload()


class Settings(BaseSettings):
    DEFAULT_SETTINGS = {
        'SITE': {
            'name': 'Django SaaS',
            'url': 'https://django-saas.dev',
            'icon': '',
            'copyright': '© 2025',
        },
        'CLIENT_IP_HEADERS': None,
        'DB_CACHE_ALIAS': 'default',
        'DEFAULT_FROM_EMAIL': None,
        'TENANT_ID_HEADER': 'X-Tenant-Id',
        'MAX_USER_TENANTS': 10,
    }


def perform_import_provider(data):
    backend_cls = import_string(data['backend'])
    options = data.get('options', {})
    return backend_cls(**options)


def perform_import(val):
    if val is None:
        return None

    elif isinstance(val, (list, tuple)):
        return [perform_import_provider(item) for item in val]
    elif isinstance(val, dict) and 'backend' not in val:
        return {k: perform_import_provider(val[k]) for k in val}
    else:
        return perform_import_provider(val)


saas_settings = Settings()
setting_changed.connect(saas_settings.listen_setting_changed)
