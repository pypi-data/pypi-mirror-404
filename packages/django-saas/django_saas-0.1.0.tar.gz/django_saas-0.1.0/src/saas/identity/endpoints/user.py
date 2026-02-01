from rest_framework.request import Request
from rest_framework.response import Response

from saas.drf.decorators import resource_permission
from saas.drf.views import AuthenticatedEndpoint

from ..serializers.user import (
    UserPasswordSerializer,
    UserSerializer,
)

__all__ = [
    'UserEndpoint',
    'UserPasswordEndpoint',
]


class UserEndpoint(AuthenticatedEndpoint):
    serializer_class = UserSerializer

    @resource_permission('user.profile.view')
    def get(self, request: Request):
        """Retrieve current user information."""
        serializer: UserSerializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @resource_permission('user.profile.update')
    def patch(self, request, *args, **kwargs):
        """Update current user information."""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserPasswordEndpoint(AuthenticatedEndpoint):
    serializer_class = UserPasswordSerializer

    # this is an non-exist permission, so that API token can not
    # access this endpoint
    required_permission = 'user.password.update'

    def post(self, request: Request, *args, **kwargs):
        """Update current user's password"""
        serializer: UserPasswordSerializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=204)
