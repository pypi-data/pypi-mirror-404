from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from saas.drf.serializers import FlattenModelSerializer
from saas.identity.settings import identity_settings

from ..gravatar import gen_gravatar_url
from ..models import UserProfile

UserModel = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ('user',)


class UserSerializer(FlattenModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)
    profile = UserProfileSerializer()

    class Meta:
        model = UserModel
        exclude = ['password', 'groups', 'user_permissions']
        flatten_fields = ['profile']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # use gravatar if enabled
        if not data.get('avatar_url') and identity_settings.ENABLE_GRAVATAR:
            name = instance.get_full_name() or instance.username
            avatar_url = gen_gravatar_url(instance.email, name, **identity_settings.GRAVATAR_PARAMS)
            data['avatar_url'] = avatar_url
        return data


class SimpleUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)
    username = serializers.CharField(source='get_username', read_only=True)

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'name', 'is_active', 'is_staff']


class UserPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.instance
        if not user.check_password(value):
            raise ValidationError(_('Password incorrect.'))
        return value

    def validate_password(self, raw_password: str):
        if self.initial_data['confirm_password'] != raw_password:
            raise ValidationError(_('Password does not match.'))
        password_validation.validate_password(raw_password)
        return raw_password

    def update(self, user, validated_data):
        raw_password = validated_data['password']
        user.set_password(raw_password)
        user.save()
        return user
