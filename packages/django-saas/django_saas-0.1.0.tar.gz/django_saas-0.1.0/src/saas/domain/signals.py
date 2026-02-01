from django.dispatch import Signal

before_add_domain = Signal()
after_add_domain = Signal()
before_remove_domain = Signal()

__all__ = [
    'before_add_domain',
    'after_add_domain',
    'before_remove_domain',
]
