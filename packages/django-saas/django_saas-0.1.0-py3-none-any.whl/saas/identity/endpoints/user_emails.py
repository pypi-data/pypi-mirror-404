from django.utils.translation import gettext_lazy as _
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from saas.drf.decorators import resource_permission
from saas.drf.filters import CurrentUserFilter
from saas.drf.views import AuthenticatedEndpoint
from saas.signals import mail_queued

from ..models import UserEmail
from ..serializers.user_email import (
    AddEmailConfirmSerializer,
    AddEmailRequestSerializer,
    UserEmailSerializer,
)

__all__ = [
    'UserEmailListEndpoint',
    'UserEmailItemEndpoint',
    'AddUserEmailRequestEndpoint',
    'AddUserEmailConfirmEndpoint',
]


class UserEmailListEndpoint(ListModelMixin, AuthenticatedEndpoint):
    pagination_class = None
    serializer_class = UserEmailSerializer
    queryset = UserEmail.objects.all()
    filter_backends = [CurrentUserFilter]

    @resource_permission('user.email.view')
    def get(self, request: Request, *args, **kwargs):
        """List all the current user's emails."""
        return self.list(request, *args, **kwargs)


class UserEmailItemEndpoint(RetrieveModelMixin, DestroyModelMixin, AuthenticatedEndpoint):
    resource_scopes = ['user:email']
    pagination_class = None
    serializer_class = UserEmailSerializer
    queryset = UserEmail.objects.all()
    filter_backends = [CurrentUserFilter]

    @resource_permission('user.email.view')
    def get(self, request: Request, *args, **kwargs):
        """Retrieve the current user's emails with the given uuid.'"""
        return self.retrieve(request, *args, **kwargs)

    @resource_permission('user.email.manage')
    def patch(self, request: Request, *args, **kwargs):
        """Set this email to be the primary email address."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @resource_permission('user.email.manage')
    def delete(self, request: Request, *args, **kwargs):
        """List all the current user's emails."""
        # TODO: preserving the primary email
        return self.destroy(request, *args, **kwargs)


class AddUserEmailRequestEndpoint(AuthenticatedEndpoint):
    resource_scopes = ['user:email']
    email_template_id = 'add_email'
    email_subject = _('Add new email')

    throttle_classes = [UserRateThrottle]
    serializer_class = AddEmailRequestSerializer

    @resource_permission('user.email.manage')
    def post(self, request: Request):
        """Send a request of authorization code for linking the account."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        mail_queued.send(
            sender=self.__class__,
            template_id=self.email_template_id,
            subject=self.email_subject,
            recipients=[obj.recipient()],
            context={'code': obj.code, 'user': obj.user},
            request=request,
        )
        return Response(status=204)


class AddUserEmailConfirmEndpoint(AuthenticatedEndpoint):
    resource_scopes = ['user:email']
    throttle_classes = [UserRateThrottle]
    serializer_class = AddEmailConfirmSerializer

    @resource_permission('user.email.manage')
    def post(self, request: Request):
        """Reset password of a user with the given code."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        data = UserEmailSerializer(obj).data
        return Response(data)
