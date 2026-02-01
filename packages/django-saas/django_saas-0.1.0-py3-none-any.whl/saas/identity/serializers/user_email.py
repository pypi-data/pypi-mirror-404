from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from ..models import UserEmail
from .email_code import (
    EmailCode,
    EmailCodeConfirmSerializer,
    EmailCodeRequestSerializer,
    NewUserEmailMixin,
)

NEW_EMAIL_CODE = 'saas:new_email_code'


class UserEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEmail
        exclude = ['user']
        read_only_fields = ['id', 'email', 'verified', 'created_at']

    def update(self, instance, validated_data):
        if validated_data.get('primary') and not instance.primary:
            # keep only one primary user email
            UserEmail.objects.filter(user_id=instance.user_id, primary=True).update(primary=False)
            with transaction.atomic():
                super().update(instance, validated_data)
                # update user's email to primary email address
                get_user_model().objects.filter(pk=instance.user_id).update(email=instance.email)
            return instance
        return instance


class AddEmailRequestSerializer(NewUserEmailMixin, EmailCodeRequestSerializer):
    CACHE_PREFIX = NEW_EMAIL_CODE

    def create(self, validated_data) -> EmailCode:
        request = self.context['request']
        code = self.save_auth_code(request.user.pk)
        email = validated_data['email']
        return EmailCode(email, code, request.user)


class AddEmailConfirmSerializer(NewUserEmailMixin, EmailCodeConfirmSerializer):
    CACHE_PREFIX = NEW_EMAIL_CODE

    def validate_code(self, value):
        user_id = super().validate_code(value)
        request = self.context['request']
        if not user_id or request.user.pk != user_id:
            self.fail_code()
        return request.user

    def create(self, validated_data):
        user = validated_data['code']
        return UserEmail.objects.create(
            email=validated_data['email'],
            user=user,
            verified=True,
        )
