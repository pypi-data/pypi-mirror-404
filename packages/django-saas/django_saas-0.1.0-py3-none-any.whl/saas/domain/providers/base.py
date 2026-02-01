from abc import ABCMeta, abstractmethod

from ..models import Domain


class BaseProvider(object, metaclass=ABCMeta):
    def __init__(self, **options):
        self.options = options

    @abstractmethod
    def add_domain(self, domain: Domain) -> Domain: ...

    @abstractmethod
    def verify_domain(self, domain: Domain) -> Domain: ...

    @abstractmethod
    def remove_domain(self, domain: Domain): ...
