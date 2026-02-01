from django.apps import AppConfig


class DemoConfig(AppConfig):
    name = 'tests.demo_app'

    def ready(self):
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules('event_hooks')
