import functools


def resource_permission(name):
    """A decorator that adding required resource permissions to the view function.

    .. code-block:: python

        class TestView(TenantEndpoint):
            @resource_permissions('org.settings.update')
            def post(self, request, *args, **kwargs):
                ...
    """

    def decorated(func):
        func._required_permission = name

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapped

    return decorated
