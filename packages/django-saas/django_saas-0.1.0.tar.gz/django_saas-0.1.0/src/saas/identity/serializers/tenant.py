import random
import string

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from saas.identity.models import Membership
from saas.models import get_tenant_model
from saas.signals import (
    before_create_tenant,
    before_update_tenant,
)

from .email_code import EmailCode


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_tenant_model()
        exclude = ['owner']
        read_only_fields = ['id', 'expires_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        before_create_tenant.send(self.__class__, data=validated_data, **self.context)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        before_update_tenant.send(self.__class__, tenant=instance, data=validated_data, **self.context)
        return super().update(instance, validated_data)


class TenantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_tenant_model()
        exclude = ['owner']
        read_only_fields = [
            'id',
            'slug',
            'environment',
            'region',
            'expires_at',
            'created_at',
            'updated_at',
        ]

    def update(self, instance, validated_data):
        before_update_tenant.send(self.__class__, tenant=instance, data=validated_data, **self.context)
        return super().update(instance, validated_data)


class TenantTransferSerializer(serializers.Serializer):
    CACHE_PREFIX = 'saas:transfer_tenant_code'
    action = serializers.ChoiceField(choices=['request', 'confirm'], required=True)
    username = serializers.CharField(required=True)
    code = serializers.CharField(required=False, allow_blank=True)

    def _get_code_cache_key(self, username: str, code: str):
        tenant_id = self.context['request'].tenant_id
        return f'{self.CACHE_PREFIX}:{tenant_id}:{username}:{code}'

    def validate_username(self, value: str):
        try:
            user = get_user_model().objects.get(username=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError('This user does not exist.')
        return user

    def validate(self, data):
        if data['action'] == 'request':
            return data
        code = data.get('code')
        if not code:
            raise serializers.ValidationError('Please enter the code.')

        user = data['username']
        cache_key = self._get_code_cache_key(user.username, code)
        if not cache.get(cache_key):
            raise serializers.ValidationError('Invalid code.')
        return data

    def create(self, validated_data):
        request = self.context['request']
        user = validated_data['username']

        if validated_data['action'] == 'request':
            code = ''.join(random.sample(string.ascii_uppercase, 6))
            cache_key = self._get_code_cache_key(user.username, code)
            cache.set(cache_key, 1, timeout=300)
            # send email to current user
            return EmailCode(request.user.email, code, request.user)

        tenant_id = request.tenant_id
        tenant = get_tenant_model().objects.get(id=tenant_id)
        with transaction.atomic():
            tenant.owner_id = user.pk
            tenant.save(update_fields=['owner_id'])
            Membership.objects.update_or_create(
                tenant=tenant,
                user=user,
                defaults={'role': 'OWNER'},
            )
        return tenant


class TenantDestroySerializer(serializers.Serializer):
    CACHE_PREFIX = 'saas:destroy_tenant_code'
    action = serializers.ChoiceField(choices=['request', 'confirm'], required=True)
    code = serializers.CharField(required=False, allow_blank=True)

    def _get_code_cache_key(self, code: str):
        tenant_id = self.context['request'].tenant_id
        return f'{self.CACHE_PREFIX}:{tenant_id}:{code}'

    def validate(self, data):
        if data['action'] == 'request':
            return data

        code = data.get('code')
        if not code:
            raise serializers.ValidationError('Please enter the code.')

        cache_key = self._get_code_cache_key(code)
        if not cache.get(cache_key):
            raise serializers.ValidationError('Invalid code.')
        return data

    def create(self, validated_data):
        request = self.context['request']
        if validated_data['action'] == 'request':
            code = ''.join(random.sample(string.ascii_uppercase, 6))
            cache_key = self._get_code_cache_key(code)
            cache.set(cache_key, 1, timeout=300)
            return EmailCode(request.user.email, code, request.user)

        tenant = get_tenant_model().objects.get(id=request.tenant_id)
        return tenant
