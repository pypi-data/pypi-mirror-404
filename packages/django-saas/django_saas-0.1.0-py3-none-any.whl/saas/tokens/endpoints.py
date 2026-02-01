from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, ListModelMixin

from saas.drf.decorators import resource_permission
from saas.drf.views import AuthenticatedEndpoint

from .drf_permissions import NotUseToken
from .models import UserToken
from .serializers import UserTokenSerializer


class UserTokenListEndpoint(ListModelMixin, CreateModelMixin, AuthenticatedEndpoint):
    queryset = UserToken.objects.all()
    serializer_class = UserTokenSerializer
    # We combine NotUseToken with resource permissions.
    # NotUseToken ensures we don't use a token to access this.
    permission_classes = [NotUseToken]

    def filter_queryset(self, queryset):
        return queryset.filter(user=self.request.user)

    @resource_permission('user.token.view')
    def get(self, request, *args, **kwargs):
        """List all active tokens for the current user."""
        return self.list(request, *args, **kwargs)

    @resource_permission('user.token.manage')
    def post(self, request, *args, **kwargs):
        """Create a new token for the current user."""
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserTokenItemEndpoint(DestroyModelMixin, AuthenticatedEndpoint):
    queryset = UserToken.objects.all()
    serializer_class = UserTokenSerializer
    permission_classes = [NotUseToken]

    def filter_queryset(self, queryset):
        return queryset.filter(user=self.request.user)

    @resource_permission('user.token.manage')
    def delete(self, request, *args, **kwargs):
        """Delete a specific token."""
        return self.destroy(request, *args, **kwargs)
