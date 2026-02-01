from unittest.mock import Mock

from rest_framework.settings import api_settings

from saas.settings import saas_settings
from saas.utils.ipware import get_client_ip


def test_get_client_ip_remote_addr():
    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {}

    assert get_client_ip(request) == '127.0.0.1'


def test_get_client_ip_x_forwarded_for():
    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {'X-Forwarded-For': '10.0.0.1'}

    assert get_client_ip(request) == '10.0.0.1'


def test_get_client_ip_custom_headers():
    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {'Custom-Header': '10.0.0.2'}

    assert get_client_ip(request, ip_headers=['Custom-Header']) == '10.0.0.2'


def test_get_client_ip_settings_headers(monkeypatch):
    monkeypatch.setattr(saas_settings, 'CLIENT_IP_HEADERS', ['My-IP'])

    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {'My-IP': '10.0.0.3'}

    assert get_client_ip(request) == '10.0.0.3'


def test_get_client_ip_proxied_no_num_proxies(monkeypatch):
    monkeypatch.setattr(api_settings, 'NUM_PROXIES', None)

    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {'X-Forwarded-For': '10.0.0.1, 10.0.0.2'}

    # When NUM_PROXIES is None, it returns the joined string without spaces
    assert get_client_ip(request) == '10.0.0.1,10.0.0.2'


def test_get_client_ip_proxied_with_num_proxies(monkeypatch):
    monkeypatch.setattr(api_settings, 'NUM_PROXIES', 1)

    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {'X-Forwarded-For': '10.0.0.1, 10.0.0.2'}

    # With NUM_PROXIES=1, it should take the last one
    assert get_client_ip(request) == '10.0.0.2'


def test_get_client_ip_proxied_with_num_proxies_2(monkeypatch):
    monkeypatch.setattr(api_settings, 'NUM_PROXIES', 2)

    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {'X-Forwarded-For': '10.0.0.1, 10.0.0.2, 10.0.0.3'}

    # With NUM_PROXIES=2, it should take the second to last
    assert get_client_ip(request) == '10.0.0.2'


def test_get_client_ip_proxied_zero_proxies(monkeypatch):
    monkeypatch.setattr(api_settings, 'NUM_PROXIES', 0)

    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.headers = {'X-Forwarded-For': '10.0.0.1, 10.0.0.2'}

    # With NUM_PROXIES=0, it should return REMOTE_ADDR
    assert get_client_ip(request) == '127.0.0.1'


def test_get_client_ip_priority():
    request = Mock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    # X-Forwarded-For is before X-Real-IP in default list
    request.headers = {
        'X-Real-IP': '10.0.0.2',
        'X-Forwarded-For': '10.0.0.1',
    }

    assert get_client_ip(request) == '10.0.0.1'
