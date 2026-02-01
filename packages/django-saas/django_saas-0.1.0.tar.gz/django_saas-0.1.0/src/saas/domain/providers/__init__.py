from ..settings import domain_settings
from .base import BaseProvider
from .cloudflare import CloudflareProvider
from .null import NullProvider


def get_domain_provider(name: str):
    return domain_settings.PROVIDERS.get(name)


__all__ = [
    'get_domain_provider',
    'BaseProvider',
    'NullProvider',
    'CloudflareProvider',
]
