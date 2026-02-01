from django.core.cache import BaseCache, caches
from django.utils.connection import ConnectionProxy

from ..settings import saas_settings

cache: BaseCache = ConnectionProxy(caches, saas_settings.DB_CACHE_ALIAS)  # type: ignore[assignment]


__all__ = ['cache']
