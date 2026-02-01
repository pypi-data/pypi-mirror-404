import typing as t

import requests

from saas.utils.secure import resolve_secret

from ..models import Domain
from ..types import InstrumentInfo, InstrumentRecord
from .base import BaseProvider


class CloudflareProvider(BaseProvider):
    TIMEOUT = 60
    DEFAULT_SSL_SETTINGS = {
        'method': 'txt',
        'type': 'dv',
        'wildcard': False,
        'settings': {
            'min_tls_version': '1.2',
        },
    }

    @property
    def base_url(self) -> str:
        zone_id = self.options['zone_id']
        return f'https://api.cloudflare.com/client/v4/zones/{zone_id}/'

    @property
    def auth_key(self):
        return resolve_secret(self.options['auth_key'])

    def skip_hostname(self, hostname: str) -> bool:
        skips = self.options.get('ignore_hostnames')
        if not skips:
            return False
        return hostname.endswith(tuple(skips))

    def request(self, method: str, path: str, **kwargs):
        url = self.base_url + path
        headers = {'Authorization': f'Bearer {self.auth_key}'}
        timeout = self.options.get('timeout', self.TIMEOUT)
        return requests.request(method, url, timeout=timeout, headers=headers, **kwargs)

    def _perform_domain_request(self, method, identifier=None, **kwargs):
        if identifier is None:
            path = 'custom_hostnames'
        else:
            path = f'custom_hostnames/{identifier}'
        resp = self.request(method, path, **kwargs)
        return resp.json()

    def add_domain(self, domain: Domain) -> Domain:
        if self.skip_hostname(domain.hostname):
            return domain

        ssl_settings = self.options.get('ssl_settings', self.DEFAULT_SSL_SETTINGS)
        if domain.instrument_id:
            payload = {'ssl': ssl_settings}
            resp = self._perform_domain_request(
                'PATCH',
                identifier=domain.instrument_id,
                json=payload,
            )
            update_domain(domain, resp)
        else:
            payload = {
                'hostname': domain.hostname,
                'ssl': ssl_settings,
            }
            resp = self._perform_domain_request('POST', json=payload)
            update_domain(domain, resp)
        return domain

    def verify_domain(self, domain: Domain) -> Domain:
        if self.skip_hostname(domain.hostname):
            return domain

        if domain.instrument_id:
            resp = self._perform_domain_request(
                'GET',
                identifier=domain.instrument_id,
            )
            update_domain(domain, resp)
        return domain

    def remove_domain(self, domain: Domain) -> None:
        if domain.instrument_id and not self.skip_hostname(domain.hostname):
            self._perform_domain_request('DELETE', identifier=domain.instrument_id)


def normalize_instrument(resp) -> t.Tuple[str, InstrumentInfo]:
    errors = []
    if 'errors' in resp:
        for item in resp['errors']:
            errors.append(item['message'])

    if 'verification_errors' in resp:
        errors.extend(resp['verification_errors'])

    messages = []
    if 'messages' in resp:
        for item in resp['messages']:
            messages.append(item['message'])

    result = resp.get('result')
    instrument: InstrumentInfo = {}
    status = result.get('status')
    if status:
        instrument['ownership_status'] = status

    records: t.List[InstrumentRecord] = []
    ownership_verification = result.get('ownership_verification')
    if ownership_verification:
        records.append(ownership_verification)

    ssl_config = result.get('ssl')
    if ssl_config:
        instrument['ssl_status'] = ssl_config['status']
        validation_records = ssl_config.get('validation_records')
        if validation_records:
            for item in validation_records:
                name = item['txt_name']
                value = item['txt_value']
                records.append({'name': name, 'value': value, 'type': 'txt'})

        validation_errors = ssl_config.get('validation_errors')
        if validation_errors:
            for item in validation_errors:
                errors.append(item['message'])

    instrument['errors'] = errors
    instrument['records'] = records
    return result.get('id'), instrument


def update_domain(obj: Domain, resp):
    instrument_id, instrument = normalize_instrument(resp)
    if instrument.get('ownership_status') == 'active':
        obj.verified = True

    if instrument.get('ssl_status') == 'active':
        obj.ssl = True

    obj.instrument_id = instrument_id
    obj.instrument = instrument
    obj.active = obj.verified and obj.ssl
    obj.save()
