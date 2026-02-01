from __future__ import annotations

import functools
import json
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from joserfc import jwe
from joserfc.errors import JoseError
from joserfc.jwk import OKPKey

DEFAULT_JWE_HEADER = {'alg': 'ECDH-ES+A256KW', 'enc': 'A128CBC-HS256'}


@functools.cache
def derive_key(secret: str) -> OKPKey:
    """Derive an X25519 key from a secret string and cache the result."""
    return OKPKey.derive_key(secret, 'X25519')


def encrypt_data(value: bytes) -> str:
    master_key = derive_key(settings.SECRET_KEY)
    header = getattr(settings, 'SAAS_JWE_HEADER', DEFAULT_JWE_HEADER)
    return jwe.encrypt_compact(
        header,
        plaintext=value,
        public_key=master_key,
    )


def decrypt_data(value: str) -> bytes | None:
    keys = [settings.SECRET_KEY] + settings.SECRET_KEY_FALLBACKS
    for key in keys:
        try:
            obj = jwe.decrypt_compact(value, private_key=derive_key(key))
            return obj.plaintext
        except JoseError:
            continue
    return None


@functools.cache
def load_secrets():
    secrets_file = getattr(settings, 'SAAS_SECRETS_FILE', None)
    if not secrets_file:
        raise ImproperlyConfigured('SAAS_SECRETS_FILE setting is not set')

    if not os.path.exists(secrets_file):
        return {}

    with open(secrets_file, 'r') as f:
        content = f.read().strip()

    if not content:
        return {}

    decrypted = decrypt_data(content)
    if decrypted is None:
        raise ImproperlyConfigured(f'Failed to decrypt secrets file: {secrets_file}')

    return json.loads(decrypted.decode('utf-8'))


def resolve_secret(key: str) -> str | None:
    if key.startswith('secret:'):
        return load_secrets()[key[7:]]
    return key
