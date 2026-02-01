from django.apps import AppConfig


class TestsConfig(AppConfig):
    name = 'tests'

    def ready(self):
        from saas.registry import default_roles, default_scopes  # noqa
