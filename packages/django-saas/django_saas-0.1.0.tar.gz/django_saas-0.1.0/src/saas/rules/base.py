import logging
from abc import ABCMeta, abstractmethod

from rest_framework.request import Request

from saas.drf.errors import BadRequest

logger = logging.getLogger(__name__)


class Rule(metaclass=ABCMeta):
    DEFAULT_RESPONSE_FIELD: str = 'email'
    error_message: str = 'Bad request'

    def __init__(self, **options):
        self.options = options

    def get_response_field_value(self, request: Request):
        response_field = self.options.get(
            'response_field',
            self.DEFAULT_RESPONSE_FIELD,
        )
        return request.data.get(response_field)

    @abstractmethod
    def bad_request(self, request: Request):
        pass


def check_rules(rules: list[Rule], request: Request):
    for rule in rules:
        if rule.bad_request(request):
            rule_name = rule.__class__.__name__
            logger.warning(f'Bad request: [{rule_name}].')
            raise BadRequest(detail=rule.error_message, code=rule_name)
