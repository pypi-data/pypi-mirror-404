from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Domain
from .settings import domain_settings
from .signals import after_add_domain, before_add_domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        exclude = ['tenant', 'instrument_id']
        read_only_fields = ['primary']

    def validate_provider(self, value: str):
        if value in domain_settings.get_supported_providers():
            return value
        raise ValidationError(f"Provider '{value}' is not supported")

    def validate_hostname(self, value: str):
        if domain_settings.BLOCKED_DOMAINS and value.endswith(tuple(domain_settings.BLOCKED_DOMAINS)):
            raise ValidationError('This hostname is not allowed')
        return value.lower()

    def create(self, validated_data):
        before_add_domain.send(self.__class__, data=validated_data, **self.context)
        # auto set primary domain
        if 'primary' not in validated_data and domain_settings.TENANT_MAX_DOMAINS == 1:
            validated_data['primary'] = True
        instance = super().create(validated_data)
        after_add_domain.send(self.__class__, instance=instance, **self.context)
        return instance


class DomainSetPrimarySerializer(serializers.Serializer):
    primary = serializers.BooleanField(required=True)

    class Meta:
        model = Domain
        fields = ['primary']

    def update(self, instance: Domain, validated_data):
        primary = validated_data['primary']
        if primary:
            with transaction.atomic():
                Domain.objects.filter(tenant_id=instance.tenant_id, primary=True).update(primary=False)
                instance.primary = True
                instance.save()
        else:
            instance.primary = False
            instance.save()
        return instance
