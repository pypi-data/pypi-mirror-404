from django.conf import settings
from django.contrib.auth import login, logout
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from saas.drf.views import Endpoint
from saas.identity.settings import identity_settings
from saas.identity.signals import after_login_user, after_signup_user
from saas.rules import check_rules
from saas.signals import mail_queued

from ..models import Invitation
from ..serializers.auth import (
    EmailCode,
    SignupConfirmCodeSerializer,
    SignupConfirmPasswordSerializer,
    SignupCreateUserSerializer,
    SignupRequestCodeSerializer,
    SignupWithInvitationSerializer,
)
from ..serializers.invitation import InvitationInfoSerializer
from ..serializers.password import PasswordLoginSerializer

__all__ = [
    'SignupRequestEndpoint',
    'SignupConfirmEndpoint',
    'SignupWithInvitationEndpoint',
    'PasswordLogInEndpoint',
    'LogoutEndpoint',
    'InvitationEndpoint',
]


class SignupRequestEndpoint(Endpoint):
    email_template_id = 'signup_code'
    email_subject = _('Signup Request')
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def get_serializer_class(self):
        if identity_settings.SIGNUP_REQUEST_CREATE_USER:
            return SignupCreateUserSerializer
        return SignupRequestCodeSerializer

    def post(self, request: Request):
        """Send a sign-up code to user's email address."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # check bad request rules
        check_rules(identity_settings.SIGNUP_SECURITY_RULES, request)

        obj: EmailCode = serializer.save()
        mail_queued.send(
            sender=self.__class__,
            template_id=self.email_template_id,
            subject=str(self.email_subject),
            recipients=[obj.recipient()],
            context={'code': obj.code},
            request=request,
        )
        return Response(status=204)


class _BaseSignupConfirmEndpoint(Endpoint):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request: Request, *args, **kwargs):
        """Register a new user and login."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # auto login after signup
        login(request._request, user, backend='saas.identity.backends.ModelBackend')
        after_signup_user.send(
            self.__class__,
            user=user,
            request=request,
            strategy='password',
        )
        return Response({'next': settings.LOGIN_REDIRECT_URL})


class SignupConfirmEndpoint(_BaseSignupConfirmEndpoint):
    def get_serializer_class(self):
        if identity_settings.SIGNUP_REQUEST_CREATE_USER:
            return SignupConfirmCodeSerializer
        return SignupConfirmPasswordSerializer


class SignupWithInvitationEndpoint(_BaseSignupConfirmEndpoint):
    serializer_class = SignupWithInvitationSerializer
    queryset = Invitation.objects.all()
    lookup_field = 'token'

    def get_serializer_context(self):
        obj: Invitation = self.get_object()
        # only allow signup with "SENT" status
        if obj.status == Invitation.InviteStatus.SENT:
            context = super().get_serializer_context()
            context['invitation'] = obj
            return context
        raise NotFound()


class PasswordLogInEndpoint(Endpoint):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]
    serializer_class = PasswordLoginSerializer

    def post(self, request: Request):
        """Login a user with the given username and password."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        check_rules(identity_settings.LOGIN_SECURITY_RULES, request)

        user = serializer.save()
        login(request._request, user, backend='saas.identity.backends.ModelBackend')

        after_login_user.send(
            self.__class__,
            user=user,
            request=request,
            strategy='password',
        )
        return Response({'next': settings.LOGIN_REDIRECT_URL})


class LogoutEndpoint(Endpoint):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request):
        """Clear the user session and log the user out."""
        logout(request._request)
        return Response({'next': settings.LOGIN_URL})


class InvitationEndpoint(Endpoint):
    authentication_classes = []
    permission_classes = []
    serializer_class = InvitationInfoSerializer
    queryset = Invitation.objects.all()
    throttle_classes = [AnonRateThrottle]
    lookup_field = 'token'

    def get(self, request: Request, *args, **kwargs):
        """Retrieve a pending membership invitation."""
        obj: Invitation = self.get_object()
        if obj.status == Invitation.InviteStatus.ACCEPTED:
            raise NotFound()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
