from __future__ import annotations

import hashlib
from urllib.parse import urlencode


def gen_gravatar_url(email: str, name: str | None = None, **params):
    email_sha = hashlib.sha256(email.encode('utf-8')).hexdigest()
    url = f'https://gravatar.com/avatar/{email_sha}'
    if name:
        params.update({'d': 'initials', 'name': name})
    params.setdefault('s', 200)
    return f'{url}?{urlencode(params)}'
