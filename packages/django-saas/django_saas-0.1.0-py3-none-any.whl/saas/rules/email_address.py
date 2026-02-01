import pathlib
from functools import cache

from rest_framework.request import Request

from .base import Rule


@cache
def load_default_blocked_domains():
    with pathlib.Path(__file__).parent.joinpath('blocklist.txt').open() as f:
        return f.read().splitlines()


class BlockedEmailDomains(Rule):
    """This rule prevents using email addresses from blocked domains.
    For example, `username@boofx.com` is not allowed.
    """

    error_message = 'Email address domain is blocked.'

    def bad_request(self, request: Request):
        blocked_list = self.options.get('domains')
        if not blocked_list:
            blocked_list = load_default_blocked_domains()

        email = self.get_response_field_value(request)
        return blocked_list and email.endswith(tuple([f'@{s}' for s in blocked_list]))


class AvoidTooManyDots(Rule):
    """This rule prevents using too many dots in email address.
    For example, `a.b.c.d.e@gmail.com` is not allowed.
    """

    error_message = 'Invalid email address.'
    MAX_DOT_COUNT = 4

    def bad_request(self, request: Request):
        max_dot_count = self.options.get('count', self.MAX_DOT_COUNT)
        email = self.get_response_field_value(request)
        name = email.split('@')[0]
        return name.count('.') > max_dot_count


class AvoidUsingPlus(Rule):
    """This rule prevents using of `+` in email address.
    For example, `username+random@gmail.com` is not allowed.
    """

    error_message = 'Email address cannot contain `+`.'

    def bad_request(self, request: Request):
        email = self.get_response_field_value(request)
        return '+' in email
