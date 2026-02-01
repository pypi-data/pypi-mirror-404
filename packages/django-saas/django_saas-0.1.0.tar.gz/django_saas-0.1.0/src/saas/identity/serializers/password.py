from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as APIValidationError

from ..models import Invitation, UserEmail
from .email_code import (
    EmailCodeConfirmSerializer,
    EmailCodeRequestSerializer,
    RetrieveUserEmailMixin,
)

PASSWORD_CODE = 'saas:password_code'


class PasswordLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    invite_code = serializers.CharField(required=False, allow_blank=True)

    @staticmethod
    def invalid_errors():
        errors = {'password': [_('Invalid username or password.')]}
        return APIValidationError(errors)

    @staticmethod
    def accept_invite(user, token: str):
        try:
            invitation = Invitation.objects.get(token=token)
        except (Invitation.DoesNotExist, ValidationError):
            return

        if invitation.status == Invitation.InviteStatus.PENDING and not invitation.is_expired():
            if UserEmail.belongs_to_user(user, invitation.email):
                with transaction.atomic():
                    invitation.accept_invite(user)

    def create(self, validated_data):
        request = self.context['request']
        invite_code = validated_data.pop('invite_code', None)
        user = authenticate(request=request, **validated_data)
        if not user:
            raise self.invalid_errors()

        # login and accept invite
        if invite_code:
            self.accept_invite(user, invite_code)
        return user

    def update(self, instance, validated_data):
        raise RuntimeError('This method is not allowed.')


class PasswordForgetSerializer(RetrieveUserEmailMixin, EmailCodeRequestSerializer):
    CACHE_PREFIX = PASSWORD_CODE

    def create(self, validated_data) -> UserEmail:
        user_email = validated_data['email']
        return user_email


class PasswordResetSerializer(RetrieveUserEmailMixin, EmailCodeConfirmSerializer):
    CACHE_PREFIX = PASSWORD_CODE
    password = serializers.CharField(required=True)

    def validate_password(self, raw_password):
        password_validation.validate_password(raw_password)
        return raw_password

    def create(self, validated_data):
        obj: UserEmail = validated_data['email']
        user_id = validated_data['code']

        if not user_id or obj.user_id != user_id:
            raise APIValidationError({'code': [_('Code does not match or expired.')]})

        raw_password = validated_data['password']
        user: AbstractUser = obj.user
        user.set_password(raw_password)
        user.save()
        return obj
