import time

from django.core.cache import cache
from django.utils import timezone
from rest_framework.authentication import (
    TokenAuthentication as _TokenAuthentication,
)
from rest_framework.request import Request

from .models import UserToken
from .settings import token_settings


class TokenAuthentication(_TokenAuthentication):
    keyword = 'Bearer'
    model = UserToken

    def authenticate(self, request: Request):
        credentials = super().authenticate(request)
        if credentials is None:
            return None

        user, token = credentials
        if token.is_expired:
            return None

        if token.tenant_id:
            tenant_id = token.tenant_id
        else:
            tenant_id = getattr(request._request, 'tenant_id', None)
        request.tenant_id = tenant_id

        _cache_key = f'saas.tokens:token_last_used:{token.id}'
        last_used = cache.get(_cache_key, 0)
        now = int(time.time())
        if now - last_used > token_settings.USER_TOKEN_RECORD_INTERVAL:
            # track for 90 days. Cache missing is expensive than hit.
            cache.set(_cache_key, now, 90 * 86400)
            token.last_used_at = timezone.now()
            token.save()
        return user, token
