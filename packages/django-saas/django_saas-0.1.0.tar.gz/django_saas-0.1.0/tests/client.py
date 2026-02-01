import json
import os
import re
from urllib.parse import parse_qs, urlparse

from django.core import mail
from django.core.cache import cache
from requests_mock import Mocker

from saas.test import SaasTestCase

ROOT = os.path.dirname(__file__)


class FixturesTestCase(SaasTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    @staticmethod
    def get_mail_auth_code():
        msg = mail.outbox[0]
        codes = re.findall(r'Code: (\w{6})', msg.body)
        return codes[0]

    @staticmethod
    def load_fixture(name: str):
        filename = os.path.join(ROOT, 'fixtures', name)
        with open(filename) as f:
            if filename.endswith('.json'):
                data = json.load(f)
            else:
                data = f.read()
        return data

    @classmethod
    def mock_requests(cls, *names: str):
        m = Mocker()
        for name in names:
            data = cls.load_fixture(name)
            m.register_uri(**data)
        return m

    def resolve_url_params(self, url: str) -> dict[str, str]:
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        location = resp.get('Location')
        params = parse_qs(urlparse(location).query)
        return {k: v[0] for k, v in params.items()}
