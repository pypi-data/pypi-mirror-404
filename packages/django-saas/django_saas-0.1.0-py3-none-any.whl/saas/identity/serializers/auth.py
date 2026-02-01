import typing as t

from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ..models import Invitation, Membership, UserEmail
from .email_code import (
    EmailCode,
    EmailCodeConfirmSerializer,
    EmailCodeRequestSerializer,
    NewUserEmailMixin,
    RetrieveUserEmailMixin,
)

SIGNUP_CODE = 'saas:signup_code'

AUTH_ERRORS = {
    'exist_username': _('This username is already associated with an existing account.'),
}


class SignupRequestCodeSerializer(NewUserEmailMixin, EmailCodeRequestSerializer):
    CACHE_PREFIX = SIGNUP_CODE

    def create(self, validated_data) -> EmailCode:
        code = self.save_auth_code(1)
        email = validated_data['email']
        return EmailCode(email, code)


class SignupCreateUserSerializer(NewUserEmailMixin, EmailCodeRequestSerializer):
    CACHE_PREFIX = SIGNUP_CODE
    username = serializers.CharField(required=True, validators=[UnicodeUsernameValidator()])
    password = serializers.CharField(required=True)

    def validate_username(self, username: str):
        cls: t.Type[User] = get_user_model()
        try:
            cls.objects.get(username=username)
            raise ValidationError(AUTH_ERRORS['exist_username'])
        except cls.DoesNotExist:
            return username

    def validate_password(self, raw_password: str):
        user = User(
            username=self.initial_data['username'],
            email=self.initial_data['email'],
        )
        password_validation.validate_password(raw_password, user)
        return raw_password

    def create(self, validated_data) -> EmailCode:
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        cls: t.Type[User] = get_user_model()
        with transaction.atomic():
            user = cls.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False,
            )
            UserEmail.objects.create(user=user, email=email, primary=True, verified=False)

        code = self.save_auth_code(1)
        return EmailCode(email, code, user)


class SignupConfirmCodeSerializer(RetrieveUserEmailMixin, EmailCodeConfirmSerializer):
    CACHE_PREFIX = SIGNUP_CODE

    def create(self, validated_data) -> User:
        user_email = validated_data['email']
        with transaction.atomic():
            user_email.verified = True
            user = user_email.user
            user.is_active = True
            user_email.save()
            user.save()
        return user


class SignupConfirmPasswordSerializer(EmailCodeConfirmSerializer):
    CACHE_PREFIX = SIGNUP_CODE
    username = serializers.CharField(required=True, validators=[UnicodeUsernameValidator()])
    password = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6)

    def validate_username(self, username: str):
        cls: t.Type[User] = get_user_model()
        try:
            cls.objects.get(username=username)
            raise ValidationError(AUTH_ERRORS['exist_username'])
        except ObjectDoesNotExist:
            return username

    def validate_password(self, raw_password: str):
        user = User(
            username=self.initial_data['username'],
            email=self.initial_data['email'],
        )
        password_validation.validate_password(raw_password, user)
        return raw_password

    def create(self, validated_data) -> User:
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        cls: t.Type[User] = get_user_model()
        with transaction.atomic():
            user = cls.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=True,
            )
            UserEmail.objects.create(
                user=user,
                email=email,
                primary=True,
                verified=True,
            )
        return user


class SignupWithInvitationSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, validators=[UnicodeUsernameValidator()])
    password = serializers.CharField(required=True)

    def validate_username(self, username: str):
        cls: t.Type[User] = get_user_model()
        try:
            cls.objects.get(username=username)
            raise ValidationError(AUTH_ERRORS['exist_username'])
        except ObjectDoesNotExist:
            return username

    def validate_password(self, raw_password: str):
        invitation = self.context['invitation']
        user = User(
            username=self.initial_data['username'],
            email=invitation.email,
        )
        password_validation.validate_password(raw_password, user)
        return raw_password

    def create(self, validated_data) -> User:
        username = validated_data['username']
        password = validated_data['password']
        invitation = self.context['invitation']

        cls: t.Type[User] = get_user_model()
        with transaction.atomic():
            user = cls.objects.create_user(
                username=username,
                email=invitation.email,
                password=password,
                is_active=True,
            )
            UserEmail.objects.create(
                user=user,
                email=invitation.email,
                primary=True,
                verified=True,
            )
            Membership.objects.create(
                tenant_id=invitation.tenant_id,
                user=user,
                role=invitation.role,
            )
            invitation.status = Invitation.InviteStatus.ACCEPTED
            invitation.save()
        return user
