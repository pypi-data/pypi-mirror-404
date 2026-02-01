import typing as t
from abc import ABCMeta, abstractmethod


class BaseBackend(metaclass=ABCMeta):
    name: str = 'base'

    def __init__(self, **options):
        self.options = options

    @abstractmethod
    def resolve_ip(self, request) -> str: ...

    @abstractmethod
    def resolve_location(self, request) -> t.Dict[str, str]: ...

    def resolve(self, request):
        record_ip = self.options.get('record_ip')
        data = self.resolve_location(request)
        if record_ip:
            data['ip'] = self.resolve_ip(request)
        return data
