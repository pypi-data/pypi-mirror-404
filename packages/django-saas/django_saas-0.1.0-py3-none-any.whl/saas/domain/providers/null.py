import logging

from ..models import Domain
from .base import BaseProvider

logger = logging.getLogger(__name__)


class NullProvider(BaseProvider):
    def add_domain(self, domain: Domain) -> Domain:
        logger.info('Add domain:', domain)
        domain.instrument_id = 'null'
        domain.instrument = {
            'ownership_status': 'pending',
            'ssl_status': 'pending',
            'records': [
                {'name': '@', 'type': 'cname', 'value': 'testserver'},
            ],
        }
        domain.save()
        return domain

    def verify_domain(self, domain: Domain) -> Domain:
        logger.info('Verify domain:', domain)
        domain.active = True
        domain.ssl = True
        domain.verified = True
        domain.save()
        return domain

    def remove_domain(self, domain: Domain):
        logger.info('Remove domain:', domain)
